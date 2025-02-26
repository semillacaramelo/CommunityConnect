"""
Module for training the LSTM model
"""
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Concatenate
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from deriv_bot.monitor.logger import setup_logger
import os

logger = setup_logger(__name__)

class ModelTrainer:
    def __init__(self, input_shape, epochs=50):
        """
        Initialize model trainer with input shape and optional training parameters

        Args:
            input_shape: Shape of input data (sequence_length, features)
            epochs: Number of training epochs (default: 50)
        """
        self.input_shape = input_shape
        self.default_epochs = epochs if epochs is not None else 50  # Ensure default_epochs is never None
        self.model = self._build_lstm_model(units=128)  # Default to medium model
        logger.info(f"Model trainer initialized with input shape {input_shape} and default epochs {self.default_epochs}")

    def _build_lstm_model(self, units, dropout_rate=0.2):
        """
        Build a single LSTM model

        Args:
            units: Number of LSTM units
            dropout_rate: Dropout rate for regularization
        """
        model = Sequential([
            LSTM(units=units, return_sequences=True, input_shape=self.input_shape),
            Dropout(dropout_rate),
            LSTM(units=units // 2, return_sequences=False),
            Dropout(dropout_rate),
            Dense(units=32, activation='relu'),
            Dropout(dropout_rate),
            Dense(units=1)
        ])

        model.compile(optimizer='adam', loss='huber')  # Huber loss for robustness
        return model

    def _build_ensemble_models(self):
        """Build ensemble of LSTM models with different architectures"""
        models = {
            'short_term': self._build_lstm_model(units=64),  # For short-term patterns
            'medium_term': self._build_lstm_model(units=128),  # For medium-term trends
            'long_term': self._build_lstm_model(units=256)  # For long-term trends
        }
        return models

    def train(self, X, y, validation_split=0.2, epochs=None, batch_size=32):
        """
        Train the model with the given data

        Args:
            X: Input sequences
            y: Target values
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs (uses default_epochs if None)
            batch_size: Batch size for training
        """
        try:
            # Use instance default epochs if none provided
            if epochs is None:
                epochs = self.default_epochs

            logger.info(f"Training model for {epochs} epochs with batch size {batch_size}")

            # Split data into train and validation sets
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=validation_split, shuffle=False
            )

            # Callbacks for better training
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                ModelCheckpoint(
                    'best_model.h5',
                    monitor='val_loss',
                    save_best_only=True
                )
            ]

            # Train the model
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )

            logger.info("Model training completed")
            return history

        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return None

    def save_model(self, path):
        """Save model to the specified path"""
        try:
            self.model.save(path, save_format='h5')
            logger.info(f"Model saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False

    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test data

        Args:
            X_test: Test input sequences
            y_test: Test target values
        """
        try:
            score = self.model.evaluate(X_test, y_test, verbose=0)
            logger.info(f"Model test loss: {score:.4f}")
            return score
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None

    def save_models(self, model_path):
        """Save trained model"""
        try:
            # Ensure directory exists
            directory = os.path.dirname(model_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Save model
            self.model.save(model_path)
            logger.info(f"Model saved to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False