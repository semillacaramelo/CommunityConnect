"""
Configuration management module
"""
import os
import logging
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
        self.environment = os.getenv('DERIV_BOT_ENV', 'demo').lower()
        logger.info(f"Trading bot initialized in {self.environment.upper()} mode")

    def load_environment(self):
        """Load environment variables"""
        try:
            # Look for .env file in current directory and parent directories
            load_dotenv()

            # For VS Code compatibility, also try to load from workspace root
            workspace_env = os.path.join(os.getcwd(), '.env')
            if os.path.exists(workspace_env):
                load_dotenv(workspace_env)

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
        env = self.environment
        token_key = f"DERIV_API_TOKEN_{env.upper()}"
        token = os.getenv(token_key)

        if not token:
            logger.error(f"No API token found for {env} environment")
            raise ValueError(f"Missing API token for {env} environment. Set {token_key} in .env file")

        return token

    def set_environment(self, environment):
        """
        Switch between demo and real trading environments
        Args:
            environment: 'demo' or 'real'
        Returns:
            bool: True if switch was successful
        """
        environment = environment.lower()
        if environment not in ['demo', 'real']:
            logger.error(f"Invalid environment: {environment}. Must be 'demo' or 'real'")
            return False

        # Before switching to real, verify token exists
        if environment == 'real':
            real_token = os.getenv('DERIV_API_TOKEN_REAL')
            if not real_token:
                logger.error("Cannot switch to REAL mode: Missing DERIV_API_TOKEN_REAL")
                return False

            logger.warning("SWITCHING TO REAL TRADING MODE - ACTUAL FUNDS WILL BE USED!")

            # Add additional safety check for real mode
            if not os.getenv('DERIV_REAL_MODE_CONFIRMED', '').lower() == 'yes':
                logger.error("Real mode requires confirmation. Set DERIV_REAL_MODE_CONFIRMED=yes in .env file.")
                logger.error("This is a safety measure to prevent accidental use of real funds.")
                return False

        # Update environment
        old_env = self.environment
        self.environment = environment
        os.environ['DERIV_BOT_ENV'] = environment
        logger.info(f"Trading environment switched from {old_env.upper()} to {environment.upper()}")
        return True

    def get_environment(self):
        """Get current trading environment"""
        return self.environment

    def is_demo(self):
        """Check if running in demo mode"""
        return self.environment == 'demo'