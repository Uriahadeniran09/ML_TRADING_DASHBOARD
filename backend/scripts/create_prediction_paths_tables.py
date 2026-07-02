"""
Create prediction_paths tables for storing intermediate predictions for graphs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine
from database.prediction_paths_model import Base, LSTMPredictionPath, TransformerPredictionPath
from sqlalchemy import inspect


def create_prediction_path_tables():
    """Create the prediction path tables."""
    
    print("\n" + "="*80)
    print("CREATING PREDICTION PATH TABLES")
    print("="*80 + "\n")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = []
    
    if 'lstm_prediction_paths' not in existing_tables:
        tables_to_create.append('lstm_prediction_paths')
    
    if 'transformer_prediction_paths' not in existing_tables:
        tables_to_create.append('transformer_prediction_paths')
    
    if not tables_to_create:
        print("✅ All prediction path tables already exist!")
        return
    
    print(f"📝 Creating tables: {', '.join(tables_to_create)}\n")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tables created successfully!\n")
    
    # Verify
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    
    print("="*80)
    print("VERIFICATION")
    print("="*80 + "\n")
    
    for table in tables_to_create:
        if table in new_tables:
            cols = inspector.get_columns(table)
            print(f"✅ {table}")
            print(f"   Columns: {len(cols)}")
            for col in cols:
                print(f"   - {col['name']}: {col['type']}")
            print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    create_prediction_path_tables()
    
    print("📊 USAGE EXAMPLE:")
    print()
    print("# Generate predictions with full paths:")
    print("from models.lstm.multi_horizon_paths import update_multi_horizon_with_paths")
    print("update_multi_horizon_with_paths('AAPL')")
    print()
    print("# Get path data for graphing:")
    print("from models.lstm.multi_horizon_paths import get_prediction_path")
    print("path = get_prediction_path('AAPL', '1month')")
    print("# Returns: [{day_offset: 1, target_date: '...', predicted_price: 183.20}, ...]")
    print()
