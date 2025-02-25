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
from deriv_bot.strategy.feature_engineering import FeatureEngineer
from deriv_bot.risk.risk_manager import RiskManager
from deriv_bot.monitor.performance import PerformanceTracker
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger('trading_simulation')

class MockOrderExecutor:
    """Mock order executor for simulation"""
    async def place_order(self, symbol, contract_type, amount, duration, stop_loss_pct=None):
        logger.info(f"SIMULATION: Would place {contract_type} order for {symbol}, amount: {amount}, stop_loss: {stop_loss_pct}%")
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
        # Initialize components with DEMO profile
        connector = DerivConnector()
        data_fetcher = DataFetcher(connector)
        data_processor = DataProcessor()
        feature_engineer = FeatureEngineer()
        risk_manager = RiskManager(is_demo=True, max_position_size=200, max_daily_loss=150)  # Aggressive DEMO settings
        mock_executor = MockOrderExecutor()
        performance_tracker = PerformanceTracker()

        # Log risk and strategy profiles
        risk_profile = risk_manager.get_risk_profile()
        logger.info("=== DEMO Trading Simulation Configuration ===")
        logger.info(f"Risk Profile: {risk_profile}")
        logger.info("Trading Parameters:")
        logger.info("- Confidence Threshold: 0.6 (DEMO)")
        logger.info("- Position Size: 20.0 (Higher for DEMO)")
        logger.info("- Trade Duration: 30s (Faster for DEMO)")
        logger.info("- Stop Loss: 5.0% (Wider for DEMO)")
        logger.info("==========================================")

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
            count=500
        )

        if historical_data is None:
            logger.error("Failed to fetch historical data")
            return

        logger.info(f"Successfully fetched {len(historical_data)} candles")

        # Add enhanced features
        historical_data = feature_engineer.calculate_features(historical_data)
        if historical_data is None:
            logger.error("Failed to calculate features")
            return

        logger.info(f"Calculated features. Shape: {historical_data.shape}")
        logger.info(f"Features: {historical_data.columns.tolist()}")

        # Process data with shorter sequence length for demo
        sequence_length = 30
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

        # Train ensemble model
        logger.info("Training ensemble models")
        model_trainer = ModelTrainer(input_shape=(X.shape[1], X.shape[2]))
        history = model_trainer.train(X, y, epochs=10)  # Quick training for testing

        if not history:
            logger.error("Model training failed")
            return

        logger.info("Model training completed")

        # Save models
        model_trainer.save_models('models')

        # Initialize predictor with trained models
        predictor = ModelPredictor('models')

        # Run simulation loop with DEMO confidence threshold
        logger.info("Starting trading simulation loop")
        iteration = 0
        trades_executed = 0
        successful_trades = 0
        confidence_threshold = 0.6  # Lower threshold for DEMO

        while iteration < 10:  # Run 10 iterations for testing
            try:
                logger.info(f"\n=== Iteration {iteration + 1}/10 ===")
                logger.info(f"Current Stats - Trades: {trades_executed}, Successful: {successful_trades}")

                # Get latest data
                latest_data = await data_fetcher.fetch_historical_data(
                    symbol,
                    interval=60,
                    count=200
                )

                if latest_data is None:
                    logger.warning("Failed to fetch latest data, retrying...")
                    await asyncio.sleep(5)
                    continue

                # Calculate features
                latest_data = feature_engineer.calculate_features(latest_data)
                if latest_data is None:
                    logger.warning("Failed to calculate features, retrying...")
                    await asyncio.sleep(5)
                    continue

                # Process data
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

                # Get the last sequence for prediction
                sequence = X_latest[-1:]
                prediction_result = predictor.predict(sequence, confidence_threshold)

                if prediction_result is not None:
                    prediction = prediction_result['prediction']
                    confidence = prediction_result['confidence']
                    logger.info(f"Prediction value: {prediction:.4f} (confidence: {confidence:.2f})")

                    current_price = latest_data['close'].iloc[-1]
                    price_diff = prediction - current_price
                    price_change_pct = (price_diff / current_price) * 100

                    logger.info(f"Current price: {current_price:.5f}")
                    logger.info(f"Predicted price: {prediction:.5f}")
                    logger.info(f"Predicted change: {price_change_pct:.2f}%")

                    # Get prediction metrics
                    metrics = predictor.get_prediction_metrics(sequence)
                    logger.info(f"Prediction metrics: {metrics}")

                    # Simulate trade execution with DEMO threshold
                    amount = 20.0  # Higher amount for DEMO
                    if abs(price_change_pct) >= 0.015:  # Lower threshold for DEMO
                        if risk_manager.validate_trade(symbol, amount, prediction):
                            contract_type = 'CALL' if price_diff > 0 else 'PUT'
                            logger.info(f"Placing {contract_type} order, predicted move: {price_change_pct:.2f}%")

                            result = await mock_executor.place_order(
                                symbol,
                                contract_type,
                                amount,
                                30,  # Shorter duration for DEMO
                                stop_loss_pct=5.0  # Wider stop loss for DEMO
                            )

                            if result:
                                # Wait for contract duration
                                await asyncio.sleep(60)

                                # Fetch latest price
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
                                        'confidence': confidence,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    performance_tracker.add_trade(trade_data)

                                    # Log detailed trade performance
                                    logger.info("\n=== Trade Performance Update ===")
                                    logger.info(f"Win Rate: {(successful_trades/trades_executed)*100:.1f}%")
                                    logger.info(f"Prediction Accuracy: {abs(price_change_pct - actual_change_pct):.2f}%")
                                    stats = performance_tracker.get_statistics()
                                    if stats:
                                        logger.info(f"Performance Stats: {stats}")
                                else:
                                    logger.error("Failed to fetch next price after trade")

                    else:
                        logger.info(f"No trade: predicted move ({price_change_pct:.2f}%) below threshold")
                else:
                    logger.info("No trade: prediction confidence below threshold")

                iteration += 1
                logger.info(f"Completed simulation iteration {iteration}/10")

                # Wait before next iteration
                await asyncio.sleep(5)  # Shorter wait for testing

            except Exception as e:
                logger.error(f"Error in simulation loop: {str(e)}")
                await asyncio.sleep(5)

        # Final performance report
        logger.info("\n=== Final Simulation Report ===")
        logger.info(f"Total Trades Executed: {trades_executed}")
        if trades_executed > 0:
            win_rate = (successful_trades / trades_executed) * 100
            logger.info(f"Final Win Rate: {win_rate:.1f}%")

            # Get detailed statistics
            stats = performance_tracker.get_statistics()
            if stats:
                logger.info("\nDetailed Performance Metrics:")
                for key, value in stats.items():
                    logger.info(f"{key}: {value}")

            # Export results
            performance_tracker.export_history('simulation_results.csv')
            logger.info("\nSimulation results exported to simulation_results.csv")
        else:
            logger.warning("No trades executed during simulation")

        logger.info("\nTrading simulation completed")

    except Exception as e:
        logger.error(f"Fatal error in simulation: {str(e)}")
    finally:
        if connector:
            await connector.close()

if __name__ == "__main__":
    print("Starting trading simulation...")
    print("=" * 30)
    asyncio.run(run_trading_simulation())