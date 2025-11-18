#!/usr/bin/env python3
"""
DAILY UPDATE SCRIPT - Keeps database current (run daily via cron)
- Checks for new trading day data (runs after market close 4:30 PM ET)
- Adds today's prices if not already in database
- Prevents duplicate entries by checking latest DB date first
- Run with: docker exec ml_trading_backend python scripts/daily_update.py
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
from config.stocks import get_all_stocks
from database.models import Stock, StockPrice
from sqlalchemy import func


def get_latest_db_date(db, symbol: str):
    """Get most recent date in DB for this stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return None
    return db.query(func.max(StockPrice.date)).filter(StockPrice.stock_id == stock.id).scalar()


def update_stock(symbol: str, name: str = None):
    """Fetch latest price and add to DB if not already present."""
    db = SessionLocal()
    try:
        latest_db_date = get_latest_db_date(db, symbol)
        
        # Get last week of data
        response = get_historical_data(symbol, "1w")
        if response.get("status") != "success":
            return False, response.get('error', 'API error')
        
        data = response.get("data", [])
        if not data:
            return False, "No data"
        
        # Get most recent trading day
        data.sort(key=lambda x: x['date'], reverse=True)
        latest = data[0]
        latest_date = datetime.strptime(latest['date'], '%Y-%m-%d').date()
        
        # Skip if already have this date
        if latest_db_date and latest_date <= latest_db_date:
            return True, "current"
        
        # Add new price
        get_or_create_stock(db, symbol, name)
        add_stock_price(
            db=db,
            symbol=symbol,
            date=datetime.combine(latest_date, datetime.min.time()),
            open_price=float(latest['open']),
            high=float(latest['high']),
            low=float(latest['low']),
            close=float(latest['close']),
            volume=int(latest['volume'])
        )
        
        return True, latest_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        return False, str(e)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    
    stocks = [(s["symbol"], s["name"]) for s in get_all_stocks()]
    updated = 0
    failed = []
    
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Checking {len(stocks)} stocks")
    
    for symbol, name in stocks:
        success, result = update_stock(symbol, name)
        
        if success and result != "current":
            print(f"  {symbol}: added {result}")
            updated += 1
        elif not success:
            print(f"  {symbol}: ERROR - {result}")
            failed.append(symbol)
        
        time.sleep(15)  # Rate limit
    
    print(f"Done: {updated} updated, {len(stocks) - updated - len(failed)} current, {len(failed)} failed")
