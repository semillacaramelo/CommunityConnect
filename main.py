"""
Main entry point for the Deriv ML Trading Bot
"""
import asyncio
import os
import argparse
import sys
import signal
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
from deriv_bot.utils.model_manager import ModelManager

logger = setup_logger(__name__)

# Global variable to handle graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals"""
    global shutdown_requested
    logger.info("Shutdown signal received. Cleaning up...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Deriv ML Trading Bot')
    parser.add_argument('--env', choices=['demo', 'real'], default=None,
                        help='Trading environment (demo or real). If not specified, uses DERIV_BOT_ENV from .env file')
    parser.add_argument('--train-only', action='store_true',
                        help='Only train the model without trading')
    parser.add_argument('--symbol', default='frxEURUSD',
                        help='Trading symbol')
    parser.add_argument('--clean-models', action='store_true',
                        help='Clean up old model files before starting')
    parser.add_argument('--stake-amount', type=float,
                        help='Stake amount for trades')
    parser.add_argument('--train-interval', type=int, default=4,
                        help='Hours between model retraining (default: 4)')
    parser.add_argument('--check-connection', action='store_true',
                        help='Only check API connection and exit')
    parser.add_argument('--data-source', choices=['api', 'file', 'both'], default='api',
                        help='Source for training data: api (from Deriv API), file (from saved data files), '
                             'or both (combine API and file data)')
    parser.add_argument('--save-data', action='store_true',
                        help='Save fetched historical data for future use')
    parser.add_argument('--model-types', nargs='+',
                        default=['short_term', 'medium_term', 'long_term'],
                        help='Types of models to train (space-separated list)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with more verbose output')

    # Training custom parameters
    parser.add_argument('--sequence-length', type=int,
                        help='Sequence length for LSTM models')
    parser.add_argument('--epochs', type=int,
                        help='Number of training epochs')
    return parser.parse_args()

async def initialize_components(args, config):
    """Initialize and connect all components"""
    try:
        # Set trading environment from args, then from env var if not specified
        if args.env:
            env_mode = args.env
        else:
            env_mode = os.getenv('DERIV_BOT_ENV', 'demo').lower()

        if not config.set_environment(env_mode):
            logger.error(f"Failed to set environment to {env_mode}")
            return None

        # Update trading configuration if provided in args
        if args.symbol:
            config.trading_config['symbol'] = args.symbol
        if args.stake_amount:
            config.trading_config['stake_amount'] = args.stake_amount

        connector = DerivConnector(config)

        # Connect to Deriv API with retry
        max_retries = 5
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

        # Always use demo risk profile when in demo mode
        is_demo = config.is_demo()
        risk_manager = RiskManager(is_demo=is_demo)

        # Warning for real mode
        if not is_demo:
            logger.warning("⚠️ RUNNING IN REAL TRADING MODE - ACTUAL FUNDS WILL BE USED! ⚠️")

        order_executor = OrderExecutor(connector)
        performance_tracker = PerformanceTracker()
        model_manager = ModelManager(max_models=int(os.getenv('MAX_MODELS_KEPT', '5')))

        # Clean up old model files if requested
        if args.clean_models:
            archived = model_manager.archive_old_models()
            logger.info(f"Archived {archived} old model files")
            deleted = model_manager.cleanup_archive(keep_days=30)
            logger.info(f"Deleted {deleted} expired archive files")

        logger.info("All components initialized successfully")
        return {
            'config': config,
            'connector': connector,
            'data_fetcher': data_fetcher,
            'data_processor': data_processor,
            'risk_manager': risk_manager,
            'order_executor': order_executor,
            'performance_tracker': performance_tracker,
            'model_manager': model_manager
        }

    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return None

async def maintain_connection(connector):
    """Maintain API connection"""
    reconnect_attempts = 0
    max_reconnect_attempts = 10
    reconnect_delay = 30  # Initial delay in seconds

    while not shutdown_requested:
        try:
            if not await connector.check_connection():
                logger.warning("Connection lost, attempting to reconnect...")

                if reconnect_attempts >= max_reconnect_attempts:
                    logger.error(f"Failed to reconnect after {max_reconnect_attempts} attempts. Exiting...")
                    return False

                # Exponential backoff for reconnection attempts
                actual_delay = reconnect_delay * (2 ** reconnect_attempts)
                if actual_delay > 300:  # Cap at 5 minutes
                    actual_delay = 300

                logger.info(f"Reconnection attempt {reconnect_attempts + 1}/{max_reconnect_attempts} in {actual_delay}s")
                await asyncio.sleep(actual_delay)

                connected = await connector.connect()
                if connected:
                    logger.info("Successfully reconnected")
                    reconnect_attempts = 0  # Reset counter on success
                else:
                    logger.error("Failed to reconnect")
                    reconnect_attempts += 1
            else:
                # Reset reconnect attempts counter when connection is stable
                reconnect_attempts = 0

        except Exception as e:
            logger.error(f"Error in connection maintenance: {str(e)}")
            reconnect_attempts += 1

        await asyncio.sleep(30)  # Check connection every 30 seconds

    # If we get here, shutdown was requested
    logger.info("Connection maintenance loop terminated")
    return True

async def load_historical_data(data_fetcher, args, symbol, count=1000):
    """
    Load historical data from API and/or local files

    Args:
        data_fetcher: Initialized DataFetcher instance
        args: Command line arguments
        symbol: Trading symbol to fetch data for
        count: Number of data points to request from API

    Returns:
        DataFrame with historical price data or None if failed
    """
    try:
        data_source = args.data_source.lower()

        # Try to load from file if requested
        file_data = None
        if data_source in ['file', 'both']:
            data_file = f"data/{symbol}_historical.csv"
            if os.path.exists(data_file):
                import pandas as pd
                try:
                    file_data = pd.read_csv(data_file, index_col='time', parse_dates=True)
                    logger.info(f"Loaded {len(file_data)} historical data points from {data_file}")
                except Exception as e:
                    logger.error(f"Failed to load data from file: {str(e)}")
                    if data_source == 'file':
                        logger.warning("Falling back to API data fetch")
                        data_source = 'api'
            else:
                logger.warning(f"Historical data file not found: {data_file}")
                if data_source == 'file':
                    logger.warning("Falling back to API data fetch")
                    data_source = 'api'

        # Fetch from API if needed
        api_data = None
        if data_source in ['api', 'both']:
            logger.info(f"Fetching {count} historical data points for {symbol} from API...")
            api_data = await data_fetcher.fetch_historical_data(
                symbol, interval=60, count=count
            )

            if api_data is None:
                logger.error("Failed to fetch data from API")
                if data_source == 'both' and file_data is not None:
                    logger.info("Using only file data for training")
                    return file_data
                return None

            logger.info(f"Successfully fetched {len(api_data)} data points from API")

            # Save to file if requested
            if args.save_data:
                os.makedirs("data", exist_ok=True)
                data_file = f"data/{symbol}_historical.csv"
                try:
                    api_data.to_csv(data_file)
                    logger.info(f"Saved historical data to {data_file}")
                except Exception as e:
                    logger.error(f"Failed to save historical data: {str(e)}")

        # Combine data if both sources are used
        if data_source == 'both' and file_data is not None and api_data is not None:
            import pandas as pd
            # Use file_data for older entries, api_data for more recent
            combined_data = pd.concat([file_data, api_data])
            # Remove duplicates (keeping new data)
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            # Sort by time index
            combined_data.sort_index(inplace=True)
            logger.info(f"Combined dataset created with {len(combined_data)} total data points")
            return combined_data

        return api_data if data_source in ['api', 'both'] else file_data

    except Exception as e:
        logger.error(f"Error loading historical data: {str(e)}")
        return None

async def train_model(components, historical_data, model_type='standard', save_timestamp=True, args=None):
    """
    Train model with latest data

    Args:
        components: Initialized components
        historical_data: Historical price data for training
        model_type: Type of model to train (short_term, medium_term, long_term, etc.)
        save_timestamp: Whether to save model with timestamp (prevents overwriting)
        args: Command line arguments for additional parameters
    """
    try:
        # Get custom training parameters if provided
        sequence_length = args.sequence_length if args and args.sequence_length else None
        epochs = args.epochs if args and args.epochs else None

        logger.info(f"Training {model_type} model with {len(historical_data)} data points")

        # Process data for training
        processed_data = components['data_processor'].prepare_data(
            historical_data,
            sequence_length=sequence_length
        )

        if processed_data is None:
            logger.error(f"Failed to process historical data for {model_type} model")
            return None

        X, y, scaler = processed_data
        if X is None or y is None:
            logger.error(f"Invalid processed data for {model_type} model")
            return None

        logger.info(f"Prepared training data with shape X: {X.shape}, y: {y.shape}")

        # Train the model
        model_trainer = ModelTrainer(
            input_shape=(X.shape[1], X.shape[2]),
            epochs=epochs
        )

        history = model_trainer.train(X, y)

        if history:
            logger.info(f"{model_type} model training completed successfully")

            if save_timestamp:
                # Save with timestamp to prevent overwriting existing models
                model_path = components['model_manager'].save_model_with_timestamp(
                    model_trainer.model,
                    base_name="trained_model",
                    model_type=model_type
                )
                if model_path:
                    logger.info(f"Saved {model_type} model to {model_path}")
                    return ModelPredictor(model_path)
                else:
                    logger.error(f"Failed to save {model_type} model")
                    return None
            else:
                # Save as standard name (will overwrite)
                model_path = os.path.join('models', f'{model_type}_model.h5')
                # Save model directly
                try:
                    model_trainer.model.save(model_path)
                    logger.info(f"{model_type} model saved to {model_path}")
                    return ModelPredictor(model_path)
                except Exception as e:
                    logger.error(f"Error saving {model_type} model to {model_path}: {str(e)}")
                    return None
        else:
            logger.error(f"{model_type} model training failed")
            return None

    except Exception as e:
        logger.error(f"Error training {model_type} model: {str(e)}")
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

async def check_api_connectivity():
    """Simple function to check API connectivity and configuration"""
    config = Config()

    try:
        # Get environment
        env_mode = os.getenv('DERIV_BOT_ENV', 'demo').lower()
        if not config.set_environment(env_mode):
            logger.error(f"Failed to set environment to {env_mode}")
            return False

        # Check if tokens exist
        demo_token = os.getenv('DERIV_API_TOKEN_DEMO')
        real_token = os.getenv('DERIV_API_TOKEN_REAL')
        real_confirmed = os.getenv('DERIV_REAL_MODE_CONFIRMED', 'no').lower() == 'yes'

        print(f"\nChecking environment configuration:")
        print(f"- Current mode: {env_mode.upper()}")
        print(f"- Demo token: {'Configured' if demo_token else 'Not configured'}")
        print(f"- Real token: {'Configured' if real_token else 'Not configured'}")
        print(f"- Real mode confirmed: {'Yes' if real_confirmed else 'No'}")

        # Connect and check API
        connector = DerivConnector(config)
        print(f"\nAttempting to connect to Deriv API ({env_mode.upper()} mode)...")
        connected = await connector.connect()

        if connected:
            print("✅ Successfully connected to Deriv API")

            # Get active symbols
            data_fetcher = DataFetcher(connector)
            symbols = await data_fetcher.get_available_symbols()

            if symbols:
                print(f"✅ Successfully fetched {len(symbols)} trading symbols")
                print(f"Sample symbols: {symbols[:5]}")
            else:
                print("❌ Failed to fetch trading symbols")

            # Close connection
            await connector.close()
            print("✅ Connection closed properly")
            return True
        else:
            print("❌ Failed to connect to Deriv API")
            return False

    except Exception as e:
        print(f"❌ Error during API connectivity check: {str(e)}")
        return False

async def main():
    # Parse command line arguments
    args = parse_arguments()

    # Set debug mode if requested
    if args.debug:
        import logging
        logging.getLogger('deriv_bot').setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")

    # Just check API connectivity if requested
    if args.check_connection:
        success = await check_api_connectivity()
        if not success:
            print("\n❌ API connectivity check failed. Please check your configuration.")
        sys.exit(0 if success else 1)

    # Initialize configuration
    config = Config()
    components = None
    last_training = None
    training_interval = timedelta(hours=args.train_interval)  # Use specified training interval
    execution_start = datetime.now()
    reconnection_task = None
    predictors = {}

    try:
        # Initialize components
        components = await initialize_components(args, config)
        if not components:
            logger.error("Failed to initialize components")
            return

        symbol = components['config'].trading_config['symbol']

        # Training-only mode
        if args.train_only:
            logger.info("=== Starting Model Training Only Mode ===")
            logger.info(f"Symbol: {symbol}")
            logger.info(f"Model types to train: {args.model_types}")

            # Fetch historical data for training
            logger.info("Loading historical data for training...")
            historical_data = await load_historical_data(
                components['data_fetcher'], args, symbol, count=1000
            )

            if historical_data is not None:
                logger.info(f"Successfully loaded {len(historical_data)} data points")

                # Train each model type
                for model_type in args.model_types:
                    logger.info(f"Training {model_type} model...")
                    model_path = f"models/{model_type}_model.h5"
                    predictor = await train_model(
                        components,
                        historical_data,
                        model_type=model_type,
                        model_path=model_path,
                        args=args
                    )

                    if predictor:
                        logger.info(f"{model_type} model training successful!")
                        predictors[model_type] = predictor
                    else:
                        logger.error(f"{model_type} model training failed")

                # Report results
                success_count = len(predictors)
                if success_count > 0:
                    logger.info(f"Successfully trained {success_count}/{len(args.model_types)} models")
                else:
                    logger.error("All model training failed")
            else:
                logger.error("Failed to load training data")

            logger.info("Training only mode completed - exiting")
            return

        # Regular trading mode
        env_mode = "REAL" if not config.is_demo() else "DEMO"
        logger.info("=== Starting Deriv ML Trading Bot ===")
        logger.info(f"Start time: {execution_start}")
        logger.info(f"Mode: {env_mode}")
        logger.info(f"Symbol: {symbol}")
        logger.info("Trading Parameters:")
        logger.info(f"- Stake Amount: {components['config'].trading_config['stake_amount']}")
        logger.info(f"- Duration: {components['config'].trading_config['duration']}s")
        logger.info(f"- Training Interval: {training_interval.total_seconds()/3600:.1f}h")
        logger.info(f"- Model Types: {args.model_types}")
        logger.info("====================================")

        # Start connection maintenance task
        reconnection_task = asyncio.create_task(maintain_connection(components['connector']))

        consecutive_errors = 0
        max_consecutive_errors = 5

        # Initial training if no models exist or they're too old
        for model_type in args.model_types:
            model_path = components['model_manager'].get_best_model_path(model_type=model_type)
            if model_path and os.path.exists(model_path):
                # Use existing model
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age > timedelta(days=1):
                    logger.info(f"Existing {model_type} model is {model_age.days} days old. Retraining...")
                    predictors[model_type] = None
                else:
                    logger.info(f"Loading existing {model_type} model from {model_path}")
                    predictors[model_type] = ModelPredictor(model_path)
            else:
                logger.info(f"No existing {model_type} model found. Training new model...")
                predictors[model_type] = None

        while not shutdown_requested:
            try:
                # Check if retraining is needed
                current_time = datetime.now()
                execution_time = current_time - execution_start
                logger.info(f"Bot running for: {execution_time}")

                needs_training = (
                    last_training is None or
                    (current_time - last_training) > training_interval or
                    any(predictor is None for predictor in predictors.values())
                )

                if needs_training:
                    logger.info("Starting model retraining cycle...")
                    historical_data = await load_historical_data(
                        components['data_fetcher'],
                        args,
                        symbol,
                        count=1000
                    )

                    if historical_data is not None:
                        # Train all required model types
                        training_success = True
                        for model_type in args.model_types:
                            predictor = await train_model(
                                components,
                                historical_data,
                                model_type=model_type,
                                save_timestamp=True,
                                args=args
                            )

                            if predictor:
                                predictors[model_type] = predictor
                                logger.info(f"{model_type} model successfully trained")
                            else:
                                training_success = False
                                logger.error(f"{model_type} model training failed")

                        if training_success:
                            last_training = current_time
                            logger.info("All models successfully retrained")
                            logger.info(f"Next training scheduled for: {current_time + training_interval}")
                            consecutive_errors = 0  # Reset error counter on successful training
                        else:
                            logger.warning("Some models failed to train")
                            consecutive_errors += 1
                    else:
                        logger.error("Failed to fetch training data")
                        consecutive_errors += 1
                        await asyncio.sleep(60)
                        continue

                # Check if we've had too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({consecutive_errors}). Restarting bot...")
                    # Force reconnection
                    await components['connector'].close()
                    await asyncio.sleep(30)
                    connected = await components['connector'].connect()
                    if connected:
                        logger.info("Successfully reconnected after multiple errors")
                        consecutive_errors = 0
                    else:
                        logger.error("Failed to reconnect after multiple errors. Exiting...")
                        break

                # Get latest market data
                latest_data = await components['data_fetcher'].fetch_historical_data(
                    symbol,
                    interval=60,
                    count=60
                )

                if latest_data is None:
                    logger.warning("Failed to fetch latest data, retrying...")
                    consecutive_errors += 1
                    await asyncio.sleep(60)
                    continue

                # Prepare data for prediction
                processed_sequence = components['data_processor'].prepare_data(latest_data)
                if processed_sequence is None:
                    logger.warning("Failed to process latest data, retrying...")
                    consecutive_errors += 1
                    await asyncio.sleep(60)
                    continue

                X_latest, _, _ = processed_sequence
                if X_latest is None or len(X_latest) == 0:
                    logger.warning("Invalid sequence data, retrying...")
                    consecutive_errors += 1
                    await asyncio.sleep(60)
                    continue

                # Get the last sequence for prediction
                sequence = X_latest[-1:]

                # Execute trade based on ensemble prediction from all model types
                # Use the first available model for now (in future, could implement ensemble voting)
                for model_type, predictor in predictors.items():
                    if predictor:
                        logger.info(f"Using {model_type} model for prediction")
                        trade_executed = await execute_trade(components, predictor, symbol, sequence)
                        if trade_executed:
                            consecutive_errors = 0  # Reset error counter on successful trade
                        break
                else:
                    logger.warning("No valid predictors available for trading")

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
                consecutive_errors += 1
                await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        if reconnection_task:
            reconnection_task.cancel()

        if components and components['connector']:
            await components['connector'].close()
            logger.info("Connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutdown requested. Exiting...")
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
        sys.exit(1)