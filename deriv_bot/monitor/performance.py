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
            self.trades.append(trade_data)
            
            if trade_data['profit'] > 0:
                self.wins += 1
            else:
                self.losses += 1
                
            self.total_profit += trade_data['profit']
            
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
            df = pd.DataFrame(self.trades)
            df.to_csv(filename, index=False)
            logger.info(f"Trade history exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting trade history: {str(e)}")
