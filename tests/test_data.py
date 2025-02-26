"""
Data Module Unit Tests

Location: tests/test_data.py

Purpose:
Unit tests for data processing and handling components, including
technical indicators and data preparation for ML models.

Dependencies:
- unittest: Testing framework
- pandas: Data manipulation
- numpy: Numerical operations
- deriv_bot.data: Modules being tested

Interactions:
- Input: Test data and configurations
- Output: Test results and assertions
- Relations: Validates data processing functionality

Author: Trading Bot Team
Last modified: 2024-02-26
"""
import unittest
import pandas as pd
import numpy as np
from deriv_bot.data.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        self.sample_data = pd.DataFrame({
            'open': np.random.random(100),
            'high': np.random.random(100),
            'low': np.random.random(100),
            'close': np.random.random(100),
            'volume': np.random.random(100)
        }, index=dates)
        
    def test_add_technical_indicators(self):
        """Test technical indicator calculation"""
        processed_df = self.processor.add_technical_indicators(self.sample_data)
        
        self.assertIn('SMA_20', processed_df.columns)
        self.assertIn('SMA_50', processed_df.columns)
        self.assertIn('RSI', processed_df.columns)
        
    def test_prepare_data(self):
        """Test data preparation for ML model"""
        X, y, scaler = self.processor.prepare_data(self.sample_data, sequence_length=10)
        
        self.assertIsNotNone(X)
        self.assertIsNotNone(y)
        self.assertIsNotNone(scaler)
        self.assertEqual(len(X.shape), 3)  # (samples, sequence_length, features)
        
    def test_create_sequences(self):
        """Test sequence creation"""
        data = np.random.random((100, 5))
        X, y = self.processor.create_sequences(data, sequence_length=10)
        
        self.assertEqual(X.shape[1], 10)  # sequence length
        self.assertEqual(len(y.shape), 1)  # 1D array of targets

if __name__ == '__main__':
    unittest.main()
