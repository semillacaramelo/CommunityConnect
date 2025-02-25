"""
Unit tests for strategy modules
"""
import unittest
import numpy as np
from deriv_bot.strategy.model_trainer import ModelTrainer
from deriv_bot.strategy.model_predictor import ModelPredictor

class TestStrategy(unittest.TestCase):
    def setUp(self):
        self.input_shape = (60, 8)  # (sequence_length, features)
        self.trainer = ModelTrainer(self.input_shape)
        
    def test_model_build(self):
        """Test model architecture creation"""
        model = self.trainer.model
        
        self.assertIsNotNone(model)
        self.assertEqual(len(model.layers), 5)  # Check number of layers
        
    def test_model_training(self):
        """Test model training process"""
        # Create dummy data
        X = np.random.random((100, 60, 8))
        y = np.random.random(100)
        
        history = self.trainer.train(
            X, y,
            validation_split=0.2,
            epochs=2,
            batch_size=32
        )
        
        self.assertIsNotNone(history)
        self.assertIn('loss', history.history)
        self.assertIn('val_loss', history.history)
        
    def test_model_prediction(self):
        """Test model prediction"""
        predictor = ModelPredictor()
        predictor.model = self.trainer.model
        
        # Create dummy sequence
        sequence = np.random.random((1, 60, 8))
        prediction = predictor.predict(sequence)
        
        self.assertIsNotNone(prediction)
        self.assertTrue(isinstance(prediction, float))

if __name__ == '__main__':
    unittest.main()
