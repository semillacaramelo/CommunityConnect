"""
Module for fetching market data from Deriv API
Based on official Deriv API documentation
"""
import pandas as pd
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class DataFetcher:
    def __init__(self, connector):
        self.connector = connector

    async def fetch_historical_data(self, symbol, interval, count=1000):
        """
        Fetch historical candlestick data

        Args:
            symbol: Trading symbol (e.g., "frxEURUSD")
            interval: Candle interval in seconds
            count: Number of candles to fetch
        """
        try:
            # Validate symbol format
            if not symbol.startswith(('frx', 'R_')):
                logger.error(f"Invalid symbol format: {symbol}")
                return None

            # Request historical data
            request = {
                "ticks_history": symbol,
                "adjust_start_time": 1,
                "count": min(count, 5000),  # API limit is 5000
                "end": "latest",
                "granularity": interval,
                "style": "candles",
                "req_id": self.connector._get_request_id()
            }

            response = await self.connector.send_request(request)

            if "error" in response:
                logger.error(f"Error fetching historical data: {response['error']['message']}")
                return None

            # Validate response structure
            if "candles" not in response:
                logger.error("Invalid response: missing candles data")
                return None

            candles = response["candles"]

            # Create DataFrame
            df = pd.DataFrame([{
                'time': candle['epoch'],
                'open': float(candle['open']),
                'high': float(candle['high']),
                'low': float(candle['low']),
                'close': float(candle['close'])
            } for candle in candles])

            # Convert timestamp and set index
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            # Sort index to ensure chronological order
            df.sort_index(inplace=True)

            logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error in fetch_historical_data: {str(e)}")
            return None

    async def subscribe_to_ticks(self, symbol):
        """
        Subscribe to real-time price ticks

        Args:
            symbol: Trading symbol (e.g., "frxEURUSD")
        """
        try:
            response = await self.connector.subscribe_to_ticks(symbol)

            if "error" in response:
                logger.error(f"Error subscribing to ticks: {response['error']['message']}")
                return None

            logger.info(f"Successfully subscribed to ticks for {symbol}")
            return response

        except Exception as e:
            logger.error(f"Error subscribing to ticks: {str(e)}")
            return None

    async def get_available_symbols(self):
        """Get list of available trading symbols"""
        try:
            response = await self.connector.get_active_symbols()

            if "error" in response:
                logger.error(f"Error fetching symbols: {response['error']['message']}")
                return None

            symbols = []
            if "active_symbols" in response:
                symbols = [symbol['symbol'] for symbol in response['active_symbols']]
                logger.info(f"Found {len(symbols)} active trading symbols")

            return symbols

        except Exception as e:
            logger.error(f"Error fetching available symbols: {str(e)}")
            return None