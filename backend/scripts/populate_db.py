"""
POPULATE DATABASE SCRIPT - Initial data load (run once)
- Fetches 5 years historical data for all 50 stocks from Polygon.io
- Saves ~63,000 price records to PostgreSQL via CRUD functions
- Takes ~12 minutes (15 sec delay between requests for rate limit)
- Run with: docker exec ml_trading_backend python scripts/populate_db.py
- Uses: database/crud.py to save, services/data_fetcher.py to fetch
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import time
from database.db import SessionLocal, init_db
from database.crud import add_stock_price, get_or_create_stock
from services.data_fetcher import get_historical_data
from config.stocks import get_all_stocks, is_valid_symbol
from database.models import Stock, StockPrice
from sqlalchemy import func



def populate_stock_data(symbol: str, name: str = None, period: str = "1mo", delay: int = 15):
    """
    Fetch historical data from Polygon.io and save to database.
    
    Args:
        symbol: Stock symbol
        name: Stock company name
        period: Time period (1d, 1mo, 5y, etc.)
        delay: Seconds to wait between API calls (Polygon.io FREE: 5 req/min = 15s delay)
    """
    db = SessionLocal()
    try:
        response = get_historical_data(symbol, period)
        
        if response.get("status") != "success":
            print(f"  ❌ {symbol}: {response.get('error', 'Unknown error')}")
            return False
        
        data = response.get("data", [])
        if not data:
            print(f"  ❌ {symbol}: No data received")
            return False
        
        # Ensure stock exists with name
        get_or_create_stock(db, symbol, name)
        
        added_count = 0
        for record in data:
            try:
                date = datetime.strptime(record['date'], '%Y-%m-%d')
                add_stock_price(
                    db=db,
                    symbol=symbol,
                    date=date,
                    open_price=float(record['open']),
                    high=float(record['high']),
                    low=float(record['low']),
                    close=float(record['close']),
                    volume=int(record['volume'])
                )
                added_count += 1
            except Exception as e:
                continue
        
        print(f"  ✅ {symbol}: {added_count} records")
        
        if delay > 0:
            time.sleep(delay)
        
        return True
        
    except Exception as e:
        print(f"  ❌ {symbol}: Error - {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    
    available_stocks = get_all_stocks()
    symbols = [(s["symbol"], s["name"]) for s in available_stocks]
    period = "5y"
    
    print(f"\n📊 Stock Data Population - {len(symbols)} stocks × 5 years")
    print(f"⏱️  Estimated time: ~{len(symbols) * 15 / 60:.0f} minutes")
    print(f"📦 Estimated records: ~{len(symbols) * 1260:,}\n")
    
    confirm = input("Start? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        exit(0)
    
    start_time = time.time()
    success_count = 0
    failed_stocks = []
    skipped_stocks = []
    
    # Check which stocks already have data
    db = SessionLocal()
    existing_data = db.query(
        Stock.symbol,
        func.count(StockPrice.id).label('count')
    ).outerjoin(StockPrice).group_by(Stock.id, Stock.symbol).all()
    existing_stocks = {stock.symbol: stock.count for stock in existing_data}
    db.close()
    
    print(f"\n🚀 Processing {len(symbols)} stocks...\n")
    
    for i, (symbol, name) in enumerate(symbols, 1):
        # Skip if stock already has data
        if symbol in existing_stocks and existing_stocks[symbol] > 0:
            print(f"[{i}/{len(symbols)}] ⏭️  {symbol} - skipped ({existing_stocks[symbol]} records)")
            skipped_stocks.append(symbol)
            continue
            
        print(f"[{i}/{len(symbols)}] {symbol}...", end=" ")
        if populate_stock_data(symbol, name, period, delay=15):
            success_count += 1
        else:
            failed_stocks.append(symbol)
    
    elapsed = (time.time() - start_time) / 60
    print(f"\n{'='*60}")
    print(f"✅ Success: {success_count} | ⏭️  Skipped: {len(skipped_stocks)} | ❌ Failed: {len(failed_stocks)}")
    if failed_stocks:
        print(f"Failed: {', '.join(failed_stocks)}")
    print(f"⏱️  Time: {elapsed:.1f} min")
    print(f"{'='*60}")
