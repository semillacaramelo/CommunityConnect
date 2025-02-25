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
            df.dropna(inplace=True)

            # Log initial price statistics
            logger.info(f"Price range - Min: {df['close'].min():.5f}, Max: {df['close'].max():.5f}")
            logger.info(f"Returns range - Min: {df['returns'].min():.5f}, Max: {df['returns'].max():.5f}")

            # Calculate technical indicators
            df = self.add_technical_indicators(df)
            if df is None or df.empty:
                logger.error("Failed to calculate technical indicators")
                return None, None, None

            logger.info(f"Data shape after indicators: {df.shape}")

            # Separate features for different scaling approaches
            price_cols = ['open', 'high', 'low', 'close']
            feature_cols = [col for col in df.columns if col not in price_cols + ['returns']]

            # Scale price data
            price_data = df[price_cols].values
            scaled_prices = self.price_scaler.fit_transform(price_data)
            logger.info(f"Price scaling params - Min: {self.price_scaler.data_min_}, Max: {self.price_scaler.data_max_}")

            # Scale technical features
            feature_data = df[feature_cols].values
            scaled_features = self.feature_scaler.fit_transform(feature_data)
            logger.info(f"Feature scaling params - Min: {self.feature_scaler.data_min_}, Max: {self.feature_scaler.data_max_}")

            # Scale returns (target variable)
            returns_data = df['returns'].values.reshape(-1, 1)
            scaled_returns = self.return_scaler.fit_transform(returns_data)
            logger.info(f"Returns scaling params - Min: {self.return_scaler.data_min_}, Max: {self.return_scaler.data_max_}")

            # Combine scaled data
            scaled_data = np.hstack((scaled_prices, scaled_features))
            logger.info(f"Combined scaled data shape: {scaled_data.shape}")

            # Create sequences for LSTM
            X, y = self.create_sequences(scaled_data, scaled_returns, sequence_length)
            if X is None or y is None:
                logger.error("Failed to create sequences")
                return None, None, None

            logger.info(f"Created sequences - X shape: {X.shape}, y shape: {y.shape}")
            return X, y, {'price': self.price_scaler, 'feature': self.feature_scaler, 'return': self.return_scaler}

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

            # Add momentum
            df['momentum'] = df['close'] / df['close'].shift(10) - 1

            # Add volatility
            df['volatility'] = df['close'].rolling(window=20).std()

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
                X.append(data[i:(i + sequence_length)])
                y.append(returns[i + sequence_length])  # Predict next return

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