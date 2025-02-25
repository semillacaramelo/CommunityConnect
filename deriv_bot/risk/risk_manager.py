"""
Module for managing trading risks with different profiles for DEMO and REAL accounts
"""
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class RiskManager:
    def __init__(self, is_demo=True, max_position_size=100, max_daily_loss=50):
        self.is_demo = is_demo
        # Demo account uses more aggressive parameters
        if is_demo:
            self.max_position_size = max_position_size * 2  # Double the position size for demo
            self.max_daily_loss = max_daily_loss * 3  # Triple the daily loss limit for demo
            self.stop_loss_pct = 0.05  # 5% stop loss for demo
            self.risk_multiplier = 2.0  # More aggressive risk profile
        else:
            self.max_position_size = max_position_size
            self.max_daily_loss = max_daily_loss
            self.stop_loss_pct = 0.01  # 1% stop loss for real
            self.risk_multiplier = 1.0  # Normal risk profile

        self.daily_loss = 0
        self.initial_balance = None
        logger.info(f"RiskManager initialized with {'DEMO' if is_demo else 'REAL'} profile")
        logger.info(f"Parameters: max_position={self.max_position_size}, "
                   f"max_daily_loss={self.max_daily_loss}, "
                   f"stop_loss={self.stop_loss_pct}%, "
                   f"risk_multiplier={self.risk_multiplier}")

    def validate_trade(self, symbol, amount, prediction):
        """
        Validate if trade meets risk parameters

        Args:
            symbol: Trading symbol
            amount: Trade amount
            prediction: Predicted price movement
        """
        try:
            # More permissive validation for demo account
            if self.is_demo:
                adjusted_amount = amount * self.risk_multiplier
                if adjusted_amount > self.max_position_size:
                    logger.warning(f"Demo trade amount {adjusted_amount} exceeds maximum position size")
                    return False

                if self.daily_loss + adjusted_amount > self.max_daily_loss:
                    logger.warning("Demo maximum daily loss limit would be exceeded")
                    logger.info(f"Current daily loss: {self.daily_loss}, Limit: {self.max_daily_loss}")
                    self.reset_demo_balance()
                    return True  # Allow trade after reset in demo

                logger.info(f"Demo trade validated - Amount: {adjusted_amount}, "
                          f"Current daily loss: {self.daily_loss}")
                return True
            else:
                # Strict validation for real account
                if amount > self.max_position_size:
                    logger.warning(f"Trade amount {amount} exceeds maximum position size")
                    return False

                if self.daily_loss + amount > self.max_daily_loss:
                    logger.warning("Maximum daily loss limit would be exceeded")
                    return False

                logger.info(f"Real trade validated - Amount: {amount}, "
                          f"Current daily loss: {self.daily_loss}")
                return True

        except Exception as e:
            logger.error(f"Error in risk validation: {str(e)}")
            return False

    def update_daily_loss(self, loss_amount):
        """Update daily loss tracker"""
        previous_loss = self.daily_loss
        self.daily_loss += loss_amount
        logger.info(f"Updated daily loss: {self.daily_loss} (change: {loss_amount:+.2f})")

        # Auto-reset for demo account if loss is too high
        if self.is_demo and self.daily_loss >= self.max_daily_loss:
            logger.warning(f"Demo daily loss ({self.daily_loss}) exceeded limit ({self.max_daily_loss})")
            self.reset_demo_balance()

    def reset_demo_balance(self):
        """Reset demo account balance and loss tracking"""
        if self.is_demo:
            previous_loss = self.daily_loss
            self.daily_loss = 0
            logger.info(f"Demo account reset - Previous loss: {previous_loss}, Balance reset to 0")
            return True
        else:
            logger.warning("Balance reset attempted on real account - operation denied")
            return False

    def get_risk_profile(self):
        """Return current risk profile settings"""
        return {
            'account_type': 'DEMO' if self.is_demo else 'REAL',
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'stop_loss_pct': self.stop_loss_pct,
            'risk_multiplier': self.risk_multiplier,
            'current_daily_loss': self.daily_loss
        }