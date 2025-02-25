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
        self.ping_interval = 30  # Ping every 30 seconds to keep connection alive

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

            # Start ping task to keep connection alive
            asyncio.create_task(self._keep_alive())

            self.active = True
            logger.info("Successfully connected to Deriv API")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Deriv API: {str(e)}")
            return False

    async def _authorize(self):
        """Authorize connection using API token"""
        auth_req = {
            "authorize": self.api_token
        }
        return await self.send_request(auth_req)

    async def _keep_alive(self):
        """Keep the WebSocket connection alive with periodic pings"""
        while self.active:
            try:
                if self.websocket and not self.websocket.closed:
                    ping_req = {"ping": 1}
                    await self.send_request(ping_req)
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.warning(f"Ping failed: {str(e)}")
                await self.reconnect()

    async def reconnect(self):
        """Attempt to reconnect if connection is lost"""
        try:
            await self.close()
            await asyncio.sleep(5)  # Wait before reconnecting
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")

    async def send_request(self, request):
        """Send request to Deriv API"""
        if not self.websocket:
            raise ConnectionError("WebSocket connection not established")

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
            await self.websocket.close()
            logger.info("Connection closed")

    async def subscribe_to_ticks(self, symbol):
        """
        Subscribe to price ticks for a symbol

        Args:
            symbol: Trading symbol (e.g., "frxEURUSD")
        """
        subscribe_req = {
            "ticks": symbol,
            "subscribe": 1
        }
        return await self.send_request(subscribe_req)

    async def get_active_symbols(self):
        """Get list of active trading symbols"""
        active_symbols_req = {
            "active_symbols": "brief",
            "product_type": "basic"
        }
        return await self.send_request(active_symbols_req)