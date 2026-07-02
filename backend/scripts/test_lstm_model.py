"""
TEST LSTM MODEL

This script tests the LSTM model functionality:
1. Train a model on a single stock
2. Make predictions
3. Evaluate performance
4. Test model save/load

Run inside Docker container:
docker exec ml_trading_backend python scripts/test_lstm_model.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

from database.db import SessionLocal
from backend.database.db_models import Stock, StockPrice
from models.lstm_model import StockLSTM
from scripts.train_lstm_model import fetch_stock_data, add_technical_indicators


def test_basic_lstm():
    """Test basic LSTM functionality without technical indicators."""
    print("\n" + "="*70)
    print("TEST 1: Basic LSTM (Close Price Only)")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Fetch data for AAPL
        print("\n📊 Fetching AAPL data...")
        df = fetch_stock_data('AAPL', db, min_days=365)
        print(f"   ✓ Loaded {len(df)} days")
        
        # Create simple model
        print("\n🔧 Creating model...")
        model = StockLSTM(
            sequence_length=60,
            features=['close'],
            lstm_units=[50, 25],
            dropout_rate=0.2
        )
        
        # Prepare data
        print("\n📈 Preparing data...")
        X_train, X_test, y_train, y_test = model.prepare_data(df, train_split=0.8)
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        print(f"   Input shape: {X_train.shape}")
        
        # Train
        print("\n🏋️ Training model (this may take a few minutes)...")
        history = model.train(
            X_train, y_train,
            X_test, y_test,
            epochs=20,  # Reduced for testing
            batch_size=32,
            verbose=1
        )
        
        # Evaluate
        print("\n📊 Evaluating model...")
        metrics = model.evaluate(X_test, y_test)
        
        print(f"\n{'='*70}")
        print("RESULTS:")
        print(f"{'='*70}")
        for metric, value in metrics.items():
            if value is not None:
                print(f"{metric.upper()}: {value:.4f}")
        print(f"{'='*70}")
        
        # Make prediction
        print("\n🔮 Making next-day prediction...")
        recent_data = df.tail(60)
        prediction = model.predict_next_day(recent_data)
        current_price = df['close'].iloc[-1]
        
        print(f"\n   Current Price: ${current_price:.2f}")
        print(f"   Predicted Price: ${prediction:.2f}")
        print(f"   Change: ${prediction - current_price:+.2f} ({((prediction - current_price) / current_price * 100):+.2f}%)")
        
        # Test save/load
        print("\n💾 Testing model save/load...")
        save_dir = 'data/models/test_model'
        model.save(save_dir, 'test_lstm')
        
        # Load model
        new_model = StockLSTM()
        new_model.load(save_dir, 'test_lstm')
        
        # Make same prediction
        new_prediction = new_model.predict_next_day(recent_data)
        
        if abs(prediction - new_prediction) < 0.01:
            print("   ✅ Model save/load successful!")
        else:
            print(f"   ⚠️ Predictions differ: {prediction:.2f} vs {new_prediction:.2f}")
        
        print("\n✅ Test 1 PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_lstm_with_indicators():
    """Test LSTM with technical indicators."""
    print("\n" + "="*70)
    print("TEST 2: LSTM with Technical Indicators")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Fetch data
        print("\n📊 Fetching META data...")
        df = fetch_stock_data('META', db, min_days=365)
        print(f"   ✓ Loaded {len(df)} days")
        
        # Add indicators
        print("\n📈 Adding technical indicators...")
        df = add_technical_indicators(df)
        print(f"   ✓ Final dataset: {len(df)} days")
        
        # Create model with multiple features
        features = [
            'close', 'volume',
            'sma_5', 'sma_20',
            'rsi', 'macd',
            'bb_upper', 'bb_lower',
            'roc', 'atr'
        ]
        
        print(f"\n🔧 Creating model with {len(features)} features...")
        model = StockLSTM(
            sequence_length=60,
            features=features,
            lstm_units=[100, 50],
            dropout_rate=0.2
        )
        
        # Prepare data
        print("\n📊 Preparing data...")
        X_train, X_test, y_train, y_test = model.prepare_data(df, train_split=0.8)
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        print(f"   Input shape: {X_train.shape}")
        
        # Train
        print("\n🏋️ Training model...")
        history = model.train(
            X_train, y_train,
            X_test, y_test,
            epochs=20,
            batch_size=32,
            verbose=1
        )
        
        # Evaluate
        print("\n📊 Evaluating model...")
        metrics = model.evaluate(X_test, y_test)
        
        print(f"\n{'='*70}")
        print("RESULTS:")
        print(f"{'='*70}")
        for metric, value in metrics.items():
            if value is not None:
                print(f"{metric.upper()}: {value:.4f}")
        print(f"{'='*70}")
        
        # Make prediction
        print("\n🔮 Making next-day prediction...")
        recent_data = df.tail(70)  # Extra for indicators
        prediction = model.predict_next_day(recent_data)
        current_price = df['close'].iloc[-1]
        
        print(f"\n   Current Price: ${current_price:.2f}")
        print(f"   Predicted Price: ${prediction:.2f}")
        print(f"   Change: ${prediction - current_price:+.2f} ({((prediction - current_price) / current_price * 100):+.2f}%)")
        
        print("\n✅ Test 2 PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_ml_predictor_service():
    """Test the ML predictor service integration."""
    print("\n" + "="*70)
    print("TEST 3: ML Predictor Service Integration")
    print("="*70)
    
    try:
        from services.ml_predictor import (
            get_prediction,
            get_prediction_with_metrics,
            list_available_models
        )
        
        # First, train a quick model
        print("\n📊 Training a test model for AAPL...")
        from scripts.train_lstm_model import train_single_stock
        
        train_single_stock(
            'AAPL',
            sequence_length=60,
            epochs=10,  # Quick training
            use_technical_indicators=True,
            save_dir='data/models'
        )
        
        # List available models
        print("\n📋 Listing available models...")
        models = list_available_models()
        print(f"   Available models: {models}")
        
        if 'AAPL' not in models:
            print("   ⚠️ AAPL model not found in list")
            return False
        
        # Get simple prediction
        print("\n🔮 Getting simple prediction...")
        prediction = get_prediction('AAPL')
        
        if prediction:
            print(f"   ✓ Predicted price: ${prediction:.2f}")
        else:
            print("   ❌ Failed to get prediction")
            return False
        
        # Get prediction with metrics
        print("\n📊 Getting detailed prediction...")
        result = get_prediction_with_metrics('AAPL')
        
        if result:
            print(f"\n{'='*70}")
            print("PREDICTION DETAILS:")
            print(f"{'='*70}")
            print(f"Symbol: {result['symbol']}")
            print(f"Current Price: ${result['current_price']:.2f}")
            print(f"Predicted Price: ${result['predicted_price']:.2f}")
            print(f"Change: ${result['predicted_change']:+.2f} ({result['predicted_change_pct']:+.2f}%)")
            print(f"Prediction Date: {result['prediction_date']}")
            print(f"\nModel Info:")
            print(f"  Last Trained: {result['model_metadata']['last_trained']}")
            print(f"  Training Samples: {result['model_metadata']['training_samples']}")
            print(f"  Features: {', '.join(result['model_metadata']['features_used'][:5])}...")
            print(f"{'='*70}")
        else:
            print("   ❌ Failed to get detailed prediction")
            return False
        
        print("\n✅ Test 3 PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 LSTM MODEL TEST SUITE")
    print("="*70)
    print(f"Started at: {datetime.now()}")
    
    results = []
    
    # Test 1: Basic LSTM
    results.append(("Basic LSTM", test_basic_lstm()))
    
    # Test 2: LSTM with indicators
    results.append(("LSTM with Indicators", test_lstm_with_indicators()))
    
    # Test 3: Service integration
    results.append(("Service Integration", test_ml_predictor_service()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n{passed}/{total} tests passed")
    print(f"Finished at: {datetime.now()}")
    print("="*70 + "\n")
    
    return all(p for _, p in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
