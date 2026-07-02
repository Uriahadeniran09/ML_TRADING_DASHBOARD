"""
MULTI-HORIZON LSTM PREDICTIONS

Generates predictions for multiple time horizons:
- 1 day ahead
- 1 week ahead (5 trading days)
- 1 month ahead (21 trading days)
- 6 months ahead (126 trading days)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import json

from database.db import SessionLocal
from database.crud import add_lstm_prediction
from .lstmmodel import load_saved_model
from .data import get_data_from_db, add_technical_indicators


# Forecast horizons in trading days
FORECAST_HORIZONS = {
    '1day': 1,
    '1week': 5,
    '1month': 21,
    '6months': 126
}


def predict_multi_step(
    model: object,
    initial_sequence: np.ndarray,
    scalers: dict,
    features: List[str],
    horizon_days: int
) -> List[float]:
    """
    Predict multiple steps ahead using iterative forecasting.
    
    Args:
        model: Trained LSTM model
        initial_sequence: Initial input sequence [sequence_length, num_features]
        scalers: Dictionary of scalers for each feature
        features: List of feature names
        horizon_days: Number of days to predict ahead
        
    Returns:
        List of predicted prices (denormalized)
    """
    predictions = []
    current_sequence = initial_sequence.copy()
    
    for step in range(horizon_days):
        # Reshape for model input: [1, sequence_length, num_features]
        X = current_sequence.reshape(1, current_sequence.shape[0], current_sequence.shape[1])
        
        # Make prediction (normalized)
        pred_normalized = model.predict(X, verbose=0)[0][0]
        
        # Denormalize prediction
        pred_price = scalers['close'].inverse_transform([[pred_normalized]])[0][0]
        predictions.append(float(pred_price))
        
        # Update sequence for next prediction
        # Create new row with predicted values
        new_row = np.zeros((1, len(features)))
        
        for i, feature in enumerate(features):
            if feature == 'close':
                # Use predicted price (already normalized)
                new_row[0, i] = pred_normalized
            else:
                # For other features, use the last known value
                # In a production system, you might want to predict these too
                new_row[0, i] = current_sequence[-1, i]
        
        # Shift sequence: remove first row, add new prediction
        current_sequence = np.vstack([current_sequence[1:], new_row])
    
    return predictions


def calculate_confidence_decay(horizon_days: int, base_confidence: float = 0.9) -> float:
    """
    Calculate confidence score with decay based on forecast horizon.
    Longer forecasts are less certain.
    
    Args:
        horizon_days: Number of days ahead
        base_confidence: Base confidence score (0-1)
        
    Returns:
        Adjusted confidence score
    """
    # Exponential decay: confidence = base_confidence * exp(-decay_rate * horizon)
    decay_rate = 0.01  # Adjust this to control how fast confidence decays
    confidence = base_confidence * np.exp(-decay_rate * horizon_days)
    return max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0


def update_multi_horizon_predictions(
    symbol: str,
    model_dir: str = 'data/models/lstm',
    horizons: List[str] = None
) -> Dict[str, bool]:
    """
    Generate predictions for multiple time horizons and save to database.
    
    Args:
        symbol: Stock symbol
        model_dir: Directory where model is saved
        horizons: List of horizon names (e.g., ['1day', '1week', '1month', '6months'])
                  If None, generates all horizons
        
    Returns:
        Dictionary mapping horizons to success status
    """
    if horizons is None:
        horizons = list(FORECAST_HORIZONS.keys())
    
    db = SessionLocal()
    results = {}
    
    try:
        print(f"\n{'='*70}")
        print(f"MULTI-HORIZON PREDICTIONS FOR {symbol}")
        print(f"{'='*70}")
        
        # Load model
        print(f"📊 Loading model...")
        model, scalers, metadata = load_saved_model(symbol, model_dir)
        
        # Get recent data
        print(f"📈 Fetching recent data...")
        df = get_data_from_db(symbol, min_days=200)
        df = add_technical_indicators(df)
        
        # Get model parameters
        features = metadata.get('features', ['close'])
        sequence_length = metadata.get('sequence_length', 60)
        
        # Prepare initial sequence
        recent_data = df.tail(sequence_length + 10).copy()
        
        # Scale features
        scaled_sequence = []
        for feature in features:
            if feature not in recent_data.columns:
                raise ValueError(f"Feature '{feature}' not found")
            
            scaler = scalers.get(feature)
            if scaler is None:
                raise ValueError(f"No scaler for '{feature}'")
            
            scaled_values = scaler.transform(
                recent_data[feature].values.reshape(-1, 1)
            )
            scaled_sequence.append(scaled_values)
        
        # Create initial input sequence
        initial_sequence = np.concatenate(scaled_sequence, axis=1)
        initial_sequence = initial_sequence[-sequence_length:]
        
        # Current price
        current_price = float(df['close'].iloc[-1])
        prediction_date = date.today()
        
        # Get validation metrics
        base_confidence = metadata.get('confidence_score', 0.85)
        validation_mse = metadata.get('best_val_loss')
        validation_r2 = metadata.get('validation_r2')
        
        print(f"\n📍 Current Price: ${current_price:.2f}")
        print(f"📅 Prediction Date: {prediction_date}")
        print(f"\nGenerating predictions for {len(horizons)} horizons...\n")
        
        # Generate predictions for each horizon
        for horizon_name in horizons:
            if horizon_name not in FORECAST_HORIZONS:
                print(f"⚠️  Unknown horizon: {horizon_name}, skipping...")
                results[horizon_name] = False
                continue
            
            horizon_days = FORECAST_HORIZONS[horizon_name]
            
            try:
                print(f"  🔮 {horizon_name} ({horizon_days} days)...")
                
                # Generate predictions
                predictions = predict_multi_step(
                    model, 
                    initial_sequence, 
                    scalers, 
                    features, 
                    horizon_days
                )
                
                # Get final prediction (last day in horizon)
                predicted_price = predictions[-1]
                predicted_change = predicted_price - current_price
                predicted_change_pct = (predicted_change / current_price) * 100
                
                # Calculate target date (accounting for weekends)
                # Approximate: horizon_days * 1.4 to account for weekends
                calendar_days = int(horizon_days * 1.4)
                target_date = prediction_date + timedelta(days=calendar_days)
                
                # Adjust confidence based on horizon
                confidence_score = calculate_confidence_decay(horizon_days, base_confidence)
                
                # Save to database
                add_lstm_prediction(
                    db=db,
                    symbol=symbol,
                    prediction_date=prediction_date,
                    target_date=target_date,
                    predicted_price=predicted_price,
                    horizon_days=horizon_days,
                    predicted_change=predicted_change,
                    predicted_change_pct=predicted_change_pct,
                    model_version=metadata.get('model_version', 'v1.0'),
                    sequence_length=sequence_length,
                    features_used=features,
                    confidence_score=confidence_score,
                    validation_mse=validation_mse,
                    validation_r2=validation_r2
                )
                
                print(f"     ✅ ${predicted_price:.2f} ({predicted_change_pct:+.2f}%) - Confidence: {confidence_score:.2%}")
                results[horizon_name] = True
                
            except Exception as e:
                print(f"     ❌ Failed: {str(e)}")
                results[horizon_name] = False
        
        print(f"\n{'='*70}")
        successful = sum(1 for v in results.values() if v)
        print(f"✅ Generated {successful}/{len(horizons)} predictions successfully")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ Error generating predictions for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        for horizon_name in horizons:
            results[horizon_name] = False
        
    finally:
        db.close()
    
    return results


def batch_update_multi_horizon(
    symbols: List[str] = None,
    model_dir: str = 'data/models/lstm',
    horizons: List[str] = None
) -> Dict[str, Dict[str, bool]]:
    """
    Update multi-horizon predictions for multiple stocks.
    
    Args:
        symbols: List of symbols (None = all available models)
        model_dir: Directory where models are saved
        horizons: List of horizon names
        
    Returns:
        Nested dictionary: {symbol: {horizon: success}}
    """
    from .lstmmodel import list_saved_models
    
    # Get all models if no symbols specified
    if symbols is None:
        symbols = list_saved_models(model_dir)
    
    if not symbols:
        print("⚠️  No models found")
        return {}
    
    print(f"\n{'='*70}")
    print(f"BATCH MULTI-HORIZON PREDICTION UPDATE")
    print(f"{'='*70}")
    print(f"Stocks: {len(symbols)}")
    print(f"Horizons: {horizons or list(FORECAST_HORIZONS.keys())}")
    print(f"{'='*70}\n")
    
    all_results = {}
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing {symbol}")
        print("-" * 70)
        
        results = update_multi_horizon_predictions(symbol, model_dir, horizons)
        all_results[symbol] = results
    
    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    
    total_predictions = sum(sum(1 for v in r.values() if v) for r in all_results.values())
    total_attempted = sum(len(r) for r in all_results.values())
    
    print(f"✅ Total successful predictions: {total_predictions}/{total_attempted}")
    
    # Summary by horizon
    if horizons is None:
        horizons = list(FORECAST_HORIZONS.keys())
    
    print(f"\n📊 By Horizon:")
    for horizon in horizons:
        successful = sum(1 for r in all_results.values() if r.get(horizon, False))
        print(f"   {horizon}: {successful}/{len(symbols)}")
    
    print(f"{'='*70}\n")
    
    return all_results


def get_prediction_summary(symbol: str) -> dict:
    """
    Get summary of all multi-horizon predictions for a symbol.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with prediction summary
    """
    from database.db_models import LSTMPrediction, Stock
    
    db = SessionLocal()
    
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            return {'error': f'Stock {symbol} not found'}
        
        # Get latest predictions for each horizon
        predictions = {}
        
        for horizon_name, horizon_days in FORECAST_HORIZONS.items():
            pred = db.query(LSTMPrediction).filter(
                LSTMPrediction.stock_id == stock.id,
                LSTMPrediction.horizon_days == horizon_days
            ).order_by(LSTMPrediction.prediction_date.desc()).first()
            
            if pred:
                predictions[horizon_name] = {
                    'predicted_price': pred.predicted_price,
                    'predicted_change_pct': pred.predicted_change_pct,
                    'target_date': pred.target_date.isoformat(),
                    'confidence': pred.confidence_score,
                    'prediction_date': pred.prediction_date.isoformat()
                }
        
        return {
            'symbol': symbol,
            'predictions': predictions
        }
        
    finally:
        db.close()


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate multi-horizon LSTM predictions')
    parser.add_argument('--symbol', type=str, help='Stock symbol')
    parser.add_argument('--all', action='store_true', help='Process all stocks')
    parser.add_argument('--horizons', nargs='+', choices=list(FORECAST_HORIZONS.keys()),
                       help='Specific horizons to generate')
    
    args = parser.parse_args()
    
    if args.all:
        batch_update_multi_horizon(horizons=args.horizons)
    elif args.symbol:
        update_multi_horizon_predictions(args.symbol, horizons=args.horizons)
    else:
        print("Please specify --symbol SYMBOL or --all")
