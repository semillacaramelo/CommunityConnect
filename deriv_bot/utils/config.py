"""
Configuration management module
"""
import os
from dotenv import load_dotenv
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class Config:
    def __init__(self):
        self.load_environment()
        self.trading_config = {
            'symbol': 'frxEURUSD',
            'stake_amount': 10.0,
            'duration': 60,  # seconds
            'max_position_size': 100.0,
            'max_daily_loss': 50.0
        }
        
    def load_environment(self):
        """Load environment variables"""
        try:
            load_dotenv()
            
            required_vars = [
                'DERIV_API_TOKEN_DEMO',
                'DERIV_API_TOKEN_REAL',
                'DERIV_BOT_ENV'
            ]
            
            for var in required_vars:
                if not os.getenv(var):
                    logger.warning(f"Missing environment variable: {var}")
                    
        except Exception as e:
            logger.error(f"Error loading environment variables: {str(e)}")
    
    def get_api_token(self):
        """Get appropriate API token based on environment"""
        env = os.getenv('DERIV_BOT_ENV', 'demo')
        token_key = f"DERIV_API_TOKEN_{env.upper()}"
        return os.getenv(token_key)
