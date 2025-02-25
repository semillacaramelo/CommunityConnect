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
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.return_scaler = MinMaxScaler(feature_range=(-1, 1))
        self.max_expected_return = 0.005  # 0.5% max expected return for Forex

    def prepare_data(self, df, sequence_length=30):
        """
        Prepare data for LSTM model using percentage returns

        Args:
            df: DataFrame with OHLCV data
            sequence_length: Number of time steps for LSTM input
        """
        try:
            if df is None or df.empty:
                logger.error("Input DataFrame is None or empty")
                return None, None, None

            logger.info(f"Preparing data with shape: {df.shape}")

            # Calculate percentage returns for prediction target
            df['returns'] = df['close'].pct_change()

            # Clip returns to realistic range for Forex
            df['returns'] = df['returns'].clip(-self.max_expected_return, self.max_expected_return)
            df.dropna(inplace=True)

            # Log initial statistics
            logger.info(f"Price range - Min: {df['close'].min():.5f}, Max: {df['close'].max():.5f}")
            logger.info(f"Returns range - Min: {df['returns'].min():.5f}, Max: {df['returns'].max():.5f}")

            # Calculate technical indicators
            df = self.add_technical_indicators(df)
            if df is None or df.empty:
                logger.error("Failed to calculate technical indicators")
                return None, None, None

            logger.info(f"Data shape after indicators: {df.shape}")

            # Scale returns first (target variable)
            returns_data = df['returns'].values.reshape(-1, 1)
            scaled_returns = self.return_scaler.fit_transform(returns_data)
            logger.info(f"Returns scaling params - Min: {self.return_scaler.data_min_}, Max: {self.return_scaler.data_max_}")

            # Create sequences for LSTM
            X, y = self.create_sequences(df.drop('returns', axis=1), scaled_returns, sequence_length)
            if X is None or y is None:
                logger.error("Failed to create sequences")
                return None, None, None

            logger.info(f"Created sequences - X shape: {X.shape}, y shape: {y.shape}")
            return X, y, self.return_scaler

        except Exception as e:
            logger.error(f"Error in prepare_data: {str(e)}")
            return None, None, None

    def add_technical_indicators(self, df):
        """Add technical indicators to the dataset"""
        try:
            # Moving averages
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Momentum
            df['momentum'] = df['close'].pct_change(periods=10)

            # Volatility
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()

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

    def create_sequences(self, data, returns, sequence_length):
        """Create input sequences and target returns for LSTM model"""
        try:
            if len(data) <= sequence_length:
                logger.error(f"Insufficient data: {len(data)} samples, need at least {sequence_length + 1}")
                return None, None

            logger.info(f"Creating sequences from data shape {data.shape} with length {sequence_length}")

            X = []
            y = []

            for i in range(len(data) - sequence_length):
                sequence = data.iloc[i:(i + sequence_length)].values
                X.append(sequence)
                y.append(returns[i + sequence_length])

            X = np.array(X)
            y = np.array(y)

            # Log sequence statistics
            logger.info(f"Sequence stats - X shape: {X.shape}, y shape: {y.shape}")
            logger.info(f"Target returns range - Min: {y.min():.5f}, Max: {y.max():.5f}")

            return X, y

        except Exception as e:
            logger.error(f"Error creating sequences: {str(e)}")
            return None, None

    def inverse_transform_returns(self, scaled_returns):
        """Convert scaled returns back to percentage returns"""
        try:
            return self.return_scaler.inverse_transform(scaled_returns.reshape(-1, 1))
        except Exception as e:
            logger.error(f"Error in inverse transform: {str(e)}")
            return None