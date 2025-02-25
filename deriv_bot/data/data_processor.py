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

    def prepare_data(self, df, sequence_length=30):  # Changed default from 60 to 30
        """
        Prepare data for LSTM model

        Args:
            df: DataFrame with OHLCV data
            sequence_length: Number of time steps for LSTM input
        """
        try:
            if df is None or df.empty:
                logger.error("Input DataFrame is None or empty")
                return None, None, None

            logger.info(f"Preparing data with shape: {df.shape}")

            # Calculate technical indicators
            df = self.add_technical_indicators(df)
            if df is None or df.empty:
                logger.error("Failed to calculate technical indicators")
                return None, None, None

            logger.info(f"Data shape after indicators: {df.shape}")

            # Extract features for scaling
            features = ['open', 'high', 'low', 'close', 'SMA_20', 'SMA_50', 'RSI']
            feature_data = df[features].values

            # Scale the features
            scaled_data = self.scaler.fit_transform(feature_data)
            logger.info(f"Scaled data shape: {scaled_data.shape}")

            # Create sequences for LSTM
            X, y = self.create_sequences(scaled_data, sequence_length)
            if X is None or y is None:
                logger.error("Failed to create sequences")
                return None, None, None

            logger.info(f"Created sequences - X shape: {X.shape}, y shape: {y.shape}")
            return X, y, self.scaler

        except Exception as e:
            logger.error(f"Error in prepare_data: {str(e)}")
            return None, None, None

    def add_technical_indicators(self, df):
        """Add basic technical indicators to the dataset"""
        try:
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

            if df.empty:
                logger.warning("All data was dropped after calculating indicators")
                return None

            logger.info(f"Indicator calculation complete. Shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return None

    def create_sequences(self, data, sequence_length):
        """Create input sequences for LSTM model"""
        try:
            if len(data) <= sequence_length:
                logger.error(f"Insufficient data: {len(data)} samples, need at least {sequence_length + 1}")
                return None, None

            logger.info(f"Creating sequences from data shape {data.shape} with length {sequence_length}")

            X = []
            y = []

            for i in range(len(data) - sequence_length):
                X.append(data[i:(i + sequence_length)])
                y.append(data[i + sequence_length, 3])  # Predict close price

            X = np.array(X)
            y = np.array(y)

            logger.info(f"Created sequences with shapes - X: {X.shape}, y: {y.shape}")
            return X, y

        except Exception as e:
            logger.error(f"Error creating sequences: {str(e)}")
            return None, None