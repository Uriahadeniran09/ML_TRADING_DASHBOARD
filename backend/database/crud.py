"""
DATABASE CRUD OPERATIONS - Create/Read/Update/Delete functions
- Directly interacts with PostgreSQL database
- Handles stock prices, predictions, and stock records
- Used by scripts (populate_db.py, daily_update.py) to save data
- Different from config/stocks.py which is just a static list
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from .models import Stock, StockPrice, Prediction


def get_or_create_stock(db: Session, symbol: str, name: Optional[str] = None) -> Stock:
    """
    Get existing stock or create new one if it doesn't exist.
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        stock = Stock(symbol=symbol, name=name or symbol)
        db.add(stock)
        db.commit()
        db.refresh(stock)
    return stock


def add_stock_price(
    db: Session,
    symbol: str,
    date: datetime,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: int
) -> StockPrice:
    """
    Add a new stock price record.
    """
    try:
        stock = get_or_create_stock(db, symbol)
        
        existing = db.query(StockPrice).filter(
            StockPrice.stock_id == stock.id,
            StockPrice.date == date
        ).first()
        
        if existing:
            existing.open = open_price
            existing.high = high
            existing.low = low
            existing.close = close
            existing.volume = volume
            db.commit()
            return existing
        else:
            price = StockPrice(
                stock_id=stock.id,
                date=date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            )
            db.add(price)
            db.commit()
            db.refresh(price)
            return price
    except Exception as e:
        db.rollback()
        raise e


def add_prediction(
    db: Session,
    symbol: str,
    prediction_date: datetime,
    target_date: datetime,
    predicted_price: float,
    model_name: str,
    confidence: Optional[float] = None,
    actual_price: Optional[float] = None
) -> Prediction:
    """
    Add a new prediction record.
    """
    stock = get_or_create_stock(db, symbol)
    
    existing = db.query(Prediction).filter(
        Prediction.stock_id == stock.id,
        Prediction.prediction_date == prediction_date,
        Prediction.target_date == target_date,
        Prediction.model_name == model_name
    ).first()
    
    if existing:
        existing.predicted_price = predicted_price
        existing.actual_price = actual_price
        existing.confidence = confidence
        db.commit()
        return existing
    
    prediction = Prediction(
        stock_id=stock.id,
        prediction_date=prediction_date,
        target_date=target_date,
        predicted_price=predicted_price,
        actual_price=actual_price,
        model_name=model_name,
        confidence=confidence
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_stock_prices(db: Session, symbol: str, limit: int = 100):
    """
    Get historical prices for a stock.
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return []
    
    return db.query(StockPrice).filter(
        StockPrice.stock_id == stock.id
    ).order_by(StockPrice.date.desc()).limit(limit).all()


def get_latest_price(db: Session, symbol: str) -> Optional[StockPrice]:
    """
    Get the most recent price for a stock.
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return None
    
    return db.query(StockPrice).filter(
        StockPrice.stock_id == stock.id
    ).order_by(StockPrice.date.desc()).first()
