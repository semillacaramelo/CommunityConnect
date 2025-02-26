"""
Deriv API connector module for establishing and managing API connections
Based on official Deriv API documentation
"""
import os
import json
import asyncio
import random
import time
import websockets
from deriv_bot.monitor.logger import setup_logger
from deriv_bot.utils.config import Config

logger = setup_logger(__name__)

class DerivConnector:
    def __init__(self, config=None):
        self.config = config or Config()
        self.api_token = self.config.get_api_token()
        self.app_id = os.getenv('APP_ID', '1089')  # Default app_id if not provided
        self.ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
        self.websocket = None
        self.active = False
        self.lock = asyncio.Lock()
        self.request_id = 0
        self.last_ping_time = None
        self.ping_interval = 30
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 15  # Aumentado para permitir más intentos
        self.reconnect_delay = 5
        self.max_reconnect_delay = 120  # Aumentado el tiempo máximo de espera
        self.consecutive_failures = 0
        self.last_message_time = None
        self.authorized = False  # Nuevo flag para rastrear si la autorización fue exitosa

        # Log the environment we're connecting to
        env_mode = "REAL" if not self.config.is_demo() else "DEMO"
        logger.info(f"DerivConnector initialized in {env_mode} mode")

    async def connect(self):
        """Establish WebSocket connection to Deriv API"""
        try:
            logger.debug(f"Connecting to {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=60,
                close_timeout=30,
                max_size=10 * 1024 * 1024,
                extra_headers={
                    'User-Agent': 'deriv-bot/1.0.0'
                }
            )

            # Authorize connection
            auth_response = await self._authorize()
            if not auth_response or "error" in auth_response:
                error_msg = auth_response.get("error", {}).get("message", "Unknown error") if auth_response else "No response"
                logger.error(f"Authorization failed: {error_msg}")
                return False

            self.active = True
            self.authorized = True  # Marcar autorización como exitosa
            self.reconnect_attempts = 0
            self.consecutive_failures = 0
            self.last_message_time = asyncio.get_event_loop().time()

            # Log environment clearly
            env_mode = "REAL" if not self.config.is_demo() else "DEMO"
            logger.info(f"Successfully connected to Deriv API in {env_mode} mode")

            # Start ping task
            asyncio.create_task(self._keep_alive())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Deriv API: {str(e)}")
            return False

    async def close(self):
        """Close WebSocket connection"""
        self.active = False
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.websocket = None
                self.authorized = False  # Resetear estado de autorización

    async def _authorize(self):
        """Authorize connection using API token"""
        self.api_token = self.config.get_api_token()
        
        auth_req = {
            "authorize": self.api_token,
            "req_id": self._get_request_id(),
            "passthrough": {"handle_errors": 1}
        }

        # Intentar autorización con reintentos
        for attempt in range(3):  # 3 intentos de autorización
            try:
                response = await self.send_request(auth_req)
                if response and "authorize" in response:
                    logger.info("API authorization successful")
                    return response
                elif response and "error" in response:
                    error_code = response["error"]["code"]
                    error_msg = response["error"]["message"]
                    logger.error(f"Authorization error {error_code}: {error_msg}")
                    # Si es un error de token inválido, no tiene sentido reintentar
                    if error_code in ["InvalidToken", "AuthorizationRequired"]:
                        return response
                else:
                    logger.warning(f"Unexpected authorization response: {response}")

                if attempt < 2:  # No esperar después del último intento
                    await asyncio.sleep(2)  # Pequeña pausa entre intentos
            except Exception as e:
                logger.error(f"Authorization attempt {attempt+1} failed: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(2)

        return None  # Todos los intentos fallaron

    def _get_request_id(self):
        """Generate unique request ID"""
        self.request_id += 1
        return self.request_id

    async def _keep_alive(self):
        """Keep the WebSocket connection alive with periodic pings"""
        while self.active:
            try:
                await asyncio.sleep(self.ping_interval)  # Wait between pings

                # If socket is already closed, attempt reconnect
                if not self.websocket or self.websocket.closed:
                    logger.warning("WebSocket closed before ping, attempting reconnect...")
                    await self.reconnect()
                    continue

                # Check if we've received any messages recently
                current_time = asyncio.get_event_loop().time()
                if self.last_message_time and current_time - self.last_message_time > 60:
                    logger.warning("No messages received in the last minute, reconnecting...")
                    await self.reconnect()
                    continue

                ping_req = {
                    "ping": 1,
                    "req_id": self._get_request_id()
                }

                try:
                    # Usar un timeout más largo para el ping
                    response = await asyncio.wait_for(
                        self.send_request(ping_req),
                        timeout=15  # Aumentado a 15 segundos
                    )

                    # Mejorado el manejo de respuestas ping
                    if response:
                        if "pong" in response:
                            self.last_ping_time = asyncio.get_event_loop().time()
                            self.consecutive_failures = 0
                            logger.debug("Ping successful")
                        else:
                            # Verificar si hay algún otro tipo de respuesta válida
                            if any(key in response for key in ["tick", "ohlc", "candles"]):
                                # Recibimos datos de trading en lugar de pong, esto es válido
                                self.last_ping_time = asyncio.get_event_loop().time()
                                self.consecutive_failures = 0
                                logger.debug("Received trading data instead of pong - connection still active")
                            else:
                                logger.warning(f"Unexpected ping response: {response}")
                                self.consecutive_failures += 1
                                if self.consecutive_failures >= 5:  # Aumentado de 3 a 5
                                    logger.warning("Multiple consecutive ping failures, reconnecting...")
                                    await self.reconnect()
                    else:
                        logger.warning("Empty ping response")
                        self.consecutive_failures += 1
                        if self.consecutive_failures >= 3:
                            logger.warning("Multiple empty responses, reconnecting...")
                            await self.reconnect()

                except asyncio.TimeoutError:
                    logger.warning("Ping timed out after 15 seconds")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= 2:
                        logger.warning("Multiple ping timeouts, reconnecting...")
                        await self.reconnect()

            except Exception as e:
                logger.warning(f"Ping process failed: {str(e)}")
                await self.reconnect()

    async def check_connection(self):
        """Check if WebSocket connection is active and responsive"""
        try:
            # Check basic connection state
            if not self.websocket or self.websocket.closed or not self.active:
                return False

            # Verify authorization
            if not self.authorized:
                return False

            # Check last successful ping time
            if self.last_ping_time:
                current_time = asyncio.get_event_loop().time()
                if current_time - self.last_ping_time > 90:
                    return False
                return True  # Si tenemos ping reciente, la conexión está activa
            
            # Si no hay último ping, hacer uno nuevo
            ping_req = {
                "ping": 1,
                "req_id": self._get_request_id()
            }
            
            response = await asyncio.wait_for(
                self.send_request(ping_req),
                timeout=5
            )
            
            if response and "pong" in response:
                self.last_ping_time = asyncio.get_event_loop().time()
                return True
                
            return False

            # Send test ping
            ping_req = {
                "ping": 1,
                "req_id": self._get_request_id()
            }

            try:
                response = await asyncio.wait_for(
                    self.send_request(ping_req),
                    timeout=10  # Aumentado de 5 a 10 segundos
                )

                # Mejorado el manejo de respuestas ping (similar a _keep_alive)
                if response:
                    if "pong" in response:
                        self.last_ping_time = asyncio.get_event_loop().time()
                        return True
                    elif any(key in response for key in ["tick", "ohlc", "candles"]):
                        # Recibimos datos de trading en lugar de pong, esto es válido
                        self.last_ping_time = asyncio.get_event_loop().time()
                        return True

                logger.warning("Connection check failed: Invalid ping response")
                return False

            except asyncio.TimeoutError:
                logger.warning("Connection check ping timed out")
                return False

        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False

    async def reconnect(self):
        """Attempt to reconnect if connection is lost"""
        if not self.active:
            logger.debug("Not reconnecting as connector is marked inactive")
            return False

        try:
            await self.close()

            # Backoff exponencial con jitter optimizado
            delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), self.max_reconnect_delay)
            jitter = random.uniform(0.5, 1.5)  # Increased jitter range
            wait_time = delay * jitter
            
            # Reset connection state
            self.websocket = None
            self.authorized = False
            self.consecutive_failures = 0

            logger.info(f"Waiting {wait_time:.2f}s before reconnect attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}")
            await asyncio.sleep(wait_time)

            success = await self.connect()
            if success:
                logger.info(f"Reconnection successful after {self.reconnect_attempts + 1} attempts")
                self.reconnect_attempts = 0
                return True
            else:
                self.reconnect_attempts += 1
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error(f"Maximum reconnection attempts ({self.max_reconnect_attempts}) reached")
                    self.active = False
                return False

        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            self.reconnect_attempts += 1
            return False

    async def send_request(self, request):
        """Send request to Deriv API with mutex lock"""
        if not self.websocket:
            raise ConnectionError("WebSocket connection not established")

        async with self.lock:  # Ensure only one request at a time
            try:
                # Añadimos un reintento básico para envío de mensajes
                for attempt in range(3):  # 3 intentos como máximo
                    try:
                        await self.websocket.send(json.dumps(request))
                        response = await self.websocket.recv()
                        parsed_response = json.loads(response)

                        # Update last message time
                        self.last_message_time = asyncio.get_event_loop().time()

                        # Check for API errors
                        if "error" in parsed_response:
                            error_code = parsed_response["error"]["code"]
                            error_message = parsed_response["error"]["message"]

                            # Check for authentication errors
                            if error_code in ["InvalidToken", "AuthorizationRequired"]:
                                logger.error(f"Authentication error: {error_message}")
                                self.authorized = False  # Marcar como no autorizado
                                # Force reconnect with fresh auth
                                await self.reconnect()
                            else:
                                logger.warning(f"API error {error_code}: {error_message}")

                        return parsed_response

                    except websockets.exceptions.ConnectionClosed:
                        if attempt < 2:  # No log en el último intento
                            logger.warning(f"Connection closed while sending request. Attempt {attempt+1}/3")
                            # Intentar reconectar antes de reintentar
                            if attempt == 0:  # Solo intentar reconectar en el primer fallo
                                await self.reconnect()
                            await asyncio.sleep(1)  # Breve pausa
                        else:
                            raise  # Re-raise en el último intento

            except Exception as e:
                logger.error(f"Error sending request: {str(e)}")
                raise

    async def subscribe_to_ticks(self, symbol):
        """Subscribe to price ticks for a symbol"""
        subscribe_req = {
            "ticks": symbol,
            "subscribe": 1,
            "req_id": self._get_request_id()
        }
        return await self.send_request(subscribe_req)

    async def get_active_symbols(self):
        """Get list of active trading symbols"""
        active_symbols_req = {
            "active_symbols": "brief",
            "product_type": "basic",
            "req_id": self._get_request_id()
        }
        return await self.send_request(active_symbols_req)

    async def get_server_time(self):
        """Get server time to check connectivity"""
        time_req = {
            "time": 1,
            "req_id": self._get_request_id()
        }
        return await self.send_request(time_req)