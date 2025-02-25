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
            logger.info(f"Placing {contract_type} order - Symbol: {symbol}, Amount: {amount}, Duration: {duration}s")

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
            logger.debug(f"Full order response: {response}")
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
            logger.info(f"Closing position {contract_id}")

            request = {
                "sell": contract_id
            }

            response = await self.connector.send_request(request)

            if "error" in response:
                logger.error(f"Position closure failed: {response['error']['message']}")
                return False

            logger.info(f"Position closed successfully: {contract_id}")
            logger.debug(f"Close position response: {response}")
            return True

        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False

    async def check_position_status(self, contract_id):
        """
        Check the status of an open position

        Args:
            contract_id: ID of the contract to check
        """
        try:
            request = {
                "proposal_open_contract": 1,
                "contract_id": contract_id
            }

            response = await self.connector.send_request(request)

            if "error" in response:
                logger.error(f"Status check failed: {response['error']['message']}")
                return None

            logger.debug(f"Position status: {response}")
            return response.get('proposal_open_contract')

        except Exception as e:
            logger.error(f"Error checking position status: {str(e)}")
            return None