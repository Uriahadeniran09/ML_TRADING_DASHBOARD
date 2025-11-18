"""
DATABASE MODELS - Defines the PostgreSQL table structure
- Stock: stores symbol and company name (50 stocks)
- StockPrice: stores OHLCV data (24,950 records currently)
- Prediction: stores ML model predictions (future use)
- These are the actual database tables
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """
    Stores basic stock information
    """
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)  # e.g., "AAPL"
    name = Column(String)  # e.g., "Apple Inc."
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship: one stock has many prices
    prices = relationship("StockPrice", back_populates="stock")
    predictions = relationship("Prediction", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class StockPrice(Base):
    """
    Stores daily stock price data (OHLCV)
    """
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship: many prices belong to one stock
    stock = relationship("Stock", back_populates="prices")
    
    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"


class Prediction(Base):
    """
    Stores ML model predictions for stock closing prices
    """
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False)  # Date we made the prediction
    target_date = Column(Date, nullable=False)  # Date we're predicting for
    predicted_price = Column(Float, nullable=False)  # Predicted CLOSING price
    actual_price = Column(Float)  # Actual CLOSING price (filled in later)
    model_name = Column(String)  # e.g., "LSTM", "Random Forest"
    confidence = Column(Float)  # Model confidence score (0-1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship: many predictions belong to one stock
    stock = relationship("Stock", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(stock_id={self.stock_id}, predicted_price={self.predicted_price})>"
