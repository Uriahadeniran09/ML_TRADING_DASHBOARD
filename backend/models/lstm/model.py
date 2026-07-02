"""
LSTM MODEL ARCHITECTURE

Builds the LSTM neural network for stock price prediction.
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional
from tensorflow.keras.optimizers import AdamW, Adam
from typing import Tuple, List


def build_lstm_model(
    input_shape: Tuple[int, int],
    lstm_units: List[int] = [128, 64],
    dropout_rate: float = 0.3,
    dense_units: List[int] = [32, 16],
    activation: str = 'relu',
    learning_rate: float = 0.0008,
    loss: str = 'huber',
    optimizer_type: str = 'adamw',
    weight_decay: float = 0.02,
    use_bidirectional: bool = True
) -> Sequential:
    """
    Build LSTM model architecture.
    
    Args:
        input_shape: (sequence_length, num_features)
        lstm_units: List of units for each LSTM layer
        dropout_rate: Dropout rate for regularization
        dense_units: List of units for dense layers
        activation: Activation function for dense layers
        learning_rate: Learning rate for optimizer
        loss: Loss function ('mse', 'mae', 'huber')
        optimizer_type: Optimizer type ('adamw', 'adam')
        weight_decay: Weight decay for AdamW optimizer (L2 regularization)
        use_bidirectional: Use bidirectional LSTM (looks forward AND backward)
        
    Returns:
        Compiled Keras Sequential model
    """
    model = Sequential(name='StockLSTM_Improved')
    
    # ========== LSTM LAYERS (IMPROVED: Bidirectional option) ==========
    for i, units in enumerate(lstm_units):
        # Return sequences for all but last LSTM layer
        return_sequences = (i < len(lstm_units) - 1)
        
        if i == 0:
            # First LSTM layer - needs input_shape
            lstm_layer = LSTM(
                units=units,
                return_sequences=return_sequences,
                input_shape=input_shape,
                name=f'lstm_{i+1}'
            )
            
            # Wrap in Bidirectional if enabled (IMPROVED)
            if use_bidirectional:
                model.add(Bidirectional(lstm_layer, name=f'bidirectional_lstm_{i+1}'))
            else:
                model.add(lstm_layer)
        else:
            # Subsequent LSTM layers
            lstm_layer = LSTM(
                units=units,
                return_sequences=return_sequences,
                name=f'lstm_{i+1}'
            )
            
            # Wrap in Bidirectional if enabled (IMPROVED)
            if use_bidirectional:
                model.add(Bidirectional(lstm_layer, name=f'bidirectional_lstm_{i+1}'))
            else:
                model.add(lstm_layer)
        
        # Add dropout and batch normalization
        model.add(Dropout(dropout_rate, name=f'dropout_{i+1}'))
        model.add(BatchNormalization(name=f'batch_norm_{i+1}'))
    
    # ========== DENSE LAYERS ==========
    for i, units in enumerate(dense_units):
        model.add(Dense(
            units,
            activation=activation,
            name=f'dense_{i+1}'
        ))
        
        # Add dropout (reduced rate for dense layers)
        if i < len(dense_units) - 1:
            model.add(Dropout(dropout_rate / 2, name=f'dropout_dense_{i+1}'))
    
    # ========== OUTPUT LAYER ==========
    model.add(Dense(1, name='output'))
    
    # ========== COMPILE MODEL ==========
    # Use AdamW for better generalization with decoupled weight decay
    if optimizer_type.lower() == 'adamw':
        optimizer = AdamW(
            learning_rate=learning_rate,
            weight_decay=weight_decay
        )
    elif optimizer_type.lower() == 'adam':
        optimizer = Adam(learning_rate=learning_rate)
    else:
        raise ValueError(f"Unsupported optimizer: {optimizer_type}. Use 'adamw' or 'adam'")
    
    model.compile(
        optimizer=optimizer,
        loss=loss,
        metrics=['mae', 'mse']
    )
    
    return model


def print_model_summary(model: Sequential):
    """
    Print model architecture summary.
    
    Args:
        model: Keras model
    """
    print("\n" + "="*70)
    print("MODEL ARCHITECTURE")
    print("="*70)
    model.summary()
    print("="*70 + "\n")


def get_model_info(model: Sequential) -> dict:
    """
    Get model information.
    
    Args:
        model: Keras model
        
    Returns:
        Dictionary with model information
    """
    return {
        'total_params': model.count_params(),
        'trainable_params': sum([tf.keras.backend.count_params(w) 
                                 for w in model.trainable_weights]),
        'non_trainable_params': sum([tf.keras.backend.count_params(w) 
                                     for w in model.non_trainable_weights]),
        'num_layers': len(model.layers),
        'input_shape': model.input_shape,
        'output_shape': model.output_shape
    }
