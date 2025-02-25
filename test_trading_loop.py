"""
Test script for simulating the trading loop without executing real trades
"""
import asyncio
import pandas as pd
from datetime import datetime
from deriv_bot.data.deriv_connector import DerivConnector
from deriv_bot.data.data_fetcher import DataFetcher
from deriv_bot.data.data_processor import DataProcessor
from deriv_bot.strategy.model_trainer import ModelTrainer
from deriv_bot.strategy.model_predictor import ModelPredictor
from deriv_bot.risk.risk_manager import RiskManager
from deriv_bot.monitor.performance import PerformanceTracker
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger('trading_simulation')

class MockOrderExecutor:
    """Mock order executor for simulation"""
    async def place_order(self, symbol, contract_type, amount, duration):
        logger.info(f"SIMULATION: Would place {contract_type} order for {symbol}, amount: {amount}")
        return {
            'contract_id': 'mock_id_' + datetime.now().strftime('%H%M%S'),
            'transaction_id': 'mock_tx_' + datetime.now().strftime('%H%M%S'),
            'entry_tick': 0,
            'entry_tick_time': datetime.now().timestamp()
        }

async def run_trading_simulation():
    """Run trading simulation with real data but mock order execution"""
    connector = None
    try:
        # Initialize components
        connector = DerivConnector()
        data_fetcher = DataFetcher(connector)
        data_processor = DataProcessor()
        risk_manager = RiskManager()
        mock_executor = MockOrderExecutor()
        performance_tracker = PerformanceTracker()

        # Connect to API
        connected = await connector.connect()
        if not connected:
            logger.error("Failed to connect to Deriv API")
            return

        logger.info("Connected to Deriv API")

        # Test with EUR/USD
        symbol = "frxEURUSD"

        # Fetch initial data
        logger.info(f"Fetching historical data for {symbol}")
        historical_data = await data_fetcher.fetch_historical_data(
            symbol,
            interval=60,
            count=200  # Increased to ensure enough data after indicator calculation
        )

        if historical_data is None:
            logger.error("Failed to fetch historical data")
            return

        logger.info(f"Successfully fetched {len(historical_data)} candles")
        logger.info(f"Data columns: {historical_data.columns.tolist()}")
        logger.info(f"Sample data:\n{historical_data.head()}")

        # Process data with shorter sequence length
        sequence_length = 30  # Reduced from 60 to work with available data
        logger.info(f"Processing data with sequence length: {sequence_length}")

        processed_data = data_processor.prepare_data(
            df=historical_data,
            sequence_length=sequence_length
        )

        if processed_data is None:
            logger.error("Failed to process historical data")
            return

        X, y, scaler = processed_data
        if X is None or y is None:
            logger.error("Invalid processed data")
            return

        logger.info(f"Processed data shapes - X: {X.shape}, y: {y.shape}")

        # Train model with minimal epochs for testing
        logger.info("Training model with historical data")
        model_trainer = ModelTrainer(input_shape=(X.shape[1], X.shape[2]))
        history = model_trainer.train(X, y, epochs=5)  # Quick training for testing

        if not history:
            logger.error("Model training failed")
            return

        logger.info("Model training completed")

        # Initialize predictor with trained model
        predictor = ModelPredictor()
        predictor.model = model_trainer.model

        # Run simulation loop
        logger.info("Starting trading simulation loop")
        iteration = 0
        trades_executed = 0
        successful_trades = 0

        while iteration < 5:  # Run 5 iterations for testing
            try:
                # Get latest data
                latest_data = await data_fetcher.fetch_historical_data(
                    symbol,
                    interval=60,
                    count=100  # Fetch enough for indicator calculation
                )

                if latest_data is None:
                    logger.warning("Failed to fetch latest data, retrying...")
                    await asyncio.sleep(5)
                    continue

                logger.info(f"Latest data shape: {latest_data.shape}")

                # Process latest data with same sequence length
                processed_sequence = data_processor.prepare_data(
                    df=latest_data,
                    sequence_length=sequence_length
                )

                if processed_sequence is None:
                    logger.warning("Failed to process latest data, retrying...")
                    await asyncio.sleep(5)
                    continue

                X_latest, _, _ = processed_sequence
                if X_latest is None or len(X_latest) == 0:
                    logger.warning("Invalid sequence data, retrying...")
                    await asyncio.sleep(5)
                    continue

                logger.info(f"Processed sequence shape: {X_latest.shape}")

                # Get the last sequence for prediction
                sequence = X_latest[-1:]
                prediction = predictor.predict(sequence)

                if prediction is not None:
                    logger.info(f"Prediction value: {prediction:.4f}")
                    current_price = latest_data['close'].iloc[-1]
                    price_diff = prediction - current_price
                    price_change_pct = (price_diff / current_price) * 100

                    logger.info(f"Current price: {current_price:.5f}")
                    logger.info(f"Predicted price: {prediction:.5f}")
                    logger.info(f"Predicted change: {price_change_pct:.2f}%")

                    # Simulate trade execution
                    amount = 10.0  # Fixed amount for simulation
                    if abs(price_change_pct) >= 0.02:  # Minimum 0.02% predicted move
                        if risk_manager.validate_trade(symbol, amount, prediction):
                            contract_type = 'CALL' if price_diff > 0 else 'PUT'
                            logger.info(f"Placing {contract_type} order, predicted move: {price_change_pct:.2f}%")

                            result = await mock_executor.place_order(
                                symbol,
                                contract_type,
                                amount,
                                60  # 1-minute contracts for testing
                            )

                            if result:
                                # Wait for 1 minute to get the next price (simulating contract settlement)
                                await asyncio.sleep(60)

                                # Fetch latest price after waiting period
                                next_data = await data_fetcher.fetch_historical_data(
                                    symbol,
                                    interval=60,
                                    count=1
                                )

                                if next_data is not None:
                                    trades_executed += 1
                                    next_price = next_data['close'].iloc[-1]
                                    actual_change_pct = ((next_price - current_price) / current_price) * 100

                                    # Determine if trade was successful
                                    if (contract_type == 'CALL' and next_price > current_price) or \
                                       (contract_type == 'PUT' and next_price < current_price):
                                        successful_trades += 1
                                        logger.info(f"Successful trade! Price moved {actual_change_pct:.2f}%")
                                    else:
                                        logger.info(f"Unsuccessful trade. Price moved {actual_change_pct:.2f}%")

                                    # Record trade for performance tracking
                                    trade_data = {
                                        'symbol': symbol,
                                        'type': contract_type,
                                        'amount': amount,
                                        'entry_price': current_price,
                                        'exit_price': next_price,
                                        'predicted_change': price_change_pct,
                                        'actual_change': actual_change_pct,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    performance_tracker.add_trade(trade_data)
                                else:
                                    logger.error("Failed to fetch next price after trade")

                    else:
                        logger.info(f"No trade: predicted move ({price_change_pct:.2f}%) below threshold")

                iteration += 1
                logger.info(f"Completed simulation iteration {iteration}/5")

                # Log performance metrics
                if trades_executed > 0:
                    win_rate = (successful_trades / trades_executed) * 100
                    logger.info(f"Current performance - Trades: {trades_executed}, "
                              f"Successful: {successful_trades}, Win Rate: {win_rate:.1f}%")

                    # Get detailed statistics
                    stats = performance_tracker.get_statistics()
                    if stats:
                        logger.info(f"Performance statistics: {stats}")

                await asyncio.sleep(5)  # Shorter wait for testing

            except Exception as e:
                logger.error(f"Error in simulation loop: {str(e)}")
                await asyncio.sleep(5)

        logger.info("Trading simulation completed")

        # Export final performance statistics
        try:
            if trades_executed > 0:
                performance_tracker.export_history('simulation_results.csv')
                logger.info("Simulation results exported to simulation_results.csv")
            else:
                logger.warning("No trades executed during simulation")
        except Exception as e:
            logger.error(f"Failed to export simulation results: {str(e)}")

    except Exception as e:
        logger.error(f"Fatal error in simulation: {str(e)}")
    finally:
        if connector:
            await connector.close()

if __name__ == "__main__":
    print("Starting trading simulation...")
    print("=" * 30)
    asyncio.run(run_trading_simulation())