"""
FASTAPI MAIN - Central API server
- Initializes FastAPI app with CORS
- Includes modular routers for different features
- Defines core endpoints (stocks, price, history)
- Manages background scheduler for daily updates
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
import logging
import secrets

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_fetcher import get_current_price, get_historical_data
from services.cache import get_cache, set_cache
from services.scheduler import (
    init_scheduler,
    stop_scheduler,
    get_scheduler_status,
    trigger_daily_update_now,
    trigger_daily_update_background,
)
from database.db import get_db, init_db
from database.crud import get_latest_price, get_stock_prices
from config.stocks import get_all_stocks, get_stock_by_symbol, get_all_sectors, is_valid_symbol
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from app.api import predictions, portfolio, risk

app = FastAPI(title="ML Trading Dashboard API", version="1.0.0")


def _is_valid_cron_request(authorization: str = None, x_cron_secret: str = None) -> bool:
    """Validate cron secret if CRON_SECRET is configured."""
    expected_secret = os.getenv("CRON_SECRET")

    # If secret is not configured, allow request for local/dev convenience.
    if not expected_secret:
        return True

    bearer_secret = None
    if authorization and authorization.startswith("Bearer "):
        bearer_secret = authorization.replace("Bearer ", "", 1).strip()

    candidates = [s for s in [x_cron_secret, bearer_secret] if s]
    return any(secrets.compare_digest(candidate, expected_secret) for candidate in candidates)

# Initialize database and scheduler on startup
@app.on_event("startup")
async def startup_event():
    """Run when the app starts"""
    logger.info("=" * 60)
    logger.info("Starting ML Trading Dashboard API...")
    logger.info("=" * 60)
    
    # Initialize database
    init_db()
    logger.info("✓ Database initialized")
    
    # Initialize scheduler for daily updates
    init_scheduler()
    logger.info("✓ Scheduler initialized")
    logger.info("=" * 60)
    logger.info("Ready to accept requests!")
    logger.info("=" * 60)


# Shutdown event to stop scheduler
@app.on_event("shutdown")
async def shutdown_event():
    """Run when the app shuts down"""
    logger.info("Shutting down scheduler...")
    stop_scheduler()
    logger.info("✓ Scheduler stopped")

# CORS - allows frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers
app.include_router(predictions.router)
app.include_router(portfolio.router)
app.include_router(risk.router)

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


# ============================================================================
# SCHEDULER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/scheduler/status")
async def scheduler_status():
    """
    Get the current status of the daily update scheduler.
    
    Returns information about:
    - Whether scheduler is running
    - Scheduled jobs
    - Next run time
    """
    return get_scheduler_status()


@app.post("/api/scheduler/update-now")
async def trigger_update_now():
    """
    Manually trigger a daily stock price update immediately.
    
    Useful for:
    - Testing the update process
    - Forcing an update outside of scheduled time
    - Verifying recent data
    
    Returns:
    - Success status
    - Number of stocks updated
    - Any errors encountered
    """
    logger.info("[API] Manual daily update triggered")
    result = trigger_daily_update_now()
    return result


@app.api_route("/api/cron/daily-update", methods=["GET", "POST"])
async def cron_daily_update(
    authorization: str = Header(default=None),
    x_cron_secret: str = Header(default=None),
):
    """
    External cron endpoint for daily update.

    Configure CRON_SECRET and send it via either:
    - Authorization: Bearer <CRON_SECRET>
    - X-Cron-Secret: <CRON_SECRET>
    """
    if not _is_valid_cron_request(authorization=authorization, x_cron_secret=x_cron_secret):
        raise HTTPException(status_code=401, detail="Invalid cron secret")

    logger.info("[CRON] Daily update trigger received")
    return trigger_daily_update_background(trigger="cron-endpoint")


@app.get("/api/health")
async def health_check():
    """
    Extended health check including scheduler status.
    """
    scheduler_info = get_scheduler_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler": scheduler_info
    }


