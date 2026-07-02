"""
MULTI-HORIZON WITH PREDICTION PATHS

Enhanced version that stores ALL intermediate predictions for graphing.

For a 1-month prediction (21 days), this stores 21 rows:
- Day 1: $183.20
- Day 2: $183.95
- ...
- Day 21: $190.30

This allows the frontend to draw smooth prediction curves.
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
from models.lstm.lstmmodel import load_saved_model
from models.lstm.data import get_data_from_db, add_technical_indicators


# Forecast horizons
FORECAST_HORIZONS = {
    '1day': 1,
    '1week': 5,
    '1month': 21,
    '6months': 126
}


def predict_multi_step_with_path(
    model: object,
    initial_sequence: np.ndarray,
    scalers: dict,
    features: List[str],
    horizon_days: int
) -> List[float]:
    """
    Predict multiple steps ahead, returning ALL intermediate predictions.
    
    Args:
        model: Trained LSTM model
        initial_sequence: Initial input sequence
        scalers: Dictionary of scalers
        features: List of feature names
        horizon_days: Number of days to predict
        
    Returns:
        List of predicted prices for each day [day1, day2, ..., dayN]
    """
    predictions = []
    current_sequence = initial_sequence.copy()
    
    for step in range(horizon_days):
        # Reshape for model
        X = current_sequence.reshape(1, current_sequence.shape[0], current_sequence.shape[1])
        
        # Predict
        pred_normalized = model.predict(X, verbose=0)[0][0]
        
        # Denormalize
        pred_price = scalers['close'].inverse_transform([[pred_normalized]])[0][0]
        predictions.append(float(pred_price))
        
        # Update sequence for next prediction
        new_row = np.zeros((1, len(features)))
        for i, feature in enumerate(features):
            if feature == 'close':
                new_row[0, i] = pred_normalized
            else:
                new_row[0, i] = current_sequence[-1, i]
        
        current_sequence = np.vstack([current_sequence[1:], new_row])
    
    return predictions


def save_prediction_path(
    db,
    stock_id: int,
    prediction_date: date,
    horizon_type: str,
    predictions: List[float],
    base_confidence: float,
    model_version: str
):
    """
    Save all intermediate predictions to lstm_prediction_paths table.
    
    Args:
        db: Database session
        stock_id: Stock ID
        prediction_date: When prediction was made
        horizon_type: '1day', '1week', '1month', or '6months'
        predictions: List of predicted prices [day1, day2, ...]
        base_confidence: Base confidence score
        model_version: Model version
    """
    from database.prediction_paths_model import LSTMPredictionPath
    
    # Delete old predictions for this stock/date/horizon
    db.query(LSTMPredictionPath).filter(
        LSTMPredictionPath.stock_id == stock_id,
        LSTMPredictionPath.prediction_date == prediction_date,
        LSTMPredictionPath.horizon_type == horizon_type
    ).delete()
    
    # Save each day's prediction
    for day_offset, price in enumerate(predictions, start=1):
        # Calculate target date (approximate, accounting for weekends)
        calendar_days = int(day_offset * 1.4)
        target_date = prediction_date + timedelta(days=calendar_days)
        
        # Confidence decays with distance
        confidence = base_confidence * np.exp(-0.01 * day_offset)
        
        path_point = LSTMPredictionPath(
            stock_id=stock_id,
            prediction_date=prediction_date,
            horizon_type=horizon_type,
            day_offset=day_offset,
            target_date=target_date,
            predicted_price=price,
            confidence_score=confidence,
            model_version=model_version
        )
        db.add(path_point)
    
    db.commit()


def update_multi_horizon_with_paths(
    symbol: str,
    model_dir: str = 'data/models/lstm',
    horizons: List[str] = None
) -> Dict[str, bool]:
    """
    Generate multi-horizon predictions AND save all intermediate points for graphing.
    
    Args:
        symbol: Stock symbol
        model_dir: Model directory
        horizons: List of horizon types to generate
        
    Returns:
        Dict mapping horizon to success status
    """
    if horizons is None:
        horizons = list(FORECAST_HORIZONS.keys())
    
    db = SessionLocal()
    results = {}
    
    try:
        print(f"\n{'='*80}")
        print(f"MULTI-HORIZON PREDICTIONS WITH PATHS FOR {symbol}")
        print(f"{'='*80}")
        
        # Load model
        print(f"📊 Loading model...")
        model, scalers, metadata = load_saved_model(symbol, model_dir)
        
        # Get data
        print(f"📈 Fetching recent data...")
        df = get_data_from_db(symbol, min_days=200)
        df = add_technical_indicators(df)
        
        # Get parameters
        features = metadata.get('features', ['close'])
        sequence_length = metadata.get('sequence_length', 60)
        
        # Prepare sequence
        recent_data = df.tail(sequence_length + 10).copy()
        scaled_sequence = []
        
        for feature in features:
            scaler = scalers.get(feature)
            scaled_values = scaler.transform(recent_data[feature].values.reshape(-1, 1))
            scaled_sequence.append(scaled_values)
        
        initial_sequence = np.concatenate(scaled_sequence, axis=1)[-sequence_length:]
        
        # Current info
        current_price = float(df['close'].iloc[-1])
        prediction_date = date.today()
        base_confidence = metadata.get('confidence_score', 0.85)
        model_version = metadata.get('model_version', 'v1.0')
        
        # Get stock ID
        from database.db_models import Stock
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        
        print(f"\n📍 Current Price: ${current_price:.2f}")
        print(f"📅 Prediction Date: {prediction_date}")
        print(f"\nGenerating predictions with full paths...\n")
        
        # Generate for each horizon
        for horizon_name in horizons:
            if horizon_name not in FORECAST_HORIZONS:
                results[horizon_name] = False
                continue
            
            horizon_days = FORECAST_HORIZONS[horizon_name]
            
            try:
                print(f"  🔮 {horizon_name} ({horizon_days} days)...")
                
                # Get ALL predictions (full path)
                prediction_path = predict_multi_step_with_path(
                    model, initial_sequence, scalers, features, horizon_days
                )
                
                # Save prediction path to database
                save_prediction_path(
                    db, stock.id, prediction_date, horizon_name,
                    prediction_path, base_confidence, model_version
                )
                
                # Also save summary to lstm_predictions table
                final_price = prediction_path[-1]
                predicted_change = final_price - current_price
                predicted_change_pct = (predicted_change / current_price) * 100
                final_confidence = base_confidence * np.exp(-0.01 * horizon_days)
                
                calendar_days = int(horizon_days * 1.4)
                target_date = prediction_date + timedelta(days=calendar_days)
                
                add_lstm_prediction(
                    db=db,
                    symbol=symbol,
                    prediction_date=prediction_date,
                    target_date=target_date,
                    predicted_price=final_price,
                    horizon_days=horizon_days,
                    predicted_change=predicted_change,
                    predicted_change_pct=predicted_change_pct,
                    model_version=model_version,
                    sequence_length=sequence_length,
                    features_used=features,
                    confidence_score=final_confidence,
                    validation_mse=metadata.get('best_val_loss'),
                    validation_r2=metadata.get('validation_r2')
                )
                
                print(f"     ✅ ${final_price:.2f} ({predicted_change_pct:+.2f}%) - "
                      f"{len(prediction_path)} data points saved")
                results[horizon_name] = True
                
            except Exception as e:
                print(f"     ❌ Failed: {str(e)}")
                results[horizon_name] = False
        
        print(f"\n{'='*80}")
        successful = sum(1 for v in results.values() if v)
        print(f"✅ Generated {successful}/{len(horizons)} predictions with full paths")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        for horizon in horizons:
            results[horizon] = False
    
    finally:
        db.close()
    
    return results


def get_prediction_path(
    symbol: str,
    horizon_type: str,
    prediction_date: date = None
) -> List[Dict]:
    """
    Get the full prediction path for graphing.
    
    Args:
        symbol: Stock symbol
        horizon_type: '1day', '1week', '1month', or '6months'
        prediction_date: Which prediction date (default: latest)
        
    Returns:
        List of dicts with date and price for each point
    """
    from database.db_models import Stock
    from database.prediction_paths_model import LSTMPredictionPath
    
    db = SessionLocal()
    
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            return []
        
        query = db.query(LSTMPredictionPath).filter(
            LSTMPredictionPath.stock_id == stock.id,
            LSTMPredictionPath.horizon_type == horizon_type
        )
        
        if prediction_date:
            query = query.filter(LSTMPredictionPath.prediction_date == prediction_date)
        else:
            # Get latest
            latest = db.query(LSTMPredictionPath.prediction_date)\
                .filter(LSTMPredictionPath.stock_id == stock.id)\
                .order_by(LSTMPredictionPath.prediction_date.desc())\
                .first()
            if latest:
                query = query.filter(LSTMPredictionPath.prediction_date == latest[0])
        
        path_points = query.order_by(LSTMPredictionPath.day_offset).all()
        
        return [
            {
                'day_offset': point.day_offset,
                'target_date': point.target_date.isoformat(),
                'predicted_price': point.predicted_price,
                'confidence': point.confidence_score
            }
            for point in path_points
        ]
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate multi-horizon predictions with paths')
    parser.add_argument('--symbol', type=str, help='Stock symbol')
    parser.add_argument('--horizons', nargs='+', choices=list(FORECAST_HORIZONS.keys()))
    
    args = parser.parse_args()
    
    if args.symbol:
        update_multi_horizon_with_paths(args.symbol, horizons=args.horizons)
    else:
        print("Please specify --symbol")
