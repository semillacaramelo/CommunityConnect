"""
Module for training the LSTM model
"""
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class ModelTrainer:
    def __init__(self, input_shape):
        self.model = self._build_model(input_shape)
        
    def _build_model(self, input_shape):
        """
        Build LSTM model architecture
        
        Args:
            input_shape: Shape of input data (sequence_length, features)
        """
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def train(self, X, y, validation_split=0.2, epochs=50, batch_size=32):
        """
        Train the LSTM model
        
        Args:
            X: Input sequences
            y: Target values
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        try:
            # Split data into train and validation sets
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=validation_split, shuffle=False
            )
            
            # Train the model
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                verbose=1
            )
            
            logger.info("Model training completed")
            return history
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return None
    
    def save_model(self, path):
        """Save the trained model"""
        try:
            self.model.save(path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
