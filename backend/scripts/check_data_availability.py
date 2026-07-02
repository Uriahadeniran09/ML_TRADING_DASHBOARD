"""
CHECK DATA AVAILABILITY - View data status for all stocks
- Shows date range (oldest to newest) for each stock
- Shows total trading days available
- Displays in a readable table format
- Run with: python scripts/check_data_availability.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from database.db import SessionLocal
from database.db_models import Stock, StockPrice
from sqlalchemy import func
from config.stocks import get_all_stocks


def check_data_availability():
    """
    Check and display data availability for all stocks.
    """
    db = SessionLocal()
    
    print("\n" + "="*120)
    print(f"{'STOCK':<8} {'COMPANY':<30} {'OLDEST DATE':<15} {'NEWEST DATE':<15} {'TRADING DAYS':<15} {'YEARS':<8}")
    print("="*120)
    
    all_stocks = get_all_stocks()
    stocks_with_data = 0
    stocks_without_data = 0
    total_records = 0
    
    for stock_config in all_stocks:
        symbol = stock_config['symbol']
        name = stock_config['name']
        
        # Get the stock from database
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            print(f"{symbol:<8} {name:<30} {'NO DATA':<15} {'—':<15} {'0':<15} {'0':<8}")
            stocks_without_data += 1
            continue
        
        # Get min and max dates
        result = db.query(
            func.min(StockPrice.date).label('oldest'),
            func.max(StockPrice.date).label('newest'),
            func.count(StockPrice.id).label('count')
        ).filter(StockPrice.stock_id == stock.id).first()
        
        if result[0] is None:  # No price data
            print(f"{symbol:<8} {name:<30} {'NO DATA':<15} {'—':<15} {'0':<15} {'0':<8}")
            stocks_without_data += 1
            continue
        
        oldest_date = result[0]
        newest_date = result[1]
        record_count = result[2]
        
        # Calculate years of data (roughly)
        days_span = (newest_date - oldest_date).days
        years = days_span / 365.25
        
        total_records += record_count
        stocks_with_data += 1
        
        print(f"{symbol:<8} {name:<30} {str(oldest_date):<15} {str(newest_date):<15} {record_count:<15} {years:>6.1f}y")
    
    print("="*120)
    print(f"\nSummary:")
    print(f"  Stocks with data: {stocks_with_data}/50")
    print(f"  Stocks without data: {stocks_without_data}/50")
    print(f"  Total price records: {total_records:,}")
    print(f"  Average records/stock: {total_records // stocks_with_data if stocks_with_data > 0 else 0:,}")
    
    # Find gaps in data
    print(f"\n{'STOCKS WITH INCOMPLETE DATA:':<50}")
    print("-"*80)
    
    incomplete_count = 0
    for stock_config in all_stocks:
        symbol = stock_config['symbol']
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            continue
        
        result = db.query(
            func.min(StockPrice.date).label('oldest'),
            func.max(StockPrice.date).label('newest'),
            func.count(StockPrice.id).label('count')
        ).filter(StockPrice.stock_id == stock.id).first()
        
        if result[0] is None:
            continue
        
        oldest_date = result[0]
        newest_date = result[1]
        record_count = result[2]
        
        # Expected ~252 trading days per year
        days_span = (newest_date - oldest_date).days
        expected_records = (days_span / 365.25) * 252  # Rough estimate
        
        # If actual is significantly less than expected, flag it
        if record_count < expected_records * 0.8:  # Less than 80% of expected
            incomplete_count += 1
            pct = (record_count / expected_records * 100) if expected_records > 0 else 0
            print(f"  {symbol:<8} {record_count:>5} records ({pct:>5.1f}% of expected) | {oldest_date} to {newest_date}")
    
    if incomplete_count == 0:
        print("  ✓ All stocks have complete data!")
    
    db.close()
    print("\n")


if __name__ == "__main__":
    try:
        check_data_availability()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
