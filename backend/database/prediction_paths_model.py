"""
PREDICTION PATHS MODEL

Stores intermediate predictions for drawing prediction trajectories on graphs.
Instead of just storing the final prediction, we store all days in between.

Example for 1-month prediction:
- Day 1: $183.20
- Day 2: $183.95
- Day 3: $184.50
- ...
- Day 21: $190.30

This allows drawing smooth prediction curves on the frontend.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.db_models import Base
from datetime import datetime


class LSTMPredictionPath(Base):
    """
    Stores daily prediction points for creating prediction graphs.
    Each horizon gets multiple rows - one for each day in the forecast.
    """
    __tablename__ = "lstm_prediction_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)  # When prediction was made
    horizon_type = Column(String, nullable=False, index=True)   # '1day', '1week', '1month', '6months'
    day_offset = Column(Integer, nullable=False)                # Days from prediction_date (1, 2, 3... N)
    target_date = Column(Date, nullable=False)                  # Specific date for this prediction
    predicted_price = Column(Float, nullable=False)             # Predicted price for this date
    
    # Metadata
    confidence_score = Column(Float)                            # Decays with day_offset
    model_version = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_prediction_path_lookup', 'stock_id', 'prediction_date', 'horizon_type'),
    )
    
    def __repr__(self):
        return f"<PredictionPath(stock_id={self.stock_id}, horizon={self.horizon_type}, day={self.day_offset}, price=${self.predicted_price:.2f})>"


class TransformerPredictionPath(Base):
    """
    Same as LSTMPredictionPath but for Transformer models.
    """
    __tablename__ = "transformer_prediction_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    horizon_type = Column(String, nullable=False, index=True)
    day_offset = Column(Integer, nullable=False)
    target_date = Column(Date, nullable=False)
    predicted_price = Column(Float, nullable=False)
    confidence_score = Column(Float)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock")
    
    __table_args__ = (
        Index('idx_transformer_path_lookup', 'stock_id', 'prediction_date', 'horizon_type'),
    )
    
    def __repr__(self):
        return f"<TransformerPredictionPath(stock_id={self.stock_id}, horizon={self.horizon_type}, day={self.day_offset}, price=${self.predicted_price:.2f})>"
