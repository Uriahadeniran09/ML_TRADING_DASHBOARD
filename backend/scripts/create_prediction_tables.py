"""
CREATE PREDICTION TABLES

This script creates the new LSTM and Transformer prediction tables in the database.

Run this script to add the new tables:
    docker exec ml_trading_backend python scripts/create_prediction_tables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine, SessionLocal
from backend.database.db_models import Base, LSTMPrediction, TransformerPrediction
from sqlalchemy import inspect


def table_exists(table_name):
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_prediction_tables():
    """Create LSTM and Transformer prediction tables."""
    print("\n" + "="*70)
    print("CREATING PREDICTION TABLES")
    print("="*70)
    
    # Check existing tables
    lstm_exists = table_exists('lstm_predictions')
    transformer_exists = table_exists('transformer_predictions')
    
    print(f"\n📊 Current status:")
    print(f"   lstm_predictions table: {'✓ EXISTS' if lstm_exists else '✗ NOT FOUND'}")
    print(f"   transformer_predictions table: {'✓ EXISTS' if transformer_exists else '✗ NOT FOUND'}")
    
    if lstm_exists and transformer_exists:
        print("\n✅ Both tables already exist. No action needed.")
        return
    
    # Create tables
    print("\n🔧 Creating new tables...")
    
    try:
        # Create only the new tables
        if not lstm_exists:
            LSTMPrediction.__table__.create(bind=engine, checkfirst=True)
            print("   ✓ Created lstm_predictions table")
        
        if not transformer_exists:
            TransformerPrediction.__table__.create(bind=engine, checkfirst=True)
            print("   ✓ Created transformer_predictions table")
        
        print("\n✅ Prediction tables created successfully!")
        
        # Verify creation
        db = SessionLocal()
        try:
            lstm_count = db.query(LSTMPrediction).count()
            transformer_count = db.query(TransformerPrediction).count()
            
            print(f"\n📊 Table verification:")
            print(f"   LSTM predictions: {lstm_count} records")
            print(f"   Transformer predictions: {transformer_count} records")
        finally:
            db.close()
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {str(e)}")
        raise
    
    print("="*70 + "\n")


def show_table_info():
    """Display information about the prediction tables."""
    print("\n" + "="*70)
    print("PREDICTION TABLES SCHEMA")
    print("="*70)
    
    print("\n📊 LSTM Predictions Table:")
    print("   - id: Primary key")
    print("   - stock_id: Foreign key to stocks table")
    print("   - prediction_date: Date prediction was made")
    print("   - target_date: Date being predicted for")
    print("   - predicted_price: Predicted closing price")
    print("   - predicted_change: Price change in dollars")
    print("   - predicted_change_pct: Price change in percentage")
    print("   - actual_price: Actual price (filled in later)")
    print("   - model_version: Model version identifier")
    print("   - sequence_length: Number of days used for prediction")
    print("   - features_used: JSON string of features")
    print("   - confidence_score: Overall confidence (0-1)")
    print("   - validation_mse: Model's MSE score")
    print("   - validation_r2: Model's R² score")
    
    print("\n📊 Transformer Predictions Table:")
    print("   - id: Primary key")
    print("   - stock_id: Foreign key to stocks table")
    print("   - prediction_date: Date prediction was made")
    print("   - target_date: Date being predicted for")
    print("   - predicted_price: Predicted closing price")
    print("   - predicted_change: Price change in dollars")
    print("   - predicted_change_pct: Price change in percentage")
    print("   - actual_price: Actual price (filled in later)")
    print("   - model_version: Model version identifier")
    print("   - sequence_length: Number of days used for prediction")
    print("   - features_used: JSON string of features")
    print("   - num_attention_heads: Number of attention heads")
    print("   - num_layers: Number of transformer layers")
    print("   - confidence_score: Overall confidence (0-1)")
    print("   - validation_mse: Model's MSE score")
    print("   - validation_r2: Model's R² score")
    print("   - attention_weights: JSON string of attention weights")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        create_prediction_tables()
        show_table_info()
        
        print("\n💡 Next steps:")
        print("   1. Update ml_predictor.py to save predictions to these tables")
        print("   2. Train LSTM models and save predictions")
        print("   3. Build Transformer models and save predictions")
        print("   4. Compare predictions between models")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
