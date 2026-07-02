"""
TRANSFORMER MODEL ARCHITECTURE

Builds the Transformer model for stock price prediction.

TODO: Implement Transformer architecture:
- Multi-head attention layers
- Positional encoding
- Feed-forward networks
- Layer normalization
- Dropout for regularization

Reference: "Attention is All You Need" (Vaswani et al., 2017)
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import Tuple


def build_transformer_model(
    sequence_length: int,
    num_features: int,
    d_model: int,
    num_heads: int,
    num_layers: int,
    dff: int,
    dropout_rate: float
) -> keras.Model:
    """
    Build Transformer model architecture.
    
    Args:
        sequence_length: Length of input sequence
        num_features: Number of input features
        d_model: Dimension of model (embedding dimension)
        num_heads: Number of attention heads
        num_layers: Number of transformer blocks
        dff: Dimension of feed-forward network
        dropout_rate: Dropout rate for regularization
        
    Returns:
        Compiled Keras model
        
    TODO: Implement Transformer architecture:
    
    1. Input Layer
       - Shape: (sequence_length, num_features)
    
    2. Positional Encoding
       - Add position information to embeddings
    
    3. Transformer Blocks (repeat num_layers times):
       - Multi-head attention
       - Add & Norm
       - Feed-forward network
       - Add & Norm
       - Dropout
    
    4. Global Average Pooling
       - Aggregate sequence information
    
    5. Dense Layers
       - Dense(64, activation='relu')
       - Dropout
       - Dense(32, activation='relu')
       - Dropout
    
    6. Output Layer
       - Dense(1) - predicted price
    
    7. Compile with:
       - Optimizer: Adam
       - Loss: Huber (robust to outliers)
       - Metrics: ['mae', 'mse']
    """
    pass


class TransformerBlock(layers.Layer):
    """
    Transformer block with multi-head attention and feed-forward network.
    
    TODO: Implement this custom layer:
    - Multi-head attention mechanism
    - Layer normalization
    - Feed-forward network
    - Residual connections
    """
    
    def __init__(self, d_model: int, num_heads: int, dff: int, dropout_rate: float = 0.1):
        """
        Initialize Transformer block.
        
        Args:
            d_model: Dimension of model
            num_heads: Number of attention heads
            dff: Dimension of feed-forward network
            dropout_rate: Dropout rate
        """
        super(TransformerBlock, self).__init__()
        # TODO: Initialize layers
        pass
    
    def call(self, inputs, training=False):
        """
        Forward pass through transformer block.
        
        Args:
            inputs: Input tensor
            training: Whether in training mode
            
        Returns:
            Output tensor
        """
        # TODO: Implement forward pass
        pass


class PositionalEncoding(layers.Layer):
    """
    Positional encoding layer to add position information.
    
    TODO: Implement positional encoding:
    - Use sine and cosine functions
    - Add to input embeddings
    """
    
    def __init__(self, sequence_length: int, d_model: int):
        """
        Initialize positional encoding.
        
        Args:
            sequence_length: Length of sequences
            d_model: Model dimension
        """
        super(PositionalEncoding, self).__init__()
        # TODO: Initialize positional encoding
        pass
    
    def call(self, inputs):
        """
        Add positional encoding to inputs.
        
        Args:
            inputs: Input tensor
            
        Returns:
            Input + positional encoding
        """
        # TODO: Implement positional encoding
        pass
