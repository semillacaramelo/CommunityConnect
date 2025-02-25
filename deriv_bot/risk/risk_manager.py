"""
Module for managing trading risks
"""
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class RiskManager:
    def __init__(self, max_position_size=100, max_daily_loss=50):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.daily_loss = 0
        
    def validate_trade(self, symbol, amount, prediction):
        """
        Validate if trade meets risk parameters
        
        Args:
            symbol: Trading symbol
            amount: Trade amount
            prediction: Predicted price movement
        """
        try:
            if amount > self.max_position_size:
                logger.warning(f"Trade amount {amount} exceeds maximum position size")
                return False
                
            if self.daily_loss + amount > self.max_daily_loss:
                logger.warning("Maximum daily loss limit would be exceeded")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error in risk validation: {str(e)}")
            return False
    
    def update_daily_loss(self, loss_amount):
        """Update daily loss tracker"""
        self.daily_loss += loss_amount
        logger.info(f"Updated daily loss: {self.daily_loss}")
