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
        self.max_expected_return = 0.005  # 0.5% max return for Forex
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

            # Get predictions from all models (returns as percentage change)
            predictions = {}
            for name, model in self.models.items():
                pred = model.predict(sequence, verbose=0)
                pred_pct = pred[0][0]  # Already in percentage form (-1 to 1 scale)

                # Validate prediction range
                if abs(pred_pct) > self.max_expected_return:
                    logger.warning(f"Model {name} prediction {pred_pct:.2%} exceeds normal range")
                    return None

                predictions[name] = pred_pct

            # Calculate ensemble prediction
            pred_array = np.array(list(predictions.values()))
            ensemble_pred = np.mean(pred_array)

            # Calculate prediction confidence based on model agreement
            pred_std = np.std(pred_array)
            max_expected_std = self.max_expected_return * 0.1  # 10% of max return
            agreement_score = 1.0 - min(pred_std / max_expected_std, 1.0)

            # Calculate confidence based on prediction magnitude
            magnitude_score = 1.0 - (abs(ensemble_pred) / self.max_expected_return)

            # Combined confidence score
            confidence = 0.7 * agreement_score + 0.3 * magnitude_score

            # Return prediction only if confidence meets threshold
            if confidence >= confidence_threshold:
                result = {
                    'prediction': ensemble_pred,
                    'confidence': confidence,
                    'model_predictions': predictions
                }
                logger.info(f"Prediction made - Value: {ensemble_pred:.2%}, Confidence: {confidence:.2f}")
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
                'confidence_score': None,
                'prediction_magnitude': None
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
            metrics['prediction_magnitude'] = abs(np.mean(pred_array))

            # Calculate confidence components
            pred_std = np.std(pred_array)
            max_expected_std = self.max_expected_return * 0.1
            agreement_score = 1.0 - min(pred_std / max_expected_std, 1.0)
            magnitude_score = 1.0 - (metrics['prediction_magnitude'] / self.max_expected_return)

            metrics['confidence_score'] = 0.7 * agreement_score + 0.3 * magnitude_score

            return metrics

        except Exception as e:
            logger.error(f"Error calculating prediction metrics: {str(e)}")
            return None