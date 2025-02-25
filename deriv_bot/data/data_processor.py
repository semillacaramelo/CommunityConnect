"""
Module for processing and preparing market data for ML model
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class DataProcessor:
    def __init__(self):
        self.scaler = MinMaxScaler()
        
    def prepare_data(self, df, sequence_length=60):
        """
        Prepare data for LSTM model
        
        Args:
            df: DataFrame with OHLCV data
            sequence_length: Number of time steps for LSTM input
        """
        try:
            # Calculate technical indicators
            df = self.add_technical_indicators(df)
            
            # Scale the features
            scaled_data = self.scaler.fit_transform(df)
            
            # Create sequences for LSTM
            X, y = self.create_sequences(scaled_data, sequence_length)
            
            return X, y, self.scaler
            
        except Exception as e:
            logger.error(f"Error in prepare_data: {str(e)}")
            return None, None, None
    
    def add_technical_indicators(self, df):
        """Add basic technical indicators to the dataset"""
        # Calculate moving averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Drop NaN values
        df.dropna(inplace=True)
        
        return df
    
    def create_sequences(self, data, sequence_length):
        """Create input sequences for LSTM model"""
        X = []
        y = []
        
        for i in range(len(data) - sequence_length):
            X.append(data[i:(i + sequence_length)])
            y.append(data[i + sequence_length, 3])  # Predict close price
            
        return np.array(X), np.array(y)
