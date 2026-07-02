"""
LSTM DATA MODULE

Handles data loading from database and preprocessing for LSTM model.
- Fetches historical stock data from PostgreSQL
- Adds technical indicators
- Normalizes features
- Creates sequences for time series prediction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
from typing import Tuple, List
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

from database.db import SessionLocal
from database.db_models import Stock, StockPrice


def get_data_from_db(symbol: str, min_days: int = 400) -> pd.DataFrame:
    """
    Fetch historical stock data from database.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        min_days: Minimum days of data required
        
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    db = SessionLocal()
    
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found in database")
        
        # Get price data
        prices = db.query(StockPrice)\
            .filter(StockPrice.stock_id == stock.id)\
            .order_by(StockPrice.date)\
            .all()
        
        if len(prices) < min_days:
            raise ValueError(
                f"Insufficient data for {symbol}: {len(prices)} days "
                f"(need at least {min_days})"
            )
        
        # Convert to DataFrame
        data = []
        for price in prices:
            data.append({
                'date': price.date,
                'open': float(price.open),
                'high': float(price.high),
                'low': float(price.low),
                'close': float(price.close),
                'volume': float(price.volume)
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('date')
        
        return df
        
    finally:
        db.close()


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators as features.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with additional technical indicator columns
    """
    df = df.copy()
    
    # ========== BASIC TECHNICAL INDICATORS ==========
    # Simple Moving Averages
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Exponential Moving Averages
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    
    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    
    # Price rate of change
    df['roc'] = df['close'].pct_change(periods=10) * 100
    
    # Volume rate of change
    df['volume_roc'] = df['volume'].pct_change(periods=5) * 100
    
    # Average True Range (ATR)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    # ========== ADVANCED FEATURES (IMPROVED PREDICTIONS) ==========
    # 1. VOLATILITY FEATURES (critical for risk assessment)
    df['returns'] = df['close'].pct_change()
    df['volatility_7d'] = df['returns'].rolling(7).std()
    df['volatility_30d'] = df['returns'].rolling(30).std()
    df['volatility_ratio'] = df['volatility_7d'] / (df['volatility_30d'] + 1e-10)
    
    # 2. MOMENTUM FEATURES (trend strength)
    df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
    df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
    df['momentum_60d'] = df['close'] / df['close'].shift(60) - 1
    
    # 3. VOLUME PATTERNS (institutional activity)
    df['volume_sma_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / (df['volume_sma_20'] + 1e-10)
    df['volume_trend'] = df['volume'].rolling(20).apply(lambda x: 1 if x[-1] > x[0] else -1, raw=True)
    
    # 4. PRICE POSITION (where are we in the range?)
    rolling_high = df['high'].rolling(20).max()
    rolling_low = df['low'].rolling(20).min()
    df['price_position'] = (df['close'] - rolling_low) / (rolling_high - rolling_low + 1e-10)
    
    # 5. GAP FEATURES (overnight gaps matter!)
    df['gap'] = (df['open'] - df['close'].shift(1)) / (df['close'].shift(1) + 1e-10)
    df['gap_filled'] = ((df['close'] > df['open']) & (df['gap'] < 0)).astype(int)
    
    # 6. TREND STRENGTH
    df['trend_strength'] = (df['close'] - df['sma_50']) / (df['close'] + 1e-10)
    df['sma_cross'] = ((df['sma_5'] > df['sma_20']).astype(int))
    
    # 7. AUTOCORRELATION FEATURES (does yesterday predict today?)
    for lag in [1, 2, 3, 5, 10]:
        df[f'return_lag_{lag}'] = df['returns'].shift(lag)
    
    # 8. PRICE ACCELERATION (rate of change of momentum)
    df['acceleration'] = df['returns'].diff()
    
    # 9. RELATIVE STRENGTH vs MOVING AVERAGES
    df['price_to_sma20'] = df['close'] / (df['sma_20'] + 1e-10)
    df['price_to_sma50'] = df['close'] / (df['sma_50'] + 1e-10)
    
    # 10. SUPPORT/RESISTANCE LEVELS
    df['dist_to_high_20d'] = (rolling_high - df['close']) / (df['close'] + 1e-10)
    df['dist_to_low_20d'] = (df['close'] - rolling_low) / (df['close'] + 1e-10)
    
    # Remove NaN values
    df = df.dropna()
    
    return df


def preprocess_data(
    df: pd.DataFrame,
    features: List[str],
    target_column: str = 'close',
    sequence_length: int = 60,
    train_split: float = 0.7,
    val_split: float = 0.2
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Preprocess data for LSTM training.
    
    Args:
        df: DataFrame with stock data
        features: List of feature columns to use
        target_column: Column to predict
        sequence_length: Number of time steps to look back
        train_split: Fraction for training (0.7 = 70%)
        val_split: Fraction for validation (0.2 = 20%)
        
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test, scalers
    """
    # Validate features
    for feature in features:
        if feature not in df.columns:
            raise ValueError(f"Feature '{feature}' not found in DataFrame")
    
    # Scale features
    scalers = {}
    scaled_data = pd.DataFrame()
    
    for feature in features:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data[feature] = scaler.fit_transform(
            df[feature].values.reshape(-1, 1)
        ).flatten()
        scalers[feature] = scaler
    
    # Create sequences
    X, y = [], []
    data_array = scaled_data.values
    
    for i in range(sequence_length, len(data_array)):
        X.append(data_array[i - sequence_length:i])
        
        # Target is the next day's closing price
        target_idx = features.index(target_column)
        y.append(data_array[i, target_idx])
    
    X, y = np.array(X), np.array(y)
    
    # Train/validation/test split (70/20/10)
    train_idx = int(len(X) * train_split)
    val_idx = int(len(X) * (train_split + val_split))
    
    X_train = X[:train_idx]
    X_val = X[train_idx:val_idx]
    X_test = X[val_idx:]
    
    y_train = y[:train_idx]
    y_val = y[train_idx:val_idx]
    y_test = y[val_idx:]
    
    return X_train, X_val, X_test, y_train, y_val, y_test, scalers


def get_data_for_training(
    symbol: str,
    features: List[str] = None,
    sequence_length: int = 60,
    add_indicators: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Complete data pipeline: fetch from DB, add indicators, preprocess.
    
    Args:
        symbol: Stock symbol
        features: List of features to use (None = default features)
        sequence_length: Number of days to look back
        add_indicators: Whether to add technical indicators
        
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test, scalers
    """
    # Default features (IMPROVED with new advanced features)
    if features is None:
        features = [
            # Price and volume
            'close', 'volume', 'returns',
            # Moving averages
            'sma_5', 'sma_20', 'sma_50',
            # Technical indicators
            'rsi', 'macd', 'bb_upper', 'bb_lower', 'roc', 'atr',
            # Volatility (NEW)
            'volatility_7d', 'volatility_30d', 'volatility_ratio',
            # Momentum (NEW)
            'momentum_5d', 'momentum_20d',
            # Volume patterns (NEW)
            'volume_ratio', 'volume_trend',
            # Price position (NEW)
            'price_position', 'trend_strength',
            # Gap features (NEW)
            'gap',
            # Autocorrelation (NEW)
            'return_lag_1', 'return_lag_2', 'return_lag_3',
            # Relative strength (NEW)
            'price_to_sma20', 'price_to_sma50'
        ]
    
    # Fetch data
    print(f"📊 Fetching data for {symbol}...")
    df = get_data_from_db(symbol)
    print(f"   ✓ Loaded {len(df)} days")
    
    # Add technical indicators
    if add_indicators:
        print(f"📈 Adding technical indicators...")
        df = add_technical_indicators(df)
        print(f"   ✓ Final dataset: {len(df)} days")
    
    # Preprocess
    print(f"🔧 Preprocessing data...")
    X_train, X_val, X_test, y_train, y_val, y_test, scalers = preprocess_data(
        df, features, sequence_length=sequence_length
    )
    
    print(f"   ✓ Training: {len(X_train)} samples (70%)")
    print(f"   ✓ Validation: {len(X_val)} samples (20%)")
    print(f"   ✓ Test: {len(X_test)} samples (10%)")
    
    return X_train, X_val, X_test, y_train, y_val, y_test, scalers
