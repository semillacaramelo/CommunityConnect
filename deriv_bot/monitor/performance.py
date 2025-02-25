"""
Module for tracking trading performance metrics
"""
import pandas as pd
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class PerformanceTracker:
    def __init__(self):
        self.trades = []
        self.wins = 0
        self.losses = 0
        self.total_profit = 0

    def add_trade(self, trade_data):
        """
        Record a completed trade

        Args:
            trade_data: Dictionary containing trade details
        """
        try:
            # Calculate profit based on entry and exit prices
            entry_price = float(trade_data['entry_price'])
            exit_price = float(trade_data['exit_price'])
            amount = float(trade_data['amount'])

            # Calculate profit based on trade type
            if trade_data['type'] == 'CALL':
                profit = (exit_price - entry_price) * amount
            else:  # PUT
                profit = (entry_price - exit_price) * amount

            # Add profit to trade data
            trade_data['profit'] = profit
            self.trades.append(trade_data)

            if profit > 0:
                self.wins += 1
            else:
                self.losses += 1

            self.total_profit += profit

            logger.info(f"Trade recorded: {trade_data}")

        except Exception as e:
            logger.error(f"Error recording trade: {str(e)}")

    def get_statistics(self):
        """Calculate and return performance statistics"""
        try:
            total_trades = self.wins + self.losses
            win_rate = (self.wins / total_trades * 100) if total_trades > 0 else 0

            stats = {
                'total_trades': total_trades,
                'wins': self.wins,
                'losses': self.losses,
                'win_rate': win_rate,
                'total_profit': self.total_profit
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return None

    def export_history(self, filename='trade_history.csv'):
        """Export trade history to CSV file"""
        try:
            if not self.trades:
                logger.warning("No trades to export")
                return

            df = pd.DataFrame(self.trades)
            df.to_csv(filename, index=False)
            logger.info(f"Trade history exported to {filename}")

        except Exception as e:
            logger.error(f"Error exporting trade history: {str(e)}")