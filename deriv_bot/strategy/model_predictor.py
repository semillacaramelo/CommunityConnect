"""
Module for making predictions using the trained model
"""
import numpy as np
from tensorflow.keras.models import load_model
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class ModelPredictor:
    def __init__(self, model_path=None):
        self.models = {}
        if model_path:
            self.load_models(model_path)

    def load_models(self, base_path):
        """Load all models in the ensemble"""
        try:
            model_types = ['short_term', 'medium_term', 'long_term']
            for model_type in model_types:
                path = f"{base_path}/{model_type}_model.h5"
                self.models[model_type] = load_model(path)
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")

    def predict(self, sequence, confidence_threshold=0.6):
        """
        Make ensemble prediction with confidence score

        Args:
            sequence: Input sequence of shape (1, sequence_length, features)
            confidence_threshold: Minimum confidence required for valid prediction
        """
        try:
            if not self.models:
                raise ValueError("Models not loaded")

            # Get predictions from all models
            predictions = {}
            for name, model in self.models.items():
                pred = model.predict(sequence, verbose=0)
                predictions[name] = pred[0][0]

            # Calculate ensemble prediction and confidence
            pred_array = np.array(list(predictions.values()))
            ensemble_pred = np.mean(pred_array)

            # Calculate prediction confidence
            pred_std = np.std(pred_array)
            pred_range = np.max(pred_array) - np.min(pred_array)

            # Normalize confidence score (0 to 1)
            confidence = 1.0 - min(pred_std / abs(ensemble_pred), pred_range / abs(ensemble_pred))

            # Return prediction only if confidence meets threshold
            if confidence >= confidence_threshold:
                result = {
                    'prediction': ensemble_pred,
                    'confidence': confidence,
                    'model_predictions': predictions
                }
                logger.info(f"Prediction made with confidence: {confidence:.2f}")
                return result
            else:
                logger.warning(f"Low confidence prediction ({confidence:.2f}) rejected")
                return None

        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return None

    def get_prediction_metrics(self, sequence):
        """
        Get detailed prediction metrics from each model

        Args:
            sequence: Input sequence
        """
        try:
            metrics = {
                'individual_predictions': {},
                'prediction_spread': None,
                'confidence_score': None
            }

            # Get individual model predictions
            predictions = []
            for name, model in self.models.items():
                pred = model.predict(sequence, verbose=0)[0][0]
                metrics['individual_predictions'][name] = pred
                predictions.append(pred)

            # Calculate prediction spread and confidence
            pred_array = np.array(predictions)
            metrics['prediction_spread'] = np.max(pred_array) - np.min(pred_array)
            metrics['confidence_score'] = 1.0 - (np.std(pred_array) / abs(np.mean(pred_array)))

            return metrics

        except Exception as e:
            logger.error(f"Error calculating prediction metrics: {str(e)}")
            return None