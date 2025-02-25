"""
Module for creating advanced technical indicators and features for ML model
"""
import numpy as np
import pandas as pd
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class FeatureEngineer:
    def __init__(self):
        pass
        
    def calculate_features(self, df):
        """
        Calculate technical indicators and features
        
        Args:
            df: DataFrame with OHLCV data
        """
        try:
            # Add momentum indicators
            df = self._add_momentum_indicators(df)
            
            # Add volatility indicators
            df = self._add_volatility_indicators(df)
            
            # Add trend indicators
            df = self._add_trend_indicators(df)
            
            # Drop NaN values from calculations
            df.dropna(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating features: {str(e)}")
            return None
    
    def _add_momentum_indicators(self, df):
        """Calculate momentum-based indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Stochastic Oscillator
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['K'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['D'] = df['K'].rolling(window=3).mean()
        
        return df
        
    def _add_volatility_indicators(self, df):
        """Calculate volatility-based indicators"""
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (std * 2)
        
        # Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        return df
        
    def _add_trend_indicators(self, df):
        """Calculate trend-based indicators"""
        # Moving Averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        # Moving Average Convergence/Divergence (MACD)
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Price Rate of Change
        df['ROC'] = df['close'].pct_change(periods=12) * 100
        
        return df

