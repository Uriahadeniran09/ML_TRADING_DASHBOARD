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
    lstm_predictions = relationship("LSTMPrediction", back_populates="stock")
    transformer_predictions = relationship("TransformerPrediction", back_populates="stock")
    
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
    Stores ML model predictions for stock closing prices (LEGACY - use LSTMPrediction or TransformerPrediction)
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


class LSTMPrediction(Base):
    """
    Stores LSTM model predictions for stock prices with multi-horizon support
    """
    __tablename__ = "lstm_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)  # Date we made the prediction
    target_date = Column(Date, nullable=False, index=True)  # Date we're predicting for
    horizon_days = Column(Integer, nullable=False, index=True)  # Forecast horizon (1, 5, 21, 126)
    predicted_price = Column(Float, nullable=False)  # Predicted closing price
    predicted_change = Column(Float)  # Predicted change in dollars
    predicted_change_pct = Column(Float)  # Predicted change in percentage
    actual_price = Column(Float)  # Actual closing price (filled in later)
    
    # Model metadata
    model_version = Column(String)  # e.g., "v1.0", "2024-11-18"
    sequence_length = Column(Integer)  # Number of days used (e.g., 60)
    features_used = Column(String)  # JSON string of features used
    
    # Confidence metrics
    confidence_score = Column(Float)  # Overall confidence (0-1)
    validation_mse = Column(Float)  # Model's validation MSE
    validation_r2 = Column(Float)  # Model's R² score
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="lstm_predictions")
    
    def __repr__(self):
        return f"<LSTMPrediction(stock_id={self.stock_id}, horizon={self.horizon_days}d, target_date='{self.target_date}', predicted_price={self.predicted_price})>"


class TransformerPrediction(Base):
    """
    Stores Transformer model predictions for stock prices
    """
    __tablename__ = "transformer_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)  # Date we made the prediction
    target_date = Column(Date, nullable=False, index=True)  # Date we're predicting for
    predicted_price = Column(Float, nullable=False)  # Predicted closing price
    predicted_change = Column(Float)  # Predicted change in dollars
    predicted_change_pct = Column(Float)  # Predicted change in percentage
    actual_price = Column(Float)  # Actual closing price (filled in later)
    
    # Model metadata
    model_version = Column(String)  # e.g., "v1.0", "2024-11-18"
    sequence_length = Column(Integer)  # Number of days used (e.g., 60)
    features_used = Column(String)  # JSON string of features used
    num_attention_heads = Column(Integer)  # Transformer specific: number of attention heads
    num_layers = Column(Integer)  # Transformer specific: number of layers
    
    # Confidence metrics
    confidence_score = Column(Float)  # Overall confidence (0-1)
    validation_mse = Column(Float)  # Model's validation MSE
    validation_r2 = Column(Float)  # Model's R² score
    attention_weights = Column(String)  # JSON string of attention weights (optional)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="transformer_predictions")
    
    def __repr__(self):
        return f"<TransformerPrediction(stock_id={self.stock_id}, target_date='{self.target_date}', predicted_price={self.predicted_price})>"


class Portfolio(Base):
    """
    Stores user's virtual portfolio - each user gets $100,000 virtual cash
    """
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # User identifier (session ID, email, etc.)
    name = Column(String, default="My Portfolio")  # Portfolio name
    cash_balance = Column(Float, default=100000.0)  # Available cash (starts at $100k)
    total_invested = Column(Float, default=0.0)  # Total amount invested in stocks
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(user_id='{self.user_id}', cash={self.cash_balance}, invested={self.total_invested})>"


class PortfolioHolding(Base):
    """
    Stores current stock holdings in a portfolio
    """
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    shares = Column(Float, nullable=False)  # Number of shares owned
    average_cost = Column(Float, nullable=False)  # Average price paid per share
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    stock = relationship("Stock")
    
    def __repr__(self):
        return f"<PortfolioHolding(portfolio_id={self.portfolio_id}, stock_id={self.stock_id}, shares={self.shares})>"


class Transaction(Base):
    """
    Stores all buy/sell transactions for audit trail and history
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    transaction_type = Column(String, nullable=False)  # "BUY" or "SELL"
    shares = Column(Float, nullable=False)  # Number of shares bought/sold
    price_per_share = Column(Float, nullable=False)  # Price at time of transaction
    total_amount = Column(Float, nullable=False)  # shares * price_per_share
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    stock = relationship("Stock")
    
    def __repr__(self):
        return f"<Transaction(type='{self.transaction_type}', stock_id={self.stock_id}, shares={self.shares})>"
