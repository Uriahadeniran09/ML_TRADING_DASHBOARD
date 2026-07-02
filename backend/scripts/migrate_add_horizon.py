"""
DATABASE MIGRATION: Add horizon_days column to lstm_predictions table

This script adds the horizon_days column to support multi-horizon predictions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.db import engine, SessionLocal


def migrate_add_horizon_column():
    """
    Add horizon_days column to lstm_predictions table.
    Sets default value to 1 for existing predictions.
    """
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Adding horizon_days column")
    print("="*70 + "\n")
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'lstm_predictions' 
                AND column_name = 'horizon_days'
            """)
            
            result = conn.execute(check_query)
            exists = result.fetchone()
            
            if exists:
                print("✅ Column 'horizon_days' already exists. No migration needed.")
                return
            
            # Add the column
            print("📝 Adding 'horizon_days' column...")
            add_column_query = text("""
                ALTER TABLE lstm_predictions 
                ADD COLUMN horizon_days INTEGER NOT NULL DEFAULT 1
            """)
            conn.execute(add_column_query)
            
            # Create index for better query performance
            print("📝 Creating index on horizon_days...")
            create_index_query = text("""
                CREATE INDEX IF NOT EXISTS idx_lstm_predictions_horizon 
                ON lstm_predictions(horizon_days)
            """)
            conn.execute(create_index_query)
            
            # Update existing records to have horizon_days = 1
            print("📝 Updating existing records...")
            update_query = text("""
                UPDATE lstm_predictions 
                SET horizon_days = 1 
                WHERE horizon_days IS NULL
            """)
            conn.execute(update_query)
            
            conn.commit()
            
            print("\n✅ Migration completed successfully!")
            print("   - Added 'horizon_days' column")
            print("   - Created index")
            print("   - Updated existing records")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            conn.rollback()
            import traceback
            traceback.print_exc()
            raise


def verify_migration():
    """
    Verify the migration was successful.
    """
    print("\n" + "="*70)
    print("VERIFYING MIGRATION")
    print("="*70 + "\n")
    
    db = SessionLocal()
    
    try:
        # Check column exists
        query = text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'lstm_predictions' 
            AND column_name = 'horizon_days'
        """)
        
        result = db.execute(query)
        row = result.fetchone()
        
        if row:
            print(f"✅ Column Details:")
            print(f"   Name: {row[0]}")
            print(f"   Type: {row[1]}")
            print(f"   Nullable: {row[2]}")
            print(f"   Default: {row[3]}")
        else:
            print("❌ Column 'horizon_days' not found!")
            return False
        
        # Check if index exists
        index_query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'lstm_predictions' 
            AND indexname = 'idx_lstm_predictions_horizon'
        """)
        
        result = db.execute(index_query)
        index = result.fetchone()
        
        if index:
            print(f"✅ Index created: {index[0]}")
        else:
            print("⚠️  Index not found (this is optional)")
        
        # Count records
        count_query = text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT horizon_days) as unique_horizons
            FROM lstm_predictions
        """)
        
        result = db.execute(count_query)
        counts = result.fetchone()
        
        print(f"\n📊 Current Data:")
        print(f"   Total predictions: {counts[0]}")
        print(f"   Unique horizons: {counts[1]}")
        
        print("\n" + "="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔧 Starting database migration...\n")
    
    try:
        migrate_add_horizon_column()
        verify_migration()
        print("\n✅ All done! You can now use multi-horizon predictions.\n")
    except Exception as e:
        print(f"\n❌ Migration process failed: {str(e)}\n")
        sys.exit(1)
