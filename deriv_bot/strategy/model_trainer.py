"""
Model Training Module

Location: deriv_bot/strategy/model_trainer.py

Purpose:
Handles the training of machine learning models for price prediction.
Implements model architecture, training loops, and validation.

Dependencies:
- numpy: Numerical computing library
- scikit-learn: Machine learning library
- tensorflow: Deep learning framework
- deriv_bot.monitor.logger: Logging functionality

Interactions:
- Input: Processed market data for training
- Output: Trained ML models
- Relations: Used by main loop for model updates

Author: Trading Bot Team
Last modified: 2024-02-26
"""
import numpy as np
import glob
import pickle
import os
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Concatenate
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
from deriv_bot.monitor.logger import setup_logger

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

    # Custom callback for saving best model without problematic options parameter
    class BestModelCheckpoint(tf.keras.callbacks.Callback):
        def __init__(self, filepath, monitor='val_loss', verbose=0):
            super().__init__()
            self.filepath = filepath
            self.monitor = monitor
            self.verbose = verbose
            self.best = float('inf')

        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            current = logs.get(self.monitor)
            if current is not None and current < self.best:
                if self.verbose > 0:
                    print(f'\nEpoch {epoch+1}: {self.monitor} improved from {self.best:.5f} to {current:.5f}, saving model to {self.filepath}')
                self.best = current
                # Use simple save without options parameter
                self.model.save(self.filepath)

    def train(self, X, y, validation_split=0.2, epochs=None, batch_size=32, model_type=None):
        """
        Train the model with the given data

        Args:
            X: Input sequences
            y: Target values
            validation_split: Fraction of data to use for validation
            epochs: Number of training epochs (uses default_epochs if None)
            batch_size: Batch size for training
            model_type: Optional model type identifier for saving

        Returns:
            History object from model training or None if training failed
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

            # Create models directory if it doesn't exist
            os.makedirs('models', exist_ok=True)

            # Create model name with type if provided
            model_file = 'best_model'
            if model_type:
                model_file = f'best_model_{model_type}'

            # Save checkpoint path using .keras format
            checkpoint_path = os.path.join('models', f'{model_file}.keras')

            # Custom callbacks for better training - Using custom checkpoint to avoid options parameter
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True,
                    verbose=1
                ),
                self.BestModelCheckpoint(
                    filepath=checkpoint_path,
                    monitor='val_loss',
                    verbose=1
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001,
                    verbose=1
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

            logger.info(f"Model training completed for {model_type or 'default'} model")
            return history

        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return None

    def save_model(self, path, scaler=None):
        """
        Save model to the specified path using native Keras format, along with metadata

        Args:
            path: Path where to save the model
            scaler: Optional scaler to save with the model for later denormalization

        Returns:
            Boolean indicating success or failure
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # Always use .keras extension for new models
            if not path.endswith('.keras'):
                if path.endswith('.h5'):
                    path = path[:-3] + '.keras'
                else:
                    path = f"{path}.keras"

            # Save model in native Keras format - no additional parameters
            self.model.save(path)
            logger.info(f"Model saved to {path} in native Keras format")

            # Save metadata including scaler if provided
            if scaler is not None:
                metadata_path = path.replace('.keras', '_metadata.pkl')
                metadata = {'scaler': scaler}
                with open(metadata_path, 'wb') as f:
                    pickle.dump(metadata, f)
                logger.info(f"Model metadata with scaler saved to {metadata_path}")

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

        Returns:
            Loss score or None if evaluation failed
        """
        try:
            score = self.model.evaluate(X_test, y_test, verbose=0)
            logger.info(f"Model test loss: {score:.4f}")
            return score
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None

    def save_models(self, model_path, scaler=None):
        """
        Save trained model (for backward compatibility)

        Args:
            model_path: Path where to save the model
            scaler: Optional scaler to save with the model

        Returns:
            Boolean indicating success or failure
        """
        return self.save_model(model_path, scaler)