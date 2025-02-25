"""
Module for executing trading orders
"""
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class OrderExecutor:
    def __init__(self, connector):
        self.connector = connector
        
    async def place_order(self, symbol, contract_type, amount, duration):
        """
        Place a new trading order
        
        Args:
            symbol: Trading symbol
            contract_type: Type of contract ('CALL' or 'PUT')
            amount: Trade amount
            duration: Contract duration in seconds
        """
        try:
            request = {
                "buy": 1,
                "parameters": {
                    "amount": amount,
                    "basis": "stake",
                    "contract_type": contract_type,
                    "currency": "USD",
                    "duration": duration,
                    "duration_unit": "s",
                    "symbol": symbol
                }
            }
            
            response = await self.connector.send_request(request)
            
            if "error" in response:
                logger.error(f"Order placement failed: {response['error']['message']}")
                return None
                
            logger.info(f"Order placed successfully: {response['buy']}")
            return response['buy']
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    async def close_position(self, contract_id):
        """
        Close an open position
        
        Args:
            contract_id: ID of the contract to close
        """
        try:
            request = {
                "sell": contract_id
            }
            
            response = await self.connector.send_request(request)
            
            if "error" in response:
                logger.error(f"Position closure failed: {response['error']['message']}")
                return False
                
            logger.info(f"Position closed successfully: {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False
