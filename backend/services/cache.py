"""
REDIS CACHE SERVICE - Caching layer to reduce API calls
- Stores API responses temporarily in Redis (in-memory storage)
- Reduces Polygon.io API usage (5 req/min limit on free tier)
- Current price cached 5 min, historical data cached 1 hour
- Used by: API endpoints to speed up repeated requests
"""
import redis
import json
import os
from typing import Optional, Any
from datetime import timedelta
import threading

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
    retry_on_timeout=False
)


def get_cache(key: str) -> Optional[Any]:
    """
    Get value from Redis cache.
    Returns None if key doesn't exist, is expired, or Redis is unavailable.
    Uses threading with timeout to prevent hanging.
    """
    result = [None]
    
    def _get():
        try:
            value = redis_client.get(key)
            if value:
                result[0] = json.loads(value)
        except Exception as e:
            pass  # Fail silently - cache is optional
    
    thread = threading.Thread(target=_get, daemon=True)
    thread.start()
    thread.join(timeout=0.3)  # Max 300ms wait
    
    return result[0]


def set_cache(key: str, value: Any, expire_seconds: int = 300):
    """
    Set value in Redis cache with expiration.
    Default: 5 minutes (300 seconds)
    Uses threading with timeout to prevent blocking.
    """
    def _set():
        try:
            redis_client.setex(
                key,
                timedelta(seconds=expire_seconds),
                json.dumps(value)
            )
        except Exception:
            pass  # Fail silently - cache is optional
    
    thread = threading.Thread(target=_set, daemon=True)
    thread.start()
    thread.join(timeout=0.3)  # Max 300ms wait
    return True


def delete_cache(key: str):
    """
    Delete a key from cache.
    """
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def get_current_price_cached(symbol: str):
    """
    Get current price with 5-minute cache.
    """
    cache_key = f"price:current:{symbol}"
    cached = get_cache(cache_key)
    
    if cached:
        print(f"Cache hit for {symbol}")
        return cached
    
    print(f"Cache miss for {symbol}, fetching from API...")
    from services.data_fetcher import get_current_price
    data = get_current_price(symbol)
    
    set_cache(cache_key, data, expire_seconds=300)
    return data


def get_historical_data_cached(symbol: str, period: str):
    """
    Get historical data with 1-hour cache.
    """
    cache_key = f"history:{symbol}:{period}"
    cached = get_cache(cache_key)
    
    if cached:
        print(f"Cache hit for {symbol} ({period})")
        return cached
    
    print(f"Cache miss for {symbol} ({period}), fetching from API...")
    from services.data_fetcher import get_historical_data
    data = get_historical_data(symbol, period)
    
    set_cache(cache_key, data, expire_seconds=3600)
    return data


def clear_stock_cache(symbol: str):
    """
    Clear all cache entries for a specific stock.
    """
    pattern = f"*:{symbol}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
    print(f"Cleared cache for {symbol}")


def cache_prediction(symbol: str, predicted_price: float, days_ahead: int = 1):
    """
    Cache ML prediction for a stock.
    Cached for 1 hour (predictions are computationally expensive).
    
    Args:
        symbol: Stock symbol
        predicted_price: Predicted price
        days_ahead: Days ahead predicted
    """
    from datetime import datetime
    
    cache_key = f"prediction:{symbol}:{days_ahead}"
    data = {
        'symbol': symbol,
        'predicted_price': predicted_price,
        'days_ahead': days_ahead,
        'cached_at': datetime.now().isoformat()
    }
    
    # Cache for 1 hour
    set_cache(cache_key, data, expire_seconds=3600)


def get_cached_prediction(symbol: str, days_ahead: int = 1):
    """
    Get cached ML prediction.
    
    Args:
        symbol: Stock symbol
        days_ahead: Days ahead to predict
        
    Returns:
        Cached prediction or None
    """
    cache_key = f"prediction:{symbol}:{days_ahead}"
    return get_cache(cache_key)
