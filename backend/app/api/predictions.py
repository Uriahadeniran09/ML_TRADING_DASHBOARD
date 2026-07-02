"""
PREDICTIONS API ROUTER - Modular endpoint set for ML predictions
Handles all prediction-related endpoints included in main.py

Endpoints:
- GET /api/predictions/stocks - Get all stocks with predictions
- GET /api/predictions/{symbol} - Get all prediction summaries for a stock
- GET /api/predictions/{symbol}/path - Get detailed prediction path for graphs
- GET /api/predictions/{symbol}/latest - Get latest prediction for each horizon
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db import get_db
from database.db_models import LSTMPrediction, Stock
from database.prediction_paths_model import LSTMPredictionPath

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/stocks")
def get_stocks_with_predictions(db: Session = Depends(get_db)):
    """
    Get list of all stocks that have predictions available.
    
    Returns:
        List of stocks with prediction counts
    """
    # Get unique stocks from predictions
    stocks_with_preds = db.query(
        LSTMPrediction.stock_id,
        func.count(LSTMPrediction.id).label('prediction_count'),
        func.max(LSTMPrediction.prediction_date).label('latest_prediction')
    ).group_by(LSTMPrediction.stock_id).all()
    
    result = []
    for stock_id, pred_count, latest_date in stocks_with_preds:
        # Get stock info
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        
        if stock:
            result.append({
                "symbol": stock.symbol,
                "name": stock.name,
                "prediction_count": pred_count,
                "latest_prediction_date": str(latest_date) if latest_date else None,
                "has_paths": True  # We always generate paths now
            })
    
    return {
        "stocks": result,
        "count": len(result)
    }


@router.get("/{symbol}")
def get_predictions_summary(
    symbol: str,
    prediction_date: Optional[str] = Query(None, description="Filter by prediction date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get all prediction summaries for a stock.
    Returns the 4 horizon predictions (1day, 1week, 1month, 6months).
    
    Args:
        symbol: Stock symbol (e.g., AAPL)
        prediction_date: Optional - filter by specific prediction date
        
    Returns:
        All prediction summaries with final prices and confidence
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Build query
    query = db.query(LSTMPrediction).filter(
        LSTMPrediction.stock_id == stock.id
    )
    
    # Filter by date if provided
    if prediction_date:
        try:
            pred_date = datetime.strptime(prediction_date, "%Y-%m-%d").date()
            query = query.filter(LSTMPrediction.prediction_date == pred_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Get latest predictions only
        latest_date = db.query(
            func.max(LSTMPrediction.prediction_date)
        ).filter(LSTMPrediction.stock_id == stock.id).scalar()
        
        if latest_date:
            query = query.filter(LSTMPrediction.prediction_date == latest_date)
    
    predictions = query.order_by(LSTMPrediction.horizon_days).all()
    
    if not predictions:
        raise HTTPException(
            status_code=404, 
            detail=f"No predictions found for {symbol}"
        )
    
    return {
        "symbol": symbol.upper(),
        "stock_name": stock.name,
        "prediction_date": str(predictions[0].prediction_date),
        "predictions": [
            {
                "horizon_type": {1: "1day", 5: "1week", 21: "1month", 126: "6months"}.get(pred.horizon_days, f"{pred.horizon_days}day"),
                "horizon_days": pred.horizon_days,
                "target_date": str(pred.target_date),
                "predicted_price": round(pred.predicted_price, 2),
                "confidence_score": round(pred.confidence_score, 4) if pred.confidence_score else 0.5,
                "created_at": pred.created_at.isoformat() if pred.created_at else None
            }
            for pred in predictions
        ],
        "count": len(predictions)
    }


@router.get("/{symbol}/path")
def get_prediction_path(
    symbol: str,
    horizon: str = Query(..., description="Horizon type: 1day, 1week, 1month, or 6months"),
    prediction_date: Optional[str] = Query(None, description="Filter by prediction date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get detailed prediction path for graphing.
    Returns all intermediate predictions (e.g., 21 points for 1month, 126 for 6months).
    
    Args:
        symbol: Stock symbol (e.g., AAPL)
        horizon: Horizon type (1day, 1week, 1month, 6months)
        prediction_date: Optional - filter by specific prediction date
        
    Returns:
        Complete prediction path with dates, prices, and confidence for each day
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Validate horizon
    valid_horizons = ['1day', '1week', '1month', '6months']
    if horizon not in valid_horizons:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid horizon. Must be one of: {', '.join(valid_horizons)}"
        )
    
    # Build query
    query = db.query(LSTMPredictionPath).filter(
        LSTMPredictionPath.stock_id == stock.id,
        LSTMPredictionPath.horizon_type == horizon
    )
    
    # Filter by date if provided
    if prediction_date:
        try:
            pred_date = datetime.strptime(prediction_date, "%Y-%m-%d").date()
            query = query.filter(LSTMPredictionPath.prediction_date == pred_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Get latest predictions only
        latest_date = db.query(
            func.max(LSTMPredictionPath.prediction_date)
        ).filter(
            LSTMPredictionPath.stock_id == stock.id,
            LSTMPredictionPath.horizon_type == horizon
        ).scalar()
        
        if latest_date:
            query = query.filter(LSTMPredictionPath.prediction_date == latest_date)
    
    # Get path points ordered by day
    path_points = query.order_by(LSTMPredictionPath.day_offset).all()
    
    if not path_points:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction path found for {symbol} with horizon {horizon}"
        )
    
    # Map horizon to days
    horizon_days_map = {'1day': 1, '1week': 5, '1month': 21, '6months': 126}
    
    return {
        "symbol": symbol.upper(),
        "stock_name": stock.name,
        "horizon_type": horizon,
        "horizon_days": horizon_days_map.get(horizon, len(path_points)),
        "prediction_date": str(path_points[0].prediction_date),
        "path": [
            {
                "day_offset": point.day_offset,
                "target_date": str(point.target_date),
                "predicted_price": round(point.predicted_price, 2),
                "confidence_score": round(point.confidence_score, 4) if point.confidence_score else 0.5
            }
            for point in path_points
        ],
        "point_count": len(path_points)
    }


@router.get("/{symbol}/latest")
def get_latest_predictions(symbol: str, db: Session = Depends(get_db)):
    """
    Get the latest prediction for each horizon (quick summary).
    
    Args:
        symbol: Stock symbol (e.g., AAPL)
        
    Returns:
        Latest predictions for all 4 horizons with key metrics
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get latest prediction date
    latest_date = db.query(
        func.max(LSTMPrediction.prediction_date)
    ).filter(LSTMPrediction.stock_id == stock.id).scalar()
    
    if not latest_date:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for {symbol}"
        )
    
    # Get all predictions for that date
    predictions = db.query(LSTMPrediction).filter(
        LSTMPrediction.stock_id == stock.id,
        LSTMPrediction.prediction_date == latest_date
    ).order_by(LSTMPrediction.horizon_days).all()
    
    # Get current price for comparison
    from database.crud import get_latest_price
    current = get_latest_price(db, symbol.upper())
    current_price = current.close if current else None
    
    result = {
        "symbol": symbol.upper(),
        "stock_name": stock.name,
        "prediction_date": str(latest_date),
        "current_price": round(current_price, 2) if current_price else None,
        "current_price_date": str(current.date) if current else None,
        "predictions": []
    }
    
    for pred in predictions:
        price_change = None
        price_change_pct = None
        
        if current_price:
            price_change = pred.predicted_price - current_price
            price_change_pct = (price_change / current_price) * 100
        
        horizon_map = {1: "1day", 5: "1week", 21: "1month", 126: "6months"}
        result["predictions"].append({
            "horizon_type": horizon_map.get(pred.horizon_days, f"{pred.horizon_days}day"),
            "horizon_days": pred.horizon_days,
            "target_date": str(pred.target_date),
            "predicted_price": round(pred.predicted_price, 2),
            "confidence_score": round(pred.confidence_score, 4),
            "price_change": round(price_change, 2) if price_change else None,
            "price_change_pct": round(price_change_pct, 2) if price_change_pct else None,
            "direction": "up" if price_change and price_change > 0 else "down" if price_change and price_change < 0 else "neutral"
        })
    
    return result
