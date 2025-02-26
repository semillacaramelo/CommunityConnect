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
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        self.consecutive_failures = 0
        self.last_message_time = None

        # Log the environment we're connecting to
        env_mode = "REAL" if not self.config.is_demo() else "DEMO"
        logger.info(f"DerivConnector initialized in {env_mode} mode")

    async def connect(self):
        """Establish WebSocket connection to Deriv API"""
        try:
            logger.debug(f"Connecting to {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=None,  # We'll handle pings manually
                ping_timeout=None,   # Disable auto ping timeout
                close_timeout=10,    # Give more time for graceful close
                max_size=10 * 1024 * 1024  # 10MB max message size
            )

            # Authorize connection
            auth_response = await self._authorize()
            if not auth_response or "error" in auth_response:
                error_msg = auth_response.get("error", {}).get("message", "Unknown error") if auth_response else "No response"
                logger.error(f"Authorization failed: {error_msg}")
                return False

            self.active = True
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

    async def _authorize(self):
        """Authorize connection using API token"""
        # Get the current token (which might have changed if environment was switched)
        self.api_token = self.config.get_api_token()

        auth_req = {
            "authorize": self.api_token,
            "req_id": self._get_request_id()
        }
        return await self.send_request(auth_req)

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
                    response = await asyncio.wait_for(
                        self.send_request(ping_req),
                        timeout=10  # 10 second timeout for ping response
                    )

                    if response and "pong" in response:
                        self.last_ping_time = asyncio.get_event_loop().time()
                        self.consecutive_failures = 0
                        logger.debug("Ping successful")
                    else:
                        logger.warning("Invalid ping response")
                        self.consecutive_failures += 1
                        if self.consecutive_failures >= 3:
                            logger.warning("Multiple consecutive ping failures, reconnecting...")
                            await self.reconnect()
                except asyncio.TimeoutError:
                    logger.warning("Ping timed out after 10 seconds")
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
                logger.warning("Connection check failed: WebSocket not active")
                return False

            # Check last successful ping time
            if self.last_ping_time:
                current_time = asyncio.get_event_loop().time()
                if current_time - self.last_ping_time > 60:  # No successful ping in last minute
                    logger.warning("Connection check failed: No recent ping response")
                    return False

            # Send test ping
            ping_req = {
                "ping": 1,
                "req_id": self._get_request_id()
            }

            try:
                response = await asyncio.wait_for(
                    self.send_request(ping_req),
                    timeout=5  # 5 second timeout for check ping
                )

                if response and "pong" in response:
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

            # Calculate backoff time with jitter
            delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), self.max_reconnect_delay)
            jitter = random.uniform(0.8, 1.2)  # Add 20% jitter
            wait_time = delay * jitter

            logger.info(f"Waiting {wait_time:.2f}s before reconnect attempt {self.reconnect_attempts + 1}")
            await asyncio.sleep(wait_time)

            success = await self.connect()
            if success:
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
                        # Force reconnect with fresh auth
                        await self.reconnect()
                    else:
                        logger.warning(f"API error {error_code}: {error_message}")

                return parsed_response
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