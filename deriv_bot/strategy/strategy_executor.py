"""
Module for executing trading strategies based on ML predictions
"""
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class StrategyExecutor:
    def __init__(self, predictor, risk_manager, order_executor):
        self.predictor = predictor
        self.risk_manager = risk_manager
        self.order_executor = order_executor
        
        # Strategy parameters
        self.min_prediction_threshold = 0.02  # 2% minimum predicted move
        self.position_hold_time = 60  # seconds
        
    async def execute_strategy(self, market_data, symbol, stake_amount):
        """
        Execute trading strategy based on predictions
        
        Args:
            market_data: Processed market data sequence
            symbol: Trading symbol
            stake_amount: Base stake amount
        """
        try:
            # Get prediction
            prediction = self.predictor.predict(market_data)
            
            if prediction is None:
                logger.warning("No prediction available")
                return None
                
            # Calculate prediction strength
            prediction_pct = abs(prediction - market_data[-1][-1]) / market_data[-1][-1]
            
            # Check if prediction meets minimum threshold
            if prediction_pct < self.min_prediction_threshold:
                logger.info(f"Prediction strength {prediction_pct:.2%} below threshold")
                return None
                
            # Determine trade direction
            contract_type = 'CALL' if prediction > market_data[-1][-1] else 'PUT'
            
            # Validate trade with risk manager
            if not self.risk_manager.validate_trade(symbol, stake_amount, prediction):
                logger.warning("Trade failed risk validation")
                return None
                
            # Execute order
            order_result = await self.order_executor.place_order(
                symbol,
                contract_type,
                stake_amount,
                self.position_hold_time
            )
            
            if order_result:
                logger.info(f"Strategy executed: {contract_type} order placed")
                return order_result
            else:
                logger.warning("Order execution failed")
                return None
                
        except Exception as e:
            logger.error(f"Error executing strategy: {str(e)}")
            return None
            
    def update_strategy_parameters(self, market_conditions):
        """
        Update strategy parameters based on market conditions
        
        Args:
            market_conditions: Dictionary containing market metrics
        """
        try:
            # Adjust prediction threshold based on volatility
            if 'volatility' in market_conditions:
                self.min_prediction_threshold = max(
                    0.02,  # minimum 2%
                    min(0.05, market_conditions['volatility'] * 0.5)  # maximum 5%
                )
                
            # Adjust position hold time based on trend strength
            if 'trend_strength' in market_conditions:
                self.position_hold_time = max(
                    30,  # minimum 30 seconds
                    min(120, int(60 * market_conditions['trend_strength']))  # maximum 120 seconds
                )
                
            logger.info("Strategy parameters updated")
            
        except Exception as e:
            logger.error(f"Error updating strategy parameters: {str(e)}")
