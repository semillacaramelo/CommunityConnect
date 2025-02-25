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
from deriv_bot.execution.order_executor import OrderExecutor
from deriv_bot.monitor.logger import setup_logger
from deriv_bot.utils.config import Config

logger = setup_logger('trading_simulation')

class MockOrderExecutor:
    """Mock order executor for simulation"""
    async def place_order(self, symbol, contract_type, amount, duration):
        logger.info(f"SIMULATION: Would place {contract_type} order for {symbol}, amount: {amount}")
        return {
            'contract_id': 'mock_id_' + datetime.now().strftime('%H%M%S'),
            'transaction_id': 'mock_tx_' + datetime.now().strftime('%H%M%S'),
            'price': 1.0000  # Simulated entry price
        }

async def run_trading_simulation():
    """Run trading simulation with real data but mock order execution"""
    try:
        # Initialize components
        config = Config()
        connector = DerivConnector()
        
        # Connect to API
        connected = await connector.connect()
        if not connected:
            logger.error("Failed to connect to Deriv API")
            return
            
        logger.info("Connected to Deriv API")
        
        # Initialize components with real data handling but mock execution
        data_fetcher = DataFetcher(connector)
        data_processor = DataProcessor()
        risk_manager = RiskManager()
        mock_executor = MockOrderExecutor()
        
        # Test with EUR/USD
        symbol = "frxEURUSD"
        
        # Fetch initial data
        logger.info(f"Fetching historical data for {symbol}")
        historical_data = await data_fetcher.fetch_historical_data(
            symbol,
            interval=60,
            count=100  # Smaller sample for testing
        )
        
        if historical_data is None:
            logger.error("Failed to fetch historical data")
            return
            
        logger.info(f"Successfully fetched {len(historical_data)} candles")
        
        # Process data
        processed_data = data_processor.prepare_data(historical_data)
        if processed_data is None:
            logger.error("Failed to process historical data")
            return
            
        X, y, scaler = processed_data
        
        if X is not None and y is not None:
            # Train model
            logger.info("Training model with historical data")
            model_trainer = ModelTrainer(input_shape=(X.shape[1], X.shape[2]))
            history = model_trainer.train(X, y, epochs=5)  # Quick training for testing
            
            if not history:
                logger.error("Model training failed")
                return
                
            logger.info("Model training completed")
            
            # Initialize predictor
            predictor = ModelPredictor()
            predictor.model = model_trainer.model
            
            # Run simulation loop
            logger.info("Starting trading simulation loop")
            iteration = 0
            
            while iteration < 5:  # Run 5 iterations for testing
                try:
                    # Get latest data
                    latest_data = await data_fetcher.fetch_historical_data(
                        symbol,
                        interval=60,
                        count=60
                    )
                    
                    if latest_data is None:
                        logger.warning("Failed to fetch latest data, retrying...")
                        await asyncio.sleep(5)
                        continue
                        
                    # Process latest data
                    processed_sequence = data_processor.prepare_data(latest_data)
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
                    
                    # Make prediction
                    prediction = predictor.predict(sequence)
                    
                    if prediction is not None:
                        # Simulate trade execution
                        amount = config.trading_config['stake_amount']
                        if risk_manager.validate_trade(symbol, amount, prediction):
                            contract_type = 'CALL' if prediction > 0 else 'PUT'
                            result = await mock_executor.place_order(
                                symbol,
                                contract_type,
                                amount,
                                config.trading_config['duration']
                            )
                            
                            if result:
                                logger.info(f"Simulation trade executed: {contract_type} {amount}")
                                
                    iteration += 1
                    logger.info(f"Completed simulation iteration {iteration}/5")
                    await asyncio.sleep(5)  # Shorter wait for testing
                    
                except Exception as e:
                    logger.error(f"Error in simulation loop: {str(e)}")
                    await asyncio.sleep(5)
                    
        logger.info("Trading simulation completed")
        
    except Exception as e:
        logger.error(f"Fatal error in simulation: {str(e)}")
    finally:
        if connector:
            await connector.close()
            
if __name__ == "__main__":
    print("Starting trading simulation...")
    print("=" * 30)
    asyncio.run(run_trading_simulation())
