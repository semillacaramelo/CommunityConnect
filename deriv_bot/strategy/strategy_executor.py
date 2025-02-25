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

        # Updated strategy parameters
        self.min_prediction_threshold = 0.015  # Reduced from 0.02 to 0.015
        self.position_hold_time = 30  # Reduced from 60 to 30 seconds
        self.max_position_size = 0.02  # 2% of account balance
        self.stop_loss_pct = 0.01  # 1% stop loss

    async def execute_strategy(self, market_data, symbol, stake_amount):
        """
        Execute trading strategy based on predictions

        Args:
            market_data: Processed market data sequence
            symbol: Trading symbol
            stake_amount: Base stake amount
        """
        try:
            # Get ensemble prediction with confidence
            prediction_result = self.predictor.predict(market_data, confidence_threshold=0.7)

            if prediction_result is None:
                logger.warning("No prediction available or confidence too low")
                return None

            prediction = prediction_result['prediction']
            confidence = prediction_result['confidence']

            # Calculate prediction strength
            current_price = market_data[-1][-1]
            price_diff = prediction - current_price
            prediction_pct = abs(price_diff / current_price)

            # Check if prediction meets minimum threshold
            if prediction_pct < self.min_prediction_threshold:
                logger.info(f"Prediction strength {prediction_pct:.2%} below threshold")
                return None

            # Determine trade direction
            contract_type = 'CALL' if price_diff > 0 else 'PUT'

            # Adjust position size based on confidence
            adjusted_stake = stake_amount * min(1.0, confidence)
            adjusted_stake = min(adjusted_stake, stake_amount * self.max_position_size)

            # Additional risk validation
            if not self.risk_manager.validate_trade(symbol, adjusted_stake, prediction):
                logger.warning("Trade failed risk validation")
                return None

            # Execute order with stop loss
            order_params = {
                'symbol': symbol,
                'contract_type': contract_type,
                'amount': adjusted_stake,
                'duration': self.position_hold_time,
                'stop_loss_pct': self.stop_loss_pct
            }

            order_result = await self.order_executor.place_order(**order_params)

            if order_result:
                logger.info(f"Strategy executed: {contract_type} order placed with confidence {confidence:.2f}")
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
                    0.01,  # minimum 1%
                    min(0.03, market_conditions['volatility'] * 0.3)  # maximum 3%
                )

            # Adjust position hold time based on trend strength
            if 'trend_strength' in market_conditions:
                self.position_hold_time = max(
                    20,  # minimum 20 seconds
                    min(60, int(30 * market_conditions['trend_strength']))  # maximum 60 seconds
                )

            # Adjust position size based on market regime
            if 'market_regime' in market_conditions:
                regime_risk = market_conditions.get('regime_risk', 1.0)  # Default to normal risk
                self.max_position_size = max(0.01, min(0.03, 0.02 * (1 / regime_risk)))

            logger.info("Strategy parameters updated")

        except Exception as e:
            logger.error(f"Error updating strategy parameters: {str(e)}")