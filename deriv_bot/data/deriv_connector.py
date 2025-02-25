"""
Deriv API connector module for establishing and managing API connections
Based on official Deriv API documentation
"""
import os
import json
import asyncio
import websockets
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class DerivConnector:
    def __init__(self):
        self.api_token = os.getenv('DERIV_API_TOKEN_DEMO')
        self.app_id = os.getenv('APP_ID', '1089')  # Default app_id if not provided
        self.ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
        self.websocket = None
        self.active = False
        self.lock = asyncio.Lock()
        self.request_id = 0
        self.last_ping_time = None

    async def connect(self):
        """Establish WebSocket connection to Deriv API"""
        try:
            self.websocket = await websockets.connect(self.ws_url)

            # Authorize connection
            auth_response = await self._authorize()
            if not auth_response or "error" in auth_response:
                error_msg = auth_response.get("error", {}).get("message", "Unknown error") if auth_response else "No response"
                logger.error(f"Authorization failed: {error_msg}")
                return False

            self.active = True
            logger.info("Successfully connected to Deriv API")

            # Start ping task
            asyncio.create_task(self._keep_alive())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Deriv API: {str(e)}")
            return False

    async def _authorize(self):
        """Authorize connection using API token"""
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
                await asyncio.sleep(30)  # Wait between pings
                if self.websocket and not self.websocket.closed:
                    ping_req = {
                        "ping": 1,
                        "req_id": self._get_request_id()
                    }
                    response = await self.send_request(ping_req)
                    if response and "pong" in response:
                        self.last_ping_time = asyncio.get_event_loop().time()
                        logger.debug("Ping successful")
                    else:
                        logger.warning("Invalid ping response")
                        await self.reconnect()
            except Exception as e:
                logger.warning(f"Ping failed: {str(e)}")
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
            response = await self.send_request(ping_req)

            if response and "pong" in response:
                self.last_ping_time = asyncio.get_event_loop().time()
                return True

            logger.warning("Connection check failed: Invalid ping response")
            return False

        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False

    async def reconnect(self):
        """Attempt to reconnect if connection is lost"""
        try:
            await self.close()
            await asyncio.sleep(5)  # Wait before reconnecting
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")

    async def send_request(self, request):
        """Send request to Deriv API with mutex lock"""
        if not self.websocket:
            raise ConnectionError("WebSocket connection not established")

        async with self.lock:  # Ensure only one request at a time
            try:
                await self.websocket.send(json.dumps(request))
                response = await self.websocket.recv()
                return json.loads(response)
            except Exception as e:
                logger.error(f"Error sending request: {str(e)}")
                raise

    async def close(self):
        """Close WebSocket connection"""
        self.active = False
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")

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