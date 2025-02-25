"""
Test script for verifying Deriv API connectivity
Following official documentation from:
- https://deriv-com.github.io/python-deriv-api/
- https://api.deriv.com/api-explorer
"""
import os
import asyncio
import json
from datetime import datetime
from deriv_bot.data.deriv_connector import DerivConnector
from deriv_bot.data.data_fetcher import DataFetcher
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger('api_test')

async def test_api_connectivity():
    """Test basic API connectivity and data fetching"""
    try:
        # Check environment variables
        print("\nVerifying environment variables:")
        env_vars = ['DERIV_API_TOKEN_DEMO', 'DERIV_API_TOKEN_REAL', 'DERIV_BOT_ENV', 'APP_ID']
        for var in env_vars:
            value = os.getenv(var)
            print(f"✓ {var}: {'Configured' if value else 'Not configured'}")

        print("\nTesting API connection...")
        connector = DerivConnector()
        connected = await connector.connect()

        if not connected:
            print("❌ Failed to connect to Deriv API")
            return

        print("✓ Successfully connected to Deriv API")

        # Get available symbols
        print("\nFetching available symbols...")
        data_fetcher = DataFetcher(connector)
        symbols = await data_fetcher.get_available_symbols()
        
        if symbols:
            print(f"✓ Found {len(symbols)} trading symbols")
            print("Sample symbols:", symbols[:5])
        else:
            print("❌ Failed to fetch trading symbols")

        # Test historical data fetching
        print("\nTesting historical data fetch for EUR/USD...")
        historical_data = await data_fetcher.fetch_historical_data(
            symbol="frxEURUSD",
            interval=60,  # 1-minute candles
            count=10  # Just a few candles for testing
        )

        if historical_data is not None:
            print("✓ Successfully fetched historical data")
            print("\nSample data:")
            print(historical_data.head())
        else:
            print("❌ Failed to fetch historical data")

        # Test tick subscription
        print("\nTesting tick subscription...")
        tick_response = await data_fetcher.subscribe_to_ticks("frxEURUSD")
        
        if tick_response and "error" not in tick_response:
            print("✓ Successfully subscribed to ticks")
        else:
            print("❌ Failed to subscribe to ticks")

        # Clean up
        await connector.close()
        print("\n✓ Connection closed properly")

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
    
if __name__ == "__main__":
    print("Starting Deriv API connectivity test...")
    print("=====================================")
    asyncio.run(test_api_connectivity())
