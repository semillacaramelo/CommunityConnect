"""
Deriv API Connector Module

Location: deriv_bot/data/deriv_connector.py

Purpose:
Handles WebSocket connections to Deriv.com API, manages authentication,
and provides low-level API communication functionality.

Dependencies:
- websockets: WebSocket client implementation
- deriv_bot.monitor.logger: Logging functionality
- deriv_bot.utils.config: Configuration management

Interactions:
- Input: API credentials, connection parameters
- Output: WebSocket connection, API responses
- Relations: Used by DataFetcher and OrderExecutor

Author: Trading Bot Team
Last modified: 2024-02-26
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
        self.max_reconnect_attempts = 15
        self.reconnect_delay = 5
        self.max_reconnect_delay = 120
        self.consecutive_failures = 0
        self.last_message_time = None
        self.authorized = False
        self.is_virtual = None
        self.balance = None
        self.currency = None
        self.heartbeat_task = None

        # Log the environment we're connecting to
        env_mode = "REAL" if not self.config.is_demo() else "DEMO"
        logger.info(f"DerivConnector initialized in {env_mode} mode")

    async def connect(self):
        """Establish WebSocket connection to Deriv API"""
        try:
            if self.websocket and not self.websocket.closed:
                logger.debug("Connection already exists")
                return True

            logger.debug(f"Connecting to {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=None,  # We'll handle our own ping
                ping_timeout=None,   # Disable built-in ping timeout
                close_timeout=15,
                max_size=10 * 1024 * 1024,
                extra_headers={
                    'User-Agent': 'deriv-bot/1.0.0'
                },
                max_queue=1024
            )

            # Set shorter timeouts for faster failure detection
            self.ping_interval = 30  # Increased from 15 to reduce frequency
            self.consecutive_failures = 0

            # Authorize connection
            auth_response = await self._authorize()
            if not auth_response or "error" in auth_response:
                error_msg = auth_response.get("error", {}).get("message", "Unknown error") if auth_response else "No response"
                logger.error(f"Authorization failed: {error_msg}")
                await self.close()
                return False

            self.active = True
            self.authorized = True
            self.reconnect_attempts = 0
            self.consecutive_failures = 0
            self.last_message_time = asyncio.get_event_loop().time()

            # Log environment clearly
            env_mode = "REAL" if not self.config.is_demo() else "DEMO"
            logger.info(f"Successfully connected to Deriv API in {env_mode} mode")

            # Start ping task
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            self.heartbeat_task = asyncio.create_task(self._keep_alive())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Deriv API: {str(e)}")
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
                self.websocket = None
            return False

    async def close(self):
        """Close WebSocket connection"""
        self.active = False
        if self.heartbeat_task:
            try:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None
            except Exception as e:
                logger.error(f"Error cancelling heartbeat task: {str(e)}")

        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.websocket = None
                self.authorized = False

    async def _authorize(self):
        """Enhanced API authorization with balance check and account type detection"""
        self.api_token = self.config.get_api_token()
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if not self.websocket or self.websocket.closed:
                    logger.error("Cannot authorize: WebSocket connection not established")
                    return None

                auth_req = {
                    "authorize": self.api_token,
                    "req_id": self._get_request_id()
                }

                response = await self.send_request(auth_req)
                if response and "authorize" in response:
                    self.authorized = True
                    account_info = response["authorize"]

                    # Detect account type and balance
                    self.is_virtual = account_info.get("is_virtual", False)
                    self.balance = float(account_info.get("balance", 0))
                    self.currency = account_info.get("currency", "USD")

                    env_type = "DEMO" if self.is_virtual else "REAL"
                    logger.info(f"API authorization successful - {env_type} account")
                    logger.info(f"Account balance: {self.balance} {self.currency}")

                    # Check minimum balance for virtual account
                    if self.is_virtual and self.balance < 1000:
                        logger.warning("Demo account balance low, initiating reset")
                        await self.reset_virtual_balance()

                    return response

                if "error" in response:
                    logger.error(f"Authorization error: {response['error'].get('message', 'Unknown error')}")

                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Authorization attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)

        return None

    async def reset_virtual_balance(self):
        """Reset virtual account balance"""
        if not self.is_virtual:
            logger.warning("Balance reset attempted on real account - denied")
            return False

        try:
            reset_req = {
                "reset_balance": 1,
                "req_id": self._get_request_id()
            }

            response = await self.send_request(reset_req)
            if response and "reset_balance" in response:
                new_balance = float(response["reset_balance"].get("balance", 0))
                logger.info(f"Demo account balance reset to {new_balance} {self.currency}")
                self.balance = new_balance
                return True

            logger.error("Failed to reset demo account balance")
            return False

        except Exception as e:
            logger.error(f"Error resetting demo balance: {str(e)}")
            return False

    def _get_request_id(self):
        """Generate unique request ID"""
        self.request_id += 1
        return self.request_id

    async def _keep_alive(self):
        """Keep the WebSocket connection alive with periodic pings"""
        while self.active:
            try:
                await asyncio.sleep(self.ping_interval)

                # Check connection state
                if not self.websocket or self.websocket.closed:
                    logger.warning("WebSocket closed, attempting immediate reconnect...")
                    if await self.reconnect():
                        continue
                    await asyncio.sleep(5)  # Wait longer between reconnect attempts
                    continue

                # Send ping to verify connection
                try:
                    ping_req = {
                        "ping": 1,
                        "req_id": self._get_request_id()
                    }

                    response = await asyncio.wait_for(
                        self.send_request(ping_req),
                        timeout=20  # Increased timeout
                    )

                    if response:
                        # Check for valid ping response (should contain 'ping': 'pong')
                        if "ping" in response and response.get("ping") == "pong":
                            # This is a valid ping response
                            self.last_ping_time = asyncio.get_event_loop().time()
                            self.last_message_time = self.last_ping_time
                            self.consecutive_failures = 0
                            logger.debug("Ping successful")
                            continue
                        elif any(key in response for key in ["tick", "ohlc", "candles"]):
                            # Also accept data response as valid connection indicator
                            self.last_ping_time = asyncio.get_event_loop().time()
                            self.last_message_time = self.last_ping_time
                            self.consecutive_failures = 0
                            continue
                        else:
                            # Log but don't treat as error as long as we got a response
                            logger.debug(f"Non-standard response received, but connection is active: {response}")
                            self.last_ping_time = asyncio.get_event_loop().time()
                            self.last_message_time = self.last_ping_time
                            # Don't increment failures for non-standard responses
                            continue
                    else:
                        logger.warning("Empty ping response")
                        self.consecutive_failures += 1

                    # Only trigger reconnect after 3 consecutive failures
                    if self.consecutive_failures >= 3:
                        logger.warning("Multiple ping failures, reconnecting...")
                        await self.reconnect()

                except asyncio.TimeoutError:
                    logger.warning(f"Ping timed out after {self.ping_interval} seconds")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= 2:
                        logger.warning("Multiple ping timeouts, reconnecting...")
                        await self.reconnect()
                except Exception as e:
                    logger.warning(f"Ping failed: {str(e)}")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= 2:
                        await self.reconnect()

                # Check if we've received any messages recently
                current_time = asyncio.get_event_loop().time()
                if self.last_message_time and current_time - self.last_message_time > 60:  # Increased from 30s to 60s
                    logger.warning("No messages received in the last 60 seconds, reconnecting...")
                    await self.reconnect()
                    continue

            except Exception as e:
                logger.warning(f"Ping process failed: {str(e)}")
                await asyncio.sleep(10)
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
                return True  # If we have recent ping, connection is active

            # If no last ping, send a new one
            ping_req = {
                "ping": 1,
                "req_id": self._get_request_id()
            }

            try:
                response = await asyncio.wait_for(
                    self.send_request(ping_req),
                    timeout=10  # Increased from 5s to 10s
                )

                # Updated check to match the proper ping response format
                if response and "ping" in response and response.get("ping") == "pong":
                    self.last_ping_time = asyncio.get_event_loop().time()
                    return True
                return False
            except (asyncio.TimeoutError, Exception):
                return False

        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False

    async def reconnect(self):
        """Attempt to reconnect if connection is lost using exponential backoff"""
        if not self.active:
            logger.debug("Not reconnecting as connector is marked inactive")
            return False

        try:
            await self.close()

            # Enhanced exponential backoff with optimized jitter
            base_delay = self.reconnect_delay
            max_delay = self.max_reconnect_delay
            attempt = self.reconnect_attempts

            # Calculate delay with full jitter backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            actual_delay = random.uniform(base_delay, delay)

            logger.info(f"Attempting reconnection {attempt + 1}/{self.max_reconnect_attempts} "
                       f"with {actual_delay:.2f}s delay")

            await asyncio.sleep(actual_delay)

            # Clear existing state
            self.websocket = None
            self.authorized = False
            self.consecutive_failures = 0
            self.last_message_time = None
            self.last_ping_time = None

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
            logger.error("WebSocket connection not established")
            return None

        async with self.lock:  # Ensure only one request at a time
            try:
                # Add basic retry for message sending
                for attempt in range(3):  # 3 attempts maximum
                    try:
                        if self.websocket.closed:
                            logger.warning(f"WebSocket closed before sending request (attempt {attempt+1})")
                            if attempt < 2:
                                if attempt == 0:  # Only try to reconnect on first failure
                                    await self.reconnect()
                                await asyncio.sleep(2)  # Increased from 1s to 2s
                                continue
                            else:
                                return None

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
                                self.authorized = False  # Mark as unauthorized
                                # Force reconnect with fresh auth
                                await self.reconnect()
                            else:
                                logger.warning(f"API error {error_code}: {error_message}")

                        return parsed_response

                    except websockets.exceptions.ConnectionClosed:
                        if attempt < 2:
                            logger.warning(f"Connection closed while sending request. Attempt {attempt+1}/3")
                            # Try to reconnect before retrying
                            if attempt == 0:  # Only try to reconnect on first failure
                                await self.reconnect()
                            await asyncio.sleep(2)  # Increased from 1s to 2s
                        else:
                            logger.error("Connection permanently closed after 3 attempts")
                            return None

                    except Exception as e:
                        logger.error(f"Error sending request (attempt {attempt+1}): {str(e)}")
                        if attempt < 2:
                            await asyncio.sleep(2)  # Increased from 1s to 2s
                        else:
                            return None

                return None  # All attempts failed

            except Exception as e:
                logger.error(f"Fatal error sending request: {str(e)}")
                return None

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