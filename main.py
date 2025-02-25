"""
Main entry point for the Deriv ML Trading Bot
"""
import asyncio
import os
from datetime import datetime, timedelta
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

async def initialize_components():
    """Initialize and connect all components"""
    try:
        config = Config()
        connector = DerivConnector()

        # Connect to Deriv API with retry
        max_retries = 5  # Increased retries
        retry_delay = 10  # Seconds between retries

        for attempt in range(max_retries):
            connected = await connector.connect()
            if connected:
                break
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)

        if not connected:
            raise Exception("Failed to connect to Deriv API after multiple attempts")

        # Initialize components
        data_fetcher = DataFetcher(connector)
        data_processor = DataProcessor()
        risk_manager = RiskManager(is_demo=True)  # Always use DEMO for safety
        order_executor = OrderExecutor(connector)  # Real order executor
        performance_tracker = PerformanceTracker()

        logger.info("All components initialized successfully")
        return {
            'config': config,
            'connector': connector,
            'data_fetcher': data_fetcher,
            'data_processor': data_processor,
            'risk_manager': risk_manager,
            'order_executor': order_executor,
            'performance_tracker': performance_tracker
        }

    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        raise

async def maintain_connection(connector):
    """Maintain API connection"""
    while True:
        try:
            if not await connector.check_connection():
                logger.warning("Connection lost, attempting to reconnect...")
                connected = await connector.connect()
                if connected:
                    logger.info("Successfully reconnected")
                else:
                    logger.error("Failed to reconnect")
        except Exception as e:
            logger.error(f"Error in connection maintenance: {str(e)}")
        await asyncio.sleep(30)  # Check connection every 30 seconds

async def train_model(components, historical_data):
    """Train model with latest data"""
    try:
        processed_data = components['data_processor'].prepare_data(historical_data)
        if processed_data is None:
            logger.error("Failed to process historical data")
            return None

        X, y, scaler = processed_data
        if X is None or y is None:
            logger.error("Invalid processed data")
            return None

        model_trainer = ModelTrainer(input_shape=(X.shape[1], X.shape[2]))
        history = model_trainer.train(X, y)

        if history:
            logger.info("Model training completed successfully")
            model_trainer.save_model('trained_model.h5')
            return ModelPredictor('trained_model.h5')
        else:
            logger.error("Model training failed")
            return None

    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return None

async def execute_trade(components, predictor, symbol, sequence):
    """Execute a trade based on model prediction"""
    try:
        prediction_result = predictor.predict(sequence)

        if prediction_result is not None:
            prediction = prediction_result['prediction']
            confidence = prediction_result['confidence']

            logger.info(f"Prediction: {prediction:.2%} (confidence: {confidence:.2f})")

            # Execute trade if prediction is significant
            amount = components['config'].trading_config['stake_amount']
            if abs(prediction) >= 0.001:  # 0.1% minimum move
                if components['risk_manager'].validate_trade(symbol, amount, prediction):
                    contract_type = 'CALL' if prediction > 0 else 'PUT'
                    duration = components['config'].trading_config['duration']

                    result = await components['order_executor'].place_order(
                        symbol,
                        contract_type,
                        amount,
                        duration
                    )

                    if result:
                        logger.info(f"Trade executed: {contract_type} {amount}")
                        return True
            else:
                logger.info(f"No trade: predicted move ({prediction:.2%}) below threshold")

        return False

    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return False

async def main():
    components = None
    last_training = None
    training_interval = timedelta(hours=4)  # Retrain every 4 hours
    execution_start = datetime.now()

    try:
        # Initialize components
        components = await initialize_components()
        symbol = components['config'].trading_config['symbol']

        logger.info("=== Starting Deriv ML Trading Bot ===")
        logger.info(f"Start time: {execution_start}")
        logger.info("Mode: DEMO")
        logger.info(f"Symbol: {symbol}")
        logger.info("Trading Parameters:")
        logger.info(f"- Stake Amount: {components['config'].trading_config['stake_amount']}")
        logger.info(f"- Duration: {components['config'].trading_config['duration']}s")
        logger.info(f"- Training Interval: {training_interval.total_seconds()/3600:.1f}h")
        logger.info("====================================")

        # Start connection maintenance task
        asyncio.create_task(maintain_connection(components['connector']))

        while True:
            try:
                # Check if retraining is needed
                current_time = datetime.now()
                execution_time = current_time - execution_start
                logger.info(f"Bot running for: {execution_time}")

                if last_training is None or (current_time - last_training) > training_interval:
                    logger.info("Starting model retraining cycle...")
                    historical_data = await components['data_fetcher'].fetch_historical_data(
                        symbol,
                        interval=60,
                        count=1000
                    )

                    if historical_data is not None:
                        predictor = await train_model(components, historical_data)
                        if predictor:
                            last_training = current_time
                            logger.info("Model successfully retrained")
                            logger.info(f"Next training scheduled for: {current_time + training_interval}")
                    else:
                        logger.error("Failed to fetch training data")
                        await asyncio.sleep(60)
                        continue

                # Get latest market data
                latest_data = await components['data_fetcher'].fetch_historical_data(
                    symbol,
                    interval=60,
                    count=60
                )

                if latest_data is None:
                    logger.warning("Failed to fetch latest data, retrying...")
                    await asyncio.sleep(60)
                    continue

                # Prepare data for prediction
                processed_sequence = components['data_processor'].prepare_data(latest_data)
                if processed_sequence is None:
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

                # Execute trade based on prediction
                await execute_trade(components, predictor, symbol, sequence)

                # Log performance metrics periodically
                if execution_time.total_seconds() % 3600 < 60:  # Every hour
                    metrics = components['performance_tracker'].get_statistics()
                    logger.info("\n=== Hourly Performance Update ===")
                    logger.info(f"Total Runtime: {execution_time}")
                    logger.info(f"Performance Metrics: {metrics}")
                    logger.info("=================================")

                # Wait before next iteration
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        if components and components['connector']:
            await components['connector'].close()

if __name__ == "__main__":
    asyncio.run(main())