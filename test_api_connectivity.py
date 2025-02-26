"""
Test script for verifying Deriv API connectivity
Following official documentation from:
- https://deriv-com.github.io/python-deriv-api/
- https://api.deriv.com/api-explorer
"""
import os
import asyncio
import json
import time
import argparse
from datetime import datetime
from deriv_bot.data.deriv_connector import DerivConnector
from deriv_bot.data.data_fetcher import DataFetcher
from deriv_bot.utils.config import Config
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger('api_test')

async def test_api_connectivity(test_mode='demo', verbose=False, extended_test=False):
    """
    Test basic API connectivity and data fetching

    Args:
        test_mode: 'demo' or 'real' environment to test
        verbose: Show detailed output
        extended_test: Run more comprehensive tests
    """
    try:
        # Check environment variables
        print("\n===== API CONNECTIVITY TEST =====")
        print("\nVerifying environment variables:")
        env_vars = ['DERIV_API_TOKEN_DEMO', 'DERIV_API_TOKEN_REAL', 'DERIV_BOT_ENV', 'APP_ID']
        for var in env_vars:
            value = os.getenv(var)
            status = '✅ Configured' if value else '❌ Not configured'
            print(f"- {var}: {status}")

        # Configure the correct environment for testing
        config = Config()
        original_env = config.get_environment()  # Store current environment
        original_confirmed = os.getenv('DERIV_REAL_MODE_CONFIRMED')  # Store current config

        if test_mode == 'real':
            if os.getenv('DERIV_API_TOKEN_REAL'):
                # Temporarily set for testing
                os.environ['DERIV_REAL_MODE_CONFIRMED'] = 'yes'
                if not config.set_environment('real'):
                    print("\n❌ Could not set REAL environment for testing")
                    print("  Verify that DERIV_API_TOKEN_REAL is configured correctly")
                    return
            else:
                print("\n❌ Cannot test REAL environment: Missing DERIV_API_TOKEN_REAL")
                return
        else:
            # Ensure we're in demo mode for testing
            config.set_environment('demo')

        print(f"\nTesting API connection in {config.get_environment().upper()} mode...")

        # Create and test the connector
        start_time = time.time()
        connector = DerivConnector(config)
        connected = await connector.connect()

        if not connected:
            print("❌ Failed to connect to Deriv API")
            return

        connection_time = time.time() - start_time
        print(f"✅ Successfully connected to Deriv API ({connection_time:.2f}s)")

        # Test server time retrieval
        print("\nVerifying server time...")
        time_response = await connector.get_server_time()

        if time_response and "time" in time_response:
            server_time = datetime.fromtimestamp(time_response["time"])
            local_time = datetime.now()
            time_diff = abs((local_time - server_time).total_seconds())
            print(f"✅ Server time: {server_time}")
            print(f"  Local time: {local_time}")
            print(f"  Difference: {time_diff:.2f} seconds")
        else:
            print("❌ Could not retrieve server time")

        # Get available symbols
        print("\nRetrieving available symbols...")
        data_fetcher = DataFetcher(connector)
        symbols = await data_fetcher.get_available_symbols()

        if symbols:
            print(f"✅ Found {len(symbols)} trading symbols")
            print("Example symbols:", symbols[:5])
        else:
            print("❌ Could not retrieve trading symbols")

        # Test historical data retrieval
        print("\nTesting historical data retrieval for EUR/USD...")
        historical_data = await data_fetcher.fetch_historical_data(
            symbol="frxEURUSD",
            interval=60,  # 1-minute candles
            count=10  # Just a few candles for testing
        )

        if historical_data is not None:
            print(f"✅ Historical data successfully retrieved ({len(historical_data)} candles)")
            print("\nSample data:")
            print(historical_data.head())
        else:
            print("❌ Could not retrieve historical data")

        # Test tick subscription
        print("\nTesting tick subscription...")
        tick_response = await data_fetcher.subscribe_to_ticks("frxEURUSD")

        if tick_response and "error" not in tick_response:
            print("✅ Tick subscription successful")
        else:
            print("❌ Tick subscription failed")

        # Extended tests if requested
        if extended_test:
            print("\n=== Running Extended Tests ===")

            # Load test: try to get a large dataset
            print("\nLoad test: Retrieving 1000 candles...")
            start_time = time.time()
            large_dataset = await data_fetcher.fetch_historical_data(
                symbol="frxEURUSD",
                interval=60,
                count=1000
            )
            load_time = time.time() - start_time

            if large_dataset is not None and len(large_dataset) > 900:
                print(f"✅ Large dataset retrieved ({len(large_dataset)} candles in {load_time:.2f}s)")
            else:
                print(f"❌ Issues retrieving large dataset")
                if large_dataset is not None:
                    print(f"  Requested 1000 candles, received {len(large_dataset)}")

            # Reconnection test
            print("\nReconnection test: Simulating disconnection...")
            await connector.close()
            reconnect_result = await connector.reconnect()

            if reconnect_result:
                print("✅ Reconnection successful")
            else:
                print("❌ Reconnection failed")

            # Request frequency test
            print("\nRequest frequency test: 5 rapid requests...")
            for i in range(5):
                start_req = time.time()
                mini_data = await data_fetcher.fetch_historical_data(
                    symbol="frxEURUSD",
                    interval=60,
                    count=5
                )
                req_time = time.time() - start_req
                status = "✅" if mini_data is not None else "❌"
                print(f"  Request {i+1}: {status} ({req_time:.2f}s)")

            print("\nExtended tests completed")

        # Cleanup
        await connector.close()
        print("\n✅ Connection properly closed")

        # If we changed to real mode just for testing, restore
        if test_mode == 'real' and original_env != 'real':
            config.set_environment(original_env)
            if original_confirmed:
                os.environ['DERIV_REAL_MODE_CONFIRMED'] = original_confirmed
            else:
                os.environ.pop('DERIV_REAL_MODE_CONFIRMED', None)
            print(f"\nEnvironment restored to {config.get_environment().upper()}")

        # Summary
        print("\n=== Test Summary ===")
        print(f"✅ Environment: {config.get_environment().upper()}")
        print(f"✅ API Connection: {'Successful' if connected else 'Failed'}")
        print(f"✅ Symbol Retrieval: {'Successful' if symbols else 'Failed'}")
        print(f"✅ Historical Data: {'Successful' if historical_data is not None else 'Failed'}")
        print(f"✅ Tick Subscription: {'Successful' if tick_response and 'error' not in tick_response else 'Failed'}")
        print("\n============================")

    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        logger.exception("Error during API test")

def main():
    """Main function with command line parser"""
    parser = argparse.ArgumentParser(description="Test Deriv API connectivity")
    parser.add_argument("--mode", choices=["demo", "real"], default="demo",
                        help="Test mode: demo (default) or real environment")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show verbose output")
    parser.add_argument("--extended", "-e", action="store_true",
                        help="Run extended tests")

    args = parser.parse_args()

    print("Starting Deriv API connectivity test...")
    print("===============================================")
    print(f"Mode: {args.mode.upper()}")

    asyncio.run(test_api_connectivity(
        test_mode=args.mode,
        verbose=args.verbose,
        extended_test=args.extended
    ))

if __name__ == "__main__":
    main()