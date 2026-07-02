#!/usr/bin/env python3
"""
DATA BACKFILL SCRIPT - Update and fill gaps in stock price data
- Fetches latest data for all 50 stocks
- Fills gaps in historical data
- Shows detailed timeframes for each stock
- Useful for fixing stale or incomplete data

Run with: python scripts/backfill_prices.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import time
from database.db import SessionLocal, init_db
from database.crud import add_stock_price, get_or_create_stock
from services.data_fetcher import get_historical_data
from config.stocks import get_all_stocks
from database.db_models import Stock, StockPrice
from sqlalchemy import func


def get_stock_date_range(db, symbol: str):
    """Get the date range of prices for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return None, None, 0
    
    result = db.query(
        func.min(StockPrice.date).label('min_date'),
        func.max(StockPrice.date).label('max_date'),
        func.count(StockPrice.id).label('count')
    ).filter(StockPrice.stock_id == stock.id).first()
    
    return result.min_date, result.max_date, result.count


def backfill_stock(symbol: str, name: str = None, years: int = 2):
    """
    Fetch historical data and fill database with all available data.
    
    Args:
        symbol: Stock symbol
        name: Company name
        years: How many years of history to fetch (default 2)
    """
    db = SessionLocal()
    try:
        # Get current data in DB
        min_db_date, max_db_date, db_count = get_stock_date_range(db, symbol)
        
        # Fetch historical data (wider range to get more)
        print(f"\n📊 {symbol}")
        print(f"  Current DB: {min_db_date} to {max_db_date} ({db_count} records)")
        
        # Fetch 1 year of data to backfill
        response = get_historical_data(symbol, "1y")
        if response.get("status") != "success":
            print(f"  ❌ API Error: {response.get('error', 'Unknown error')}")
            return False, "API error"
        
        data = response.get("data", [])
        if not data:
            print(f"  ❌ No data returned from API")
            return False, "No data"
        
        # Sort by date ascending
        data.sort(key=lambda x: x['date'])
        
        # Get or create stock
        get_or_create_stock(db, symbol, name)
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        
        # Add all prices (skip if already exists)
        added = 0
        for record in data:
            try:
                price_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                
                # Check if this date already exists
                existing = db.query(StockPrice).filter(
                    StockPrice.stock_id == stock.id,
                    StockPrice.date == price_date
                ).first()
                
                if not existing:
                    add_stock_price(
                        db=db,
                        symbol=symbol,
                        date=datetime.combine(price_date, datetime.min.time()),
                        open_price=float(record['open']),
                        high=float(record['high']),
                        low=float(record['low']),
                        close=float(record['close']),
                        volume=int(record['volume'])
                    )
                    added += 1
            except Exception as e:
                continue
        
        # Get updated range
        new_min_date, new_max_date, new_count = get_stock_date_range(db, symbol)
        
        if added > 0:
            print(f"  ✅ Updated: {min_db_date} to {new_max_date}")
            print(f"     Added {added} new records | Total: {new_count} records")
        else:
            print(f"  ✓ Current: {new_min_date} to {new_max_date} ({new_count} records)")
        
        return True, new_count
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False, str(e)
    finally:
        db.close()


def get_all_stock_ranges(db):
    """Get date ranges for all stocks."""
    print("\n" + "=" * 70)
    print("CURRENT DATABASE STATUS")
    print("=" * 70)
    
    stocks = db.query(Stock).all()
    
    date_ranges = []
    for stock in stocks:
        min_date, max_date, count = get_stock_date_range(db, stock.symbol)
        if count > 0:
            days_old = (datetime.now().date() - max_date).days if max_date else -1
            date_ranges.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'min_date': min_date,
                'max_date': max_date,
                'count': count,
                'days_old': days_old
            })
    
    # Sort by max_date to see oldest first
    date_ranges.sort(key=lambda x: x['max_date'] if x['max_date'] else datetime.min.date())
    
    print(f"\n{'Symbol':<8} {'Name':<35} {'From':<12} {'To':<12} {'Days':<6} {'Count':<6}")
    print("-" * 80)
    
    for dr in date_ranges:
        age_str = f"{dr['days_old']}d" if dr['days_old'] >= 0 else "NEW"
        print(f"{dr['symbol']:<8} {dr['name']:<35} {str(dr['min_date']):<12} {str(dr['max_date']):<12} {age_str:<6} {dr['count']:<6}")
    
    print("-" * 80)
    
    # Statistics
    total_records = sum([dr['count'] for dr in date_ranges])
    avg_age = sum([dr['days_old'] for dr in date_ranges if dr['days_old'] >= 0]) / len([dr for dr in date_ranges if dr['days_old'] >= 0]) if date_ranges else 0
    
    print(f"Total: {len(stocks)} stocks | {total_records} records | Avg age: {avg_age:.0f} days")
    print("=" * 70)
    
    return date_ranges


def main():
    print("\n" + "=" * 70)
    print("🔄 BACKFILLING STOCK PRICE DATA")
    print("=" * 70)
    
    init_db()
    
    # Show current status
    db = SessionLocal()
    get_all_stock_ranges(db)
    db.close()
    
    # Backfill each stock
    print(f"\n🔄 UPDATING {len(get_all_stocks())} STOCKS...")
    print("=" * 70)
    
    stocks = [(s["symbol"], s["name"]) for s in get_all_stocks()]
    success_count = 0
    error_count = 0
    
    for i, (symbol, name) in enumerate(stocks, 1):
        success, result = backfill_stock(symbol, name)
        
        if success:
            success_count += 1
        else:
            error_count += 1
        
        # Rate limit
        time.sleep(15)
    
    # Show final status
    print("\n" + "=" * 70)
    print("📊 FINAL DATABASE STATUS")
    print("=" * 70)
    
    db = SessionLocal()
    final_ranges = get_all_stock_ranges(db)
    db.close()
    
    print(f"\n✅ Update completed!")
    print(f"   - Updated: {success_count} stocks")
    print(f"   - Errors: {error_count} stocks")
    
    # Show newest and oldest data
    if final_ranges:
        newest = max(final_ranges, key=lambda x: x['max_date'] if x['max_date'] else datetime.min.date())
        oldest = min(final_ranges, key=lambda x: x['max_date'] if x['max_date'] else datetime.max.date())
        
        print(f"\n📅 Data Coverage:")
        print(f"   - Newest: {newest['symbol']} ({newest['max_date']})")
        print(f"   - Oldest: {oldest['symbol']} ({oldest['max_date']})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
