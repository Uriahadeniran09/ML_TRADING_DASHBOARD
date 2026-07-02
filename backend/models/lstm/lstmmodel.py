"""
LSTM MODEL PERSISTENCE

Handles saving and loading of trained LSTM models.
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import json
import numpy as np
from tensorflow.keras.models import load_model as keras_load_model
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from typing import Tuple, Dict, Optional


def save_best_model(
    model: object,
    scalers: dict,
    symbol: str,
    metadata: dict,
    save_dir: str = 'data/models/lstm'
) -> str:
    """
    Save the best trained model with scalers and metadata.
    
    Args:
        model: Trained Keras model
        scalers: Dictionary of feature scalers
        symbol: Stock symbol
        metadata: Training metadata (hyperparameters, metrics, etc.)
        save_dir: Directory to save model
        
    Returns:
        Path where model was saved
    """
    # Create directory for this stock
    model_dir = os.path.join(save_dir, symbol)
    os.makedirs(model_dir, exist_ok=True)
    
    # Save Keras model
    model_path = os.path.join(model_dir, 'lstm_model.keras')
    model.save(model_path)
    
    # Save scalers
    scalers_data = {}
    for feature, scaler in scalers.items():
        scalers_data[feature] = {
            'min': scaler.min_.tolist(),
            'scale': scaler.scale_.tolist(),
            'data_min': scaler.data_min_.tolist(),
            'data_max': scaler.data_max_.tolist()
        }
    
    scalers_path = os.path.join(model_dir, 'scalers.json')
    with open(scalers_path, 'w') as f:
        json.dump(scalers_data, f, indent=2)
    
    # Add timestamps to metadata
    metadata['saved_at'] = datetime.now().isoformat()
    metadata['model_path'] = model_path
    metadata['symbol'] = symbol
    
    # Save metadata
    metadata_path = os.path.join(model_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Model saved successfully!")
    print(f"   Location: {model_dir}")
    print(f"   Files:")
    print(f"     - lstm_model.keras (model)")
    print(f"     - scalers.json (normalization)")
    print(f"     - metadata.json (training info)\n")
    
    return model_dir


def load_saved_model(
    symbol: str,
    load_dir: str = 'data/models/lstm'
) -> Tuple[object, Dict[str, MinMaxScaler], dict]:
    """
    Load a saved LSTM model with its scalers and metadata.
    
    Args:
        symbol: Stock symbol
        load_dir: Directory where models are saved
        
    Returns:
        (model, scalers, metadata)
    """
    model_dir = os.path.join(load_dir, symbol)
    
    if not os.path.exists(model_dir):
        raise FileNotFoundError(f"No saved model found for {symbol} in {load_dir}")
    
    # Load Keras model
    model_path = os.path.join(model_dir, 'lstm_model.keras')
    model = keras_load_model(model_path)
    
    # Load scalers
    scalers_path = os.path.join(model_dir, 'scalers.json')
    with open(scalers_path, 'r') as f:
        scalers_data = json.load(f)
    
    scalers = {}
    for feature, scaler_dict in scalers_data.items():
        scaler = MinMaxScaler()
        scaler.min_ = np.array(scaler_dict['min'])
        scaler.scale_ = np.array(scaler_dict['scale'])
        scaler.data_min_ = np.array(scaler_dict['data_min'])
        scaler.data_max_ = np.array(scaler_dict['data_max'])
        scaler.n_features_in_ = 1
        scaler.n_samples_seen_ = 1
        scalers[feature] = scaler
    
    # Load metadata
    metadata_path = os.path.join(model_dir, 'metadata.json')
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Model loaded successfully for {symbol}")
    print(f"   Saved at: {metadata.get('saved_at', 'Unknown')}")
    print(f"   Best val loss: {metadata.get('best_val_loss', 'N/A')}")
    
    return model, scalers, metadata


def list_saved_models(load_dir: str = 'data/models/lstm') -> list:
    """
    List all saved LSTM models.
    
    Args:
        load_dir: Directory where models are saved
        
    Returns:
        List of stock symbols with saved models
    """
    if not os.path.exists(load_dir):
        return []
    
    models = []
    for item in os.listdir(load_dir):
        model_path = os.path.join(load_dir, item)
        if os.path.isdir(model_path):
            # Check if it has the required files
            if os.path.exists(os.path.join(model_path, 'lstm_model.keras')):
                models.append(item)
    
    return sorted(models)


def get_model_metadata(
    symbol: str,
    load_dir: str = 'data/models/lstm'
) -> Optional[dict]:
    """
    Get metadata for a saved model without loading the model itself.
    
    Args:
        symbol: Stock symbol
        load_dir: Directory where models are saved
        
    Returns:
        Metadata dictionary or None if not found
    """
    metadata_path = os.path.join(load_dir, symbol, 'metadata.json')
    
    if not os.path.exists(metadata_path):
        return None
    
    with open(metadata_path, 'r') as f:
        return json.load(f)


def delete_model(
    symbol: str,
    load_dir: str = 'data/models/lstm'
) -> bool:
    """
    Delete a saved model and all its files.
    
    Args:
        symbol: Stock symbol
        load_dir: Directory where models are saved
        
    Returns:
        True if deleted successfully, False otherwise
    """
    import shutil
    
    model_dir = os.path.join(load_dir, symbol)
    
    if not os.path.exists(model_dir):
        print(f"❌ No model found for {symbol}")
        return False
    
    try:
        shutil.rmtree(model_dir)
        print(f"✅ Model for {symbol} deleted successfully")
        return True
    except Exception as e:
        print(f"❌ Error deleting model for {symbol}: {e}")
        return False
