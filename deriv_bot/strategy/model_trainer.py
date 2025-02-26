"""
Module for training the LSTM model
"""
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Concatenate
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class ModelTrainer:
    def __init__(self, input_shape):
        self.input_shape = input_shape
        self.models = self._build_ensemble_models()

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

    def train(self, X, y, validation_split=0.2, epochs=50, batch_size=32):
        """
        Train the ensemble of LSTM models

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

            # Train each model in the ensemble
            history = {}
            for name, model in self.models.items():
                logger.info(f"Training {name} model...")

                history[name] = model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=epochs,
                    batch_size=batch_size,
                    callbacks=callbacks,
                    verbose=1
                )

                logger.info(f"{name} model training completed")

            logger.info("Ensemble training completed")
            return history

        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return None

    def save_models(self, directory='models'):
        """Save all models in the ensemble"""
        try:
            for name, model in self.models.items():
                path = f"{directory}/{name}_model.keras"
                model.save(path, save_format='keras')
                logger.info(f"Model {name} saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
            return False

    def evaluate_models(self, X_test, y_test):
        """
        Evaluate each model in the ensemble

        Args:
            X_test: Test input sequences
            y_test: Test target values
        """
        try:
            results = {}
            for name, model in self.models.items():
                score = model.evaluate(X_test, y_test, verbose=0)
                results[name] = score
                logger.info(f"{name} model test loss: {score:.4f}")
            return results
        except Exception as e:
            logger.error(f"Error evaluating models: {str(e)}")
            return None