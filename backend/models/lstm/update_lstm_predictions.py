"""
UPDATE LSTM PREDICTIONS IN DATABASE

Saves LSTM model predictions to the lstm_predictions table in PostgreSQL.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, List
import json

from database.db import SessionLocal
from database.crud import add_lstm_prediction
from .lstmmodel import load_saved_model
from .data import get_data_from_db, add_technical_indicators, preprocess_data


def predict_next_day(
    model: object,
    recent_data: np.ndarray,
    scaler: object
) -> float:
    """
    Predict next day's closing price.
    
    Args:
        model: Trained LSTM model
        recent_data: Recent normalized sequences
        scaler: Scaler for target column
        
    Returns:
        Predicted price (denormalized)
    """
    prediction = model.predict(recent_data, verbose=0)
    predicted_price = scaler.inverse_transform(prediction)[0][0]
    return float(predicted_price)


def update_predictions_in_db(
    symbol: str,
    model_dir: str = 'data/models/lstm',
    days_ahead: int = 1
) -> bool:
    """
    Make prediction and save to lstm_predictions table.
    
    Args:
        symbol: Stock symbol
        model_dir: Directory where model is saved
        days_ahead: Days ahead to predict (currently only supports 1)
        
    Returns:
        True if successful, False otherwise
    """
    if days_ahead != 1:
        raise NotImplementedError("Multi-day predictions not yet supported")
    
    db = SessionLocal()
    
    try:
        print(f"\n📊 Generating LSTM prediction for {symbol}...")
        
        # Load model
        print(f"   Loading model...")
        model, scalers, metadata = load_saved_model(symbol, model_dir)
        
        # Get recent data
        print(f"   Fetching recent data...")
        df = get_data_from_db(symbol, min_days=100)
        df = add_technical_indicators(df)
        
        # Get features from metadata
        features = metadata.get('features', ['close'])
        sequence_length = metadata.get('sequence_length', 60)
        
        # Prepare recent sequence
        recent_data = df.tail(sequence_length + 10).copy()  # Extra for safety
        
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
        
        # Create input sequence
        X = np.concatenate(scaled_sequence, axis=1)
        X = X[-sequence_length:].reshape(1, sequence_length, len(features))
        
        # Make prediction
        print(f"   Making prediction...")
        predicted_price = predict_next_day(model, X, scalers['close'])
        
        # Get current price
        current_price = float(df['close'].iloc[-1])
        predicted_change = predicted_price - current_price
        predicted_change_pct = (predicted_change / current_price) * 100
        
        # Get validation metrics from metadata
        validation_mse = metadata.get('best_val_loss')
        validation_r2 = metadata.get('validation_r2')
        confidence_score = metadata.get('confidence_score')
        
        # Dates
        prediction_date = date.today()
        target_date = prediction_date + timedelta(days=1)
        
        # Save to database
        print(f"   Saving to database...")
        add_lstm_prediction(
            db=db,
            symbol=symbol,
            prediction_date=prediction_date,
            target_date=target_date,
            predicted_price=predicted_price,
            predicted_change=predicted_change,
            predicted_change_pct=predicted_change_pct,
            model_version=metadata.get('model_version', 'v1.0'),
            sequence_length=sequence_length,
            features_used=features,
            confidence_score=confidence_score,
            validation_mse=validation_mse,
            validation_r2=validation_r2
        )
        
        print(f"\n✅ Prediction saved successfully!")
        print(f"   Symbol: {symbol}")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   Predicted Price: ${predicted_price:.2f}")
        print(f"   Change: ${predicted_change:+.2f} ({predicted_change_pct:+.2f}%)")
        print(f"   Target Date: {target_date}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating predictions for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def batch_update_predictions(
    symbols: List[str] = None,
    model_dir: str = 'data/models/lstm'
) -> Dict[str, bool]:
    """
    Update predictions for multiple stocks.
    
    Args:
        symbols: List of symbols (None = all available models)
        model_dir: Directory where models are saved
        
    Returns:
        Dictionary mapping symbols to success status
    """
    from .lstmmodel import list_saved_models
    
    # Get all models if no symbols specified
    if symbols is None:
        symbols = list_saved_models(model_dir)
    
    if not symbols:
        print("⚠️  No models found")
        return {}
    
    print(f"\n{'='*70}")
    print(f"BATCH UPDATE LSTM PREDICTIONS")
    print(f"{'='*70}")
    print(f"Processing {len(symbols)} stocks...\n")
    
    results = {}
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] {symbol}")
        print("-" * 70)
        
        success = update_predictions_in_db(symbol, model_dir)
        results[symbol] = success
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        failed_symbols = [s for s, success in results.items() if not success]
        print(f"\n❌ Failed stocks: {', '.join(failed_symbols)}")
    
    print(f"{'='*70}\n")
    
    return results


def update_actual_prices():
    """
    Update actual prices for past predictions (for evaluation).
    This should be run daily to fill in actual prices for yesterday's predictions.
    """
    from backend.database.db_models import LSTMPrediction, Stock, StockPrice
    
    db = SessionLocal()
    
    try:
        # Get all predictions where target_date is today or earlier and actual_price is NULL
        today = date.today()
        
        predictions = db.query(LSTMPrediction).filter(
            LSTMPrediction.target_date <= today,
            LSTMPrediction.actual_price.is_(None)
        ).all()
        
        if not predictions:
            print("ℹ️  No predictions to update")
            return
        
        print(f"\n📊 Updating actual prices for {len(predictions)} predictions...")
        
        updated = 0
        for pred in predictions:
            # Get actual price for target date
            stock = db.query(Stock).filter(Stock.id == pred.stock_id).first()
            if not stock:
                continue
            
            actual = db.query(StockPrice).filter(
                StockPrice.stock_id == stock.id,
                StockPrice.date == pred.target_date
            ).first()
            
            if actual:
                pred.actual_price = float(actual.close)
                updated += 1
        
        db.commit()
        
        print(f"✅ Updated {updated} predictions with actual prices")
        
    except Exception as e:
        print(f"❌ Error updating actual prices: {e}")
        db.rollback()
        
    finally:
        db.close()
