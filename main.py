"""
Main entry point for the Deriv ML Trading Bot
"""
import asyncio
from deriv_bot.data.deriv_connector import DerivConnector
from deriv_bot.data.data_fetcher import DataFetcher
from deriv_bot.data.data_processor import DataProcessor
from deriv_bot.strategy.model_trainer import ModelTrainer
from deriv_bot.strategy.model_predictor import ModelPredictor
from deriv_bot.risk.risk_manager import RiskManager
from deriv_bot.execution.order_executor import OrderExecutor
from deriv_bot.monitor.logger import setup_logger
from deriv_bot.monitor.performance import PerformanceTracker
from deriv_bot.utils.config import Config

logger = setup_logger(__name__)

async def main():
    connector = None
    try:
        # Initialize components
        config = Config()
        connector = DerivConnector()

        # Connect to Deriv API
        connected = await connector.connect()
        if not connected:
            logger.error("Failed to connect to Deriv API")
            return

        # Initialize other components
        data_fetcher = DataFetcher(connector)
        data_processor = DataProcessor()
        risk_manager = RiskManager()
        order_executor = OrderExecutor(connector)
        performance_tracker = PerformanceTracker()

        # Fetch historical data
        symbol = config.trading_config['symbol']
        historical_data = await data_fetcher.fetch_historical_data(
            symbol,
            interval=60,
            count=1000
        )

        if historical_data is None:
            logger.error("Failed to fetch historical data")
            return

        # Prepare data and train model
        processed_data = data_processor.prepare_data(historical_data)
        if processed_data is None:
            logger.error("Failed to process historical data")
            return

        X, y, scaler = processed_data

        if X is not None and y is not None:
            model_trainer = ModelTrainer(input_shape=(X.shape[1], X.shape[2]))
            history = model_trainer.train(X, y)

            if history:
                logger.info("Model training completed successfully")
                model_trainer.save_model('trained_model.h5')
            else:
                logger.error("Model training failed")
                return

        # Start real-time trading loop
        predictor = ModelPredictor('trained_model.h5')

        while True:
            try:
                # Get latest market data
                latest_data = await data_fetcher.fetch_historical_data(
                    symbol,
                    interval=60,
                    count=60
                )

                if latest_data is None:
                    logger.warning("Failed to fetch latest data, retrying...")
                    await asyncio.sleep(60)
                    continue

                # Prepare data for prediction
                processed_sequence = data_processor.prepare_data(latest_data)
                if processed_sequence is None or len(processed_sequence) < 3:
                    logger.warning("Failed to process latest data, retrying...")
                    await asyncio.sleep(60)
                    continue

                X_latest, _, _ = processed_sequence
                if X_latest is None or len(X_latest) == 0:
                    logger.warning("Invalid sequence data, retrying...")
                    await asyncio.sleep(60)
                    continue

                # Get the last sequence for prediction
                sequence = X_latest[-1:]

                # Make prediction
                prediction = predictor.predict(sequence)

                if prediction is not None:
                    # Validate trade with risk manager
                    amount = config.trading_config['stake_amount']
                    if risk_manager.validate_trade(symbol, amount, prediction):
                        # Execute trade
                        contract_type = 'CALL' if prediction > 0 else 'PUT'
                        result = await order_executor.place_order(
                            symbol,
                            contract_type,
                            amount,
                            config.trading_config['duration']
                        )

                        if result:
                            logger.info(f"Trade executed: {contract_type} {amount}")

                # Wait before next iteration
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        if connector:
            await connector.close()

if __name__ == "__main__":
    asyncio.run(main())