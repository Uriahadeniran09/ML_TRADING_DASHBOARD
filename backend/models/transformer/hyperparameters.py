"""
TRANSFORMER HYPERPARAMETERS

Optimal hyperparameters for Transformer model training.
These values are based on research and best practices for time series forecasting.

TODO: Adjust these values based on your experiments and results.
"""

TRANSFORMER_HYPERPARAMETERS = {
    # ============================================================================
    # DATA PARAMETERS
    # ============================================================================
    'sequence_length': 60,  # Number of days to look back
    'features': [
        'close',      # Closing price (primary target)
        'volume',     # Trading volume
        'sma_5',      # 5-day simple moving average
        'sma_20',     # 20-day simple moving average
        'rsi',        # Relative Strength Index
        'macd',       # MACD indicator
        'bb_upper',   # Bollinger Band upper
        'bb_lower',   # Bollinger Band lower
        'roc',        # Rate of Change
        'atr'         # Average True Range
    ],
    'target_column': 'close',
    
    # Data split ratios (must sum to 1.0)
    'train_ratio': 0.7,      # 70% for training
    'val_ratio': 0.2,        # 20% for validation
    'test_ratio': 0.1,       # 10% for testing
    
    # ============================================================================
    # MODEL ARCHITECTURE
    # ============================================================================
    'd_model': 128,          # Dimension of model (embedding dimension)
                             # Typical values: 64, 128, 256, 512
                             # Larger = more capacity but slower
    
    'num_heads': 8,          # Number of attention heads
                             # Must divide d_model evenly
                             # Typical values: 4, 8, 16
                             # More heads = captures more patterns
    
    'num_layers': 4,         # Number of transformer blocks
                             # Typical values: 2, 4, 6, 8
                             # More layers = deeper network, better patterns
                             # But risk of overfitting
    
    'dff': 512,              # Dimension of feed-forward network
                             # Typical values: 2-4x d_model
                             # Larger = more capacity
    
    'dropout_rate': 0.2,     # Dropout rate for regularization
                             # Range: 0.1 - 0.3
                             # Higher = more regularization, less overfitting
    
    # ============================================================================
    # TRAINING PARAMETERS
    # ============================================================================
    'epochs': 100,           # Maximum number of training epochs
                             # Early stopping will stop if no improvement
    
    'batch_size': 32,        # Batch size for training
                             # Typical values: 16, 32, 64, 128
                             # Larger = faster but more memory
                             # Smaller = slower but better generalization
    
    'learning_rate': 0.0001, # Initial learning rate
                             # Typical values: 0.001, 0.0001, 0.00001
                             # Transformers often use smaller LR than LSTMs
    
    'warmup_steps': 1000,    # Learning rate warmup steps
                             # Gradual increase in LR at start
                             # Helps stability
    
    # ============================================================================
    # CALLBACKS
    # ============================================================================
    'early_stopping_patience': 15,  # Stop if no improvement for N epochs
    'reduce_lr_patience': 5,        # Reduce LR if no improvement for N epochs
    'reduce_lr_factor': 0.5,        # Multiply LR by this factor
    'min_lr': 1e-7,                 # Minimum learning rate
    
    # ============================================================================
    # MODEL SAVING
    # ============================================================================
    'model_save_dir': 'data/models/transformer',
    'save_best_only': True,          # Only save best model
    'monitor_metric': 'val_loss',    # Metric to monitor for best model
    
    # ============================================================================
    # PREDICTION
    # ============================================================================
    'confidence_threshold': 0.5,     # Minimum confidence for predictions
    'prediction_horizon': 1,         # Days ahead to predict (currently only 1)
    
    # ============================================================================
    # ADVANCED PARAMETERS (Experimental)
    # ============================================================================
    'use_positional_encoding': True,  # Add positional encoding
    'use_layer_normalization': True,  # Use layer normalization
    'use_residual_connections': True, # Use skip connections
    'attention_dropout': 0.1,         # Dropout in attention layer
    
    # Label smoothing (helps with overconfidence)
    'label_smoothing': 0.0,          # 0.0 = no smoothing, 0.1 = 10% smoothing
    
    # Gradient clipping (prevents exploding gradients)
    'clipnorm': 1.0,                 # Clip gradients to this norm
}


# ============================================================================
# HYPERPARAMETER SUGGESTIONS
# ============================================================================
"""
QUICK START CONFIGURATIONS:

1. FAST TRAINING (for testing):
   - epochs: 20
   - batch_size: 64
   - num_layers: 2
   - d_model: 64

2. BALANCED (recommended):
   - epochs: 100
   - batch_size: 32
   - num_layers: 4
   - d_model: 128

3. HIGH PERFORMANCE (if you have time):
   - epochs: 200
   - batch_size: 16
   - num_layers: 6
   - d_model: 256

4. PRODUCTION (best results):
   - epochs: 300
   - batch_size: 32
   - num_layers: 8
   - d_model: 512
   - warmup_steps: 2000
"""


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_hyperparameters():
    """
    Validate that hyperparameters are consistent.
    
    TODO: Implement validation checks:
    - d_model must be divisible by num_heads
    - train_ratio + val_ratio + test_ratio must equal 1.0
    - All rates must be between 0 and 1
    """
    pass


def get_hyperparameters(mode: str = 'balanced') -> dict:
    """
    Get hyperparameters for different modes.
    
    Args:
        mode: 'fast', 'balanced', 'high_performance', or 'production'
        
    Returns:
        Dictionary of hyperparameters
        
    TODO: Implement different configuration modes
    """
    pass
