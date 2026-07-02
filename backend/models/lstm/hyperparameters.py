"""
LSTM HYPERPARAMETERS

Optimal hyperparameters for LSTM stock price prediction.
These values are tuned for best performance based on research and experimentation.
"""

# Model Architecture - IMPROVED CONFIGURATION
LSTM_HYPERPARAMETERS = {
    # ========== DATA PARAMETERS ==========
    'sequence_length': 120,  # IMPROVED: Look back 6 months (better long-term patterns)
    'features': [
        # Price and volume
        'close', 'volume', 'returns',
        # Moving averages
        'sma_5', 'sma_20', 'sma_50',
        # Technical indicators
        'rsi', 'macd', 'bb_upper', 'bb_lower', 'roc', 'atr',
        # IMPROVED: Volatility features
        'volatility_7d', 'volatility_30d', 'volatility_ratio',
        # IMPROVED: Momentum features
        'momentum_5d', 'momentum_20d',
        # IMPROVED: Volume patterns
        'volume_ratio', 'volume_trend',
        # IMPROVED: Price position
        'price_position', 'trend_strength',
        # IMPROVED: Gap features
        'gap',
        # IMPROVED: Autocorrelation
        'return_lag_1', 'return_lag_2', 'return_lag_3',
        # IMPROVED: Relative strength
        'price_to_sma20', 'price_to_sma50'
    ],
    'target_column': 'close',
    
    # ========== MODEL ARCHITECTURE ==========
    'lstm_units': [128, 64],  # IMPROVED: Larger capacity for more features
    'dropout_rate': 0.3,      # IMPROVED: Higher dropout for better regularization
    'dense_units': [32, 16],  # Units in dense layers
    'activation': 'relu',     # Activation function for dense layers
    'use_bidirectional': True,  # IMPROVED: Bidirectional LSTM for better context
    
    # ========== TRAINING PARAMETERS ==========
    'epochs': 100,            # Maximum training epochs
    'batch_size': 32,         # Batch size for training
    'learning_rate': 0.0008,  # IMPROVED: Slightly lower for stability
    'loss': 'huber',          # Loss function (robust to outliers)
    'optimizer': 'adamw',     # IMPROVED: AdamW for better generalization
    'weight_decay': 0.02,     # IMPROVED: More L2 regularization
    
    # ========== DATA SPLIT ==========
    'train_split': 0.7,       # 70% for training
    'val_split': 0.2,         # 20% for validation
    # Test split is automatic: 1 - train - val = 0.1 (10%)
    
    # ========== EARLY STOPPING ==========
    'early_stopping': {
        'monitor': 'val_loss',
        'patience': 15,       # Stop if no improvement for 15 epochs
        'restore_best_weights': True,
        'min_delta': 0.0001   # Minimum change to qualify as improvement
    },
    
    # ========== LEARNING RATE SCHEDULER ==========
    'reduce_lr': {
        'monitor': 'val_loss',
        'factor': 0.5,        # Reduce LR by half
        'patience': 5,        # Reduce after 5 epochs without improvement
        'min_lr': 1e-7,       # Minimum learning rate
        'verbose': 1
    },
    
    # ========== MODEL CHECKPOINTING ==========
    'checkpoint': {
        'monitor': 'val_loss',
        'save_best_only': True,
        'save_weights_only': False,
        'verbose': 1
    },
    
    # ========== VALIDATION ==========
    'validation': {
        'shuffle': False,     # Don't shuffle time series data
        'verbose': 1          # Show training progress
    }
}


# Alternative configurations for different scenarios
LSTM_CONFIGS = {
    # Fast training for testing
    'quick_test': {
        **LSTM_HYPERPARAMETERS,
        'epochs': 20,
        'sequence_length': 30,
        'lstm_units': [50, 25],
    },
    
    # High accuracy configuration - IMPROVED
    'high_accuracy': {
        **LSTM_HYPERPARAMETERS,
        'epochs': 150,
        'sequence_length': 180,  # 9 months lookback
        'lstm_units': [256, 128, 64],  # Deeper network
        'batch_size': 16,
        'learning_rate': 0.0005,
        'dropout_rate': 0.4,  # Higher regularization
        'use_bidirectional': True,
    },
    
    # Simple model (fewer features)
    'simple': {
        **LSTM_HYPERPARAMETERS,
        'features': ['close'],
        'lstm_units': [50],
        'dense_units': [16],
    },
    
    # Production model (balanced)
    'production': LSTM_HYPERPARAMETERS
}


def get_hyperparameters(config_name: str = 'production') -> dict:
    """
    Get hyperparameters for a specific configuration.
    
    Args:
        config_name: One of 'quick_test', 'high_accuracy', 'simple', 'production'
        
    Returns:
        Dictionary of hyperparameters
    """
    if config_name not in LSTM_CONFIGS:
        raise ValueError(
            f"Unknown config '{config_name}'. "
            f"Available: {list(LSTM_CONFIGS.keys())}"
        )
    
    return LSTM_CONFIGS[config_name].copy()


# Explanation of key hyperparameters
HYPERPARAMETER_GUIDE = """
LSTM HYPERPARAMETER GUIDE
=========================

sequence_length (60):
- How many previous days to consider
- Too short: Misses long-term patterns
- Too long: Overfits, slower training
- Sweet spot: 60-90 days

lstm_units ([100, 50]):
- Number of neurons in each LSTM layer
- More units = more capacity but risk of overfitting
- Decreasing units helps with feature abstraction
- Typical: 50-200 units per layer

dropout_rate (0.2):
- Randomly drops 20% of connections during training
- Prevents overfitting
- Too high: Underfit
- Too low: Overfit
- Typical: 0.2-0.3

batch_size (32):
- Number of samples processed before updating weights
- Larger: Faster but less precise
- Smaller: Slower but more precise
- Typical: 16-64

learning_rate (0.001):
- How big of steps optimizer takes
- Too high: Overshoots minimum, unstable
- Too low: Slow convergence
- Typical: 0.0001-0.001

early_stopping patience (15):
- Stop training if no improvement for N epochs
- Prevents wasting time and overfitting
- Typical: 10-20 epochs

reduce_lr patience (5):
- Reduce learning rate if no improvement
- Helps fine-tune when stuck
- Typical: 3-7 epochs
"""
