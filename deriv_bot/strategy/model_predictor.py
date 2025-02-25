"""
Module for making predictions using the trained model
"""
import numpy as np
from tensorflow.keras.models import load_model
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class ModelPredictor:
    def __init__(self, model_path=None):
        self.model = None
        if model_path:
            self.load_model(model_path)
            
    def load_model(self, model_path):
        """Load trained model from file"""
        try:
            self.model = load_model(model_path)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            
    def predict(self, sequence):
        """
        Make price prediction
        
        Args:
            sequence: Input sequence of shape (1, sequence_length, features)
        """
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
                
            prediction = self.model.predict(sequence)
            return prediction[0][0]
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return None
