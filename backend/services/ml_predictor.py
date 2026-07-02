"""
ML PREDICTOR SERVICE - Stock price predictions using LSTM

This service provides stock price predictions using trained LSTM models.
- Loads pre-trained LSTM models for each stock
- Makes predictions for next day, week, or custom horizon
- Returns prediction with confidence metrics
- Caches predictions to reduce compute

Functions:
- get_prediction(symbol, days_ahead): Get price prediction
- get_prediction_with_metrics(symbol): Get prediction + confidence
- batch_predict(symbols): Predict multiple stocks
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from backend.database.db_models import Stock, StockPrice
from models.lstm_model import StockLSTM
from services.cache import cache_prediction, get_cached_prediction


# Model directory
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'models'
)

# Cache for loaded models
_model_cache: Dict[str, StockLSTM] = {}


def load_model(symbol: str, force_reload: bool = False) -> Optional[StockLSTM]:
    """
    Load LSTM model for a stock.
    
    Args:
        symbol: Stock symbol
        force_reload: Force reload from disk
        
    Returns:
        Loaded LSTM model or None if not found
    """
    # Check cache
    if not force_reload and symbol in _model_cache:
        return _model_cache[symbol]
    
    # Load from disk
    model_path = os.path.join(MODEL_DIR, symbol)
    
    if not os.path.exists(model_path):
        return None
    
    try:
        model = StockLSTM()
        model.load(model_path, 'lstm_model')
        _model_cache[symbol] = model
        return model
    except Exception as e:
        print(f"Error loading model for {symbol}: {e}")
        return None


def fetch_recent_data(
    symbol: str,
    days: int = 100,
    db: SessionLocal = None
) -> pd.DataFrame:
    """
    Fetch recent stock data from database.
    
    Args:
        symbol: Stock symbol
        days: Number of recent days to fetch
        db: Database session (creates new if None)
        
    Returns:
        DataFrame with recent stock data
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        # Get recent prices
        prices = db.query(StockPrice)\
            .filter(StockPrice.stock_id == stock.id)\
            .order_by(StockPrice.date.desc())\
            .limit(days)\
            .all()
        
        if not prices:
            raise ValueError(f"No price data for {symbol}")
        
        # Convert to DataFrame
        data = []
        for price in reversed(prices):  # Reverse to chronological order
            data.append({
                'date': price.date,
                'open': float(price.open),
                'high': float(price.high),
                'low': float(price.low),
                'close': float(price.close),
                'volume': float(price.volume)
            })
        
        df = pd.DataFrame(data)
        
        # Add technical indicators if needed
        df = _add_technical_indicators(df)
        
        return df
        
    finally:
        if close_db:
            db.close()


def _add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators matching training features."""
    df = df.copy()
    
    # Simple Moving Averages
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    
    # Bollinger Bands
    bb_middle = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = bb_middle + (bb_std * 2)
    df['bb_lower'] = bb_middle - (bb_std * 2)
    
    # ROC
    df['roc'] = df['close'].pct_change(periods=10) * 100
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    return df


def get_prediction(symbol: str, days_ahead: int = 1) -> Optional[float]:
    """
    Get price prediction for a stock.
    
    Args:
        symbol: Stock symbol
        days_ahead: Days ahead to predict (currently only supports 1)
        
    Returns:
        Predicted price or None if model not available
    """
    if days_ahead != 1:
        # TODO: Implement multi-day predictions
        raise NotImplementedError("Multi-day predictions not yet implemented")
    
    # Check cache
    cached = get_cached_prediction(symbol, days_ahead)
    if cached:
        return cached['predicted_price']
    
    # Load model
    model = load_model(symbol)
    if not model:
        return None
    
    # Get recent data
    try:
        df = fetch_recent_data(symbol, days=100)
        prediction = model.predict_next_day(df)
        
        # Cache result
        cache_prediction(symbol, prediction, days_ahead)
        
        return prediction
    except Exception as e:
        print(f"Error predicting {symbol}: {e}")
        return None


def get_prediction_with_metrics(symbol: str) -> Optional[Dict]:
    """
    Get prediction with confidence metrics.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with prediction and metrics
    """
    # Load model
    model = load_model(symbol)
    if not model:
        return None
    
    try:
        # Get recent data
        df = fetch_recent_data(symbol, days=100)
        
        # Get prediction
        predicted_price = model.predict_next_day(df)
        
        # Get current price
        current_price = df['close'].iloc[-1]
        
        # Calculate metrics
        predicted_change = predicted_price - current_price
        predicted_change_pct = (predicted_change / current_price) * 100
        
        # Get model metadata
        metadata = model.metadata
        
        result = {
            'symbol': symbol,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_change': float(predicted_change),
            'predicted_change_pct': float(predicted_change_pct),
            'prediction_date': (datetime.now() + timedelta(days=1)).date().isoformat(),
            'model_metadata': {
                'last_trained': metadata.get('last_trained'),
                'training_samples': metadata.get('training_samples'),
                'best_val_loss': metadata.get('best_val_loss'),
                'features_used': metadata.get('features_used', [])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache result
        cache_prediction(symbol, predicted_price, days_ahead=1)
        
        return result
        
    except Exception as e:
        print(f"Error getting prediction for {symbol}: {e}")
        return None


def batch_predict(symbols: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Get predictions for multiple stocks.
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dictionary mapping symbols to predictions
    """
    results = {}
    
    for symbol in symbols:
        results[symbol] = get_prediction_with_metrics(symbol)
    
    return results


def list_available_models() -> List[str]:
    """
    List stocks with trained models.
    
    Returns:
        List of stock symbols with available models
    """
    if not os.path.exists(MODEL_DIR):
        return []
    
    models = []
    for item in os.listdir(MODEL_DIR):
        model_path = os.path.join(MODEL_DIR, item)
        if os.path.isdir(model_path):
            # Check if model files exist
            if os.path.exists(os.path.join(model_path, 'lstm_model.keras')):
                models.append(item)
    
    return sorted(models)
