"""
DATA FETCHER SERVICE - External API integration
- Fetches live stock prices from Polygon.io API
- get_current_price() - latest trading day OHLCV data
- get_historical_data() - time series data (1d to 5y)
- Used by: API endpoints, populate_db.py, daily_update.py
- Rate limit: 5 requests/minute on free tier
"""
import requests
from datetime import datetime, timedelta
import os


POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "Ap9RmA9ycqGkmLS6E3HvpyU5UeVDmseQ")
BASE_URL = "https://api.polygon.io"


def get_current_price(symbol: str) -> dict:
    """
    Get the most recent trading day's price data using Polygon.io
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dictionary with latest trading day's price data
    """
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/v1/open-close/{symbol}/{yesterday}"
        params = {"apiKey": POLYGON_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "NOT_FOUND":
            return {
                "symbol": symbol.upper(),
                "error": "Invalid symbol or no data available",
                "status": "error"
            }
        
        if data.get("status") == "ERROR":
            return {
                "symbol": symbol.upper(),
                "error": data.get("message", "API error"),
                "status": "error"
            }
        
        return {
            "symbol": symbol.upper(),
            "date": data.get("from"),
            "open": round(data.get("open", 0), 2),
            "high": round(data.get("high", 0), 2),
            "low": round(data.get("low", 0), 2),
            "close": round(data.get("close", 0), 2),
            "volume": data.get("volume", 0),
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "error": f"Failed to fetch data: {str(e)}",
            "status": "error"
        }


def get_historical_data(symbol: str, period: str = "1mo") -> dict:
    """
    Get historical stock data from Polygon.io
    
    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 1w, 1mo, 3mo, 6mo, 1y, 2y, 5y)
    
    Returns:
        Dictionary with historical price data
    """
    try:
        period_days = {
            "1d": 1, "1w": 7, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_days.get(period, 30)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {
            "apiKey": POLYGON_API_KEY,
            "adjusted": "true",
            "sort": "desc"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "ERROR":
            error_msg = data.get("error", data.get("message", "API error"))
            return {
                "symbol": symbol.upper(),
                "error": f"API Error: {error_msg}",
                "status": "error",
                "response": data
            }
        
        if data.get("resultsCount", 0) == 0:
            return {
                "symbol": symbol.upper(),
                "error": f"No data available for this period. Response: {data}",
                "status": "error",
                "response": data
            }
        
        results = data.get("results", [])
        
        data_list = []
        for item in results:
            timestamp_ms = item.get("t")
            date = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
            
            data_list.append({
                "date": date,
                "open": round(item.get("o", 0), 2),
                "high": round(item.get("h", 0), 2),
                "low": round(item.get("l", 0), 2),
                "close": round(item.get("c", 0), 2),
                "volume": int(item.get("v", 0))
            })
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "data": data_list,
            "count": len(data_list),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "error": str(e),
            "status": "error"
        }
