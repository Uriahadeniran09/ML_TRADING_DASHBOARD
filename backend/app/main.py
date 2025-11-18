"""
FASTAPI MAIN - REST API endpoints for frontend
- GET /api/stocks - list available stocks (from config)
- GET /api/sectors - list all sectors
- GET /api/price?symbol=AAPL - current price (cache → DB → API)
- GET /api/history?symbol=AAPL&period=1mo - historical data (cache → DB → API)
- Smart data fetching: checks cache first, then database, then external API
- Returns "source" field so you know where data came from
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_fetcher import get_current_price, get_historical_data
from services.cache import get_cache, set_cache
from database.db import get_db, init_db
from database.crud import get_latest_price, get_stock_prices
from config.stocks import get_all_stocks, get_stock_by_symbol, get_all_sectors, is_valid_symbol
from datetime import datetime, timedelta

app = FastAPI(title="ML Trading Dashboard API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Run when the app starts"""
    print("Starting ML Trading Dashboard API...")
    init_db()
    print("Ready to accept requests!")

# CORS - allows frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check"""
    return {"status": "online", "message": "ML Trading Dashboard API"}


@app.get("/api/stocks")
async def get_stocks(sector: str = None):
    """
    Get list of available stocks.
    Optionally filter by sector.
    """
    from config.stocks import get_stocks_by_sector
    
    if sector:
        stocks = get_stocks_by_sector(sector)
        if not stocks:
            raise HTTPException(status_code=404, detail=f"No stocks found for sector: {sector}")
        return {"stocks": stocks, "count": len(stocks)}
    
    return {"stocks": get_all_stocks(), "count": len(get_all_stocks())}


@app.get("/api/sectors")
async def get_sectors():
    """
    Get list of all sectors.
    """
    sectors = get_all_sectors()
    return {"sectors": sorted(sectors), "count": len(sectors)}


@app.get("/api/price")
async def get_price(symbol: str, db: Session = Depends(get_db)):
    """
    Get current price for a stock symbol.
    Checks: Cache → Database → API (in that order)
    """
    if not is_valid_symbol(symbol):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid stock symbol. Use /api/stocks to see available stocks."
        )
    
    try:
        stock_info = get_stock_by_symbol(symbol)
        cache_key = f"price:current:{symbol}"
        
        # 1. Check cache first (5-minute TTL)
        cached = get_cache(cache_key)
        if cached:
            return {
                "symbol": symbol,
                "name": stock_info["name"],
                "sector": stock_info["sector"],
                "data": cached,
                "source": "cache"
            }
        
        # 2. Check database (if recent data exists - within last 7 days)
        latest = get_latest_price(db, symbol)
        
        if latest:
            days_old = (datetime.now().date() - latest.date).days
            # Use database data if it's less than 7 days old
            if days_old < 7:
                price_data = {
                    "symbol": symbol,
                    "date": str(latest.date),
                    "open": round(latest.open, 2),
                    "high": round(latest.high, 2),
                    "low": round(latest.low, 2),
                    "close": round(latest.close, 2),
                    "volume": latest.volume,
                    "status": "success",
                    "days_old": days_old
                }
                # Cache it for next time
                set_cache(cache_key, price_data, expire_seconds=300)
                return {
                    "symbol": symbol,
                    "name": stock_info["name"],
                    "sector": stock_info["sector"],
                    "data": price_data,
                    "source": "database"
                }
        
        # 3. Fallback to API (and cache the result)
        data = get_current_price(symbol)
        if data.get("status") == "success":
            set_cache(cache_key, data, expire_seconds=300)
        
        return {
            "symbol": symbol, 
            "name": stock_info["name"],
            "sector": stock_info["sector"],
            "data": data,
            "source": "api"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/history")
async def get_history(symbol: str, period: str = "1mo", db: Session = Depends(get_db)):
    """
    Get historical price data for a stock symbol.
    Period: 1d, 1w, 1mo, 3mo, 6mo, 1y, 2y, 5y
    Checks: Cache → Database → API (in that order)
    """
    if not is_valid_symbol(symbol):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid stock symbol. Use /api/stocks to see available stocks."
        )
    
    try:
        stock_info = get_stock_by_symbol(symbol)
        cache_key = f"history:{symbol}:{period}"
        
        # 1. Check cache first (1-hour TTL)
        cached = get_cache(cache_key)
        if cached:
            return {
                "symbol": symbol,
                "name": stock_info["name"],
                "sector": stock_info["sector"],
                "period": period,
                "data": cached.get("data", cached),
                "source": "cache"
            }
        
        # 2. Try to get from database
        period_days = {
            "1d": 1, "1w": 7, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_days.get(period, 30)
        
        db_prices = get_stock_prices(db, symbol, limit=days * 2)  # Get more than needed
        
        if db_prices and len(db_prices) >= min(days, 30):  # If we have enough data
            history_data = {
                "symbol": symbol,
                "period": period,
                "data": [
                    {
                        "date": str(price.date),
                        "open": round(price.open, 2),
                        "high": round(price.high, 2),
                        "low": round(price.low, 2),
                        "close": round(price.close, 2),
                        "volume": price.volume
                    }
                    for price in db_prices[:days]
                ],
                "count": len(db_prices[:days]),
                "status": "success"
            }
            # Cache it
            set_cache(cache_key, history_data, expire_seconds=3600)
            return {
                "symbol": symbol,
                "name": stock_info["name"],
                "sector": stock_info["sector"],
                "period": period,
                "data": history_data,
                "source": "database"
            }
        
        # 3. Fallback to API
        data = get_historical_data(symbol, period)
        if data.get("status") == "success":
            set_cache(cache_key, data, expire_seconds=3600)
        
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "sector": stock_info["sector"],
            "period": period,
            "data": data,
            "source": "api"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TODO: We'll build these endpoints next
# @app.get("/api/prediction")
# @app.get("/api/risk")
# @app.post("/api/portfolio/optimize")
