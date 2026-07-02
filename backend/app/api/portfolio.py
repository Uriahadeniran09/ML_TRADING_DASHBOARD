"""
PORTFOLIO API ROUTER - Portfolio management endpoints
- Create and manage virtual portfolios
- Buy/sell stocks
- View holdings and transaction history
- Risk metrics

Each user gets $100,000 virtual cash to trade with the top 50 stocks
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
import sys
import os
import logging
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db import get_db
from database.db_models import Portfolio, PortfolioHolding, Transaction, Stock, StockPrice

logger = logging.getLogger(__name__)


# Request/Response models
class BuyStockRequest(BaseModel):
    symbol: str
    shares: Optional[float] = None
    amount: Optional[float] = None


class SellStockRequest(BaseModel):
    symbol: str
    shares: Optional[float] = None
    amount: Optional[float] = None
from services.portfolio_manager import (
    create_portfolio,
    buy_stock,
    sell_stock,
    get_portfolio_summary,
)
from sqlalchemy import func

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/create")
def create_new_portfolio(
    user_id: str,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new virtual portfolio for a user with $100,000 starting cash.
    
    Args:
        user_id: Unique user identifier
        name: Optional portfolio name (defaults to "My Portfolio")
        
    Returns:
        Created portfolio with starting $100k cash
    """
    try:
        # Check if user already has a portfolio
        existing = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if existing:
            return {
                "success": True,
                "message": "Portfolio already exists for this user",
                "portfolio": {
                    "id": existing.id,
                    "user_id": existing.user_id,
                    "name": existing.name,
                    "cash_balance": existing.cash_balance,
                    "total_invested": existing.total_invested,
                    "created_at": str(existing.created_at)
                }
            }
        
        portfolio = create_portfolio(db, user_id, name or "My Portfolio")
        
        return {
            "success": True,
            "portfolio": {
                "id": portfolio.id,
                "user_id": portfolio.user_id,
                "name": portfolio.name,
                "cash_balance": portfolio.cash_balance,
                "total_invested": portfolio.total_invested,
                "created_at": str(portfolio.created_at)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
def get_portfolio_by_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get portfolio for a user, creating one if it doesn't exist.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        Portfolio details with current holdings and cash balance
    """
    try:
        # Try to get existing portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        
        # If no portfolio exists, create one
        if not portfolio:
            portfolio = create_portfolio(db, user_id, "My Portfolio")
        
        # Get holdings
        holdings = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio.id
        ).all()
        
        # Get current prices for holdings
        holdings_data = []
        for holding in holdings:
            stock = holding.stock
            latest_price = db.query(StockPrice).filter(
                StockPrice.stock_id == stock.id
            ).order_by(StockPrice.date.desc()).first()
            
            current_price = latest_price.close if latest_price else holding.average_cost
            current_value = holding.shares * current_price
            gain_loss = current_value - (holding.shares * holding.average_cost)
            gain_loss_pct = (gain_loss / (holding.shares * holding.average_cost) * 100) if holding.average_cost > 0 else 0
            
            holdings_data.append({
                "id": holding.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "shares": holding.shares,
                "average_cost": round(holding.average_cost, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_pct": round(gain_loss_pct, 2),
            })
        
        # Calculate portfolio totals
        total_value = sum([h["current_value"] for h in holdings_data])
        total_cost = sum([h["shares"] * h["average_cost"] for h in holdings_data])
        portfolio_gain_loss = total_value - total_cost
        portfolio_gain_loss_pct = (portfolio_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "portfolio": {
                "id": portfolio.id,
                "user_id": portfolio.user_id,
                "name": portfolio.name,
                "cash_balance": round(portfolio.cash_balance, 2),
                "total_invested": round(portfolio.total_invested, 2),
                "total_stock_value": round(total_value, 2),
                "portfolio_value": round(portfolio.cash_balance + total_value, 2),
                "gain_loss": round(portfolio_gain_loss, 2),
                "gain_loss_pct": round(portfolio_gain_loss_pct, 2),
                "created_at": str(portfolio.created_at)
            },
            "holdings": holdings_data,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Get portfolio by ID with all holdings and current valuation.
    
    Args:
        portfolio_id: Portfolio ID
        
    Returns:
        Portfolio details with holdings and current values
    """
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get holdings
        holdings = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio.id
        ).all()
        
        # Get current prices for holdings
        holdings_data = []
        for holding in holdings:
            stock = holding.stock
            latest_price = db.query(StockPrice).filter(
                StockPrice.stock_id == stock.id
            ).order_by(StockPrice.date.desc()).first()
            
            current_price = latest_price.close if latest_price else holding.average_cost
            current_value = holding.shares * current_price
            gain_loss = current_value - (holding.shares * holding.average_cost)
            gain_loss_pct = (gain_loss / (holding.shares * holding.average_cost) * 100) if holding.average_cost > 0 else 0
            
            holdings_data.append({
                "id": holding.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "shares": holding.shares,
                "average_cost": round(holding.average_cost, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_pct": round(gain_loss_pct, 2),
            })
        
        # Calculate portfolio totals
        total_value = sum([h["current_value"] for h in holdings_data])
        total_cost = sum([h["shares"] * h["average_cost"] for h in holdings_data])
        portfolio_gain_loss = total_value - total_cost
        portfolio_gain_loss_pct = (portfolio_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "portfolio": {
                "id": portfolio.id,
                "user_id": portfolio.user_id,
                "name": portfolio.name,
                "cash_balance": round(portfolio.cash_balance, 2),
                "total_invested": round(portfolio.total_invested, 2),
                "total_stock_value": round(total_value, 2),
                "portfolio_value": round(portfolio.cash_balance + total_value, 2),
                "gain_loss": round(portfolio_gain_loss, 2),
                "gain_loss_pct": round(portfolio_gain_loss_pct, 2),
                "created_at": str(portfolio.created_at)
            },
            "holdings": holdings_data,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{portfolio_id}/buy")
def buy_stock_endpoint(
    portfolio_id: int,
    request: BuyStockRequest,
    db: Session = Depends(get_db)
):
    """
    Buy shares of a stock using virtual cash.
    
    You must provide EITHER shares OR amount, not both.
    
    Args:
        portfolio_id: Portfolio ID
        request: BuyStockRequest with symbol, shares, and/or amount
        
    Returns:
        Transaction details and updated portfolio
        
    Examples:
        POST /api/portfolio/1/buy
        {
          "symbol": "AAPL",
          "shares": 10
        }
        
        POST /api/portfolio/1/buy
        {
          "symbol": "AAPL",
          "amount": 1000
        }
    """
    try:
        result = buy_stock(db, portfolio_id, request.symbol, request.shares, request.amount)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buying stock: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{portfolio_id}/sell")
def sell_stock_endpoint(
    portfolio_id: int,
    request: SellStockRequest,
    db: Session = Depends(get_db)
):
    """
    Sell shares of a stock from your portfolio.
    
    You must provide EITHER shares OR amount, not both.
    
    Args:
        portfolio_id: Portfolio ID
        request: SellStockRequest with symbol, shares, and/or amount
        
    Returns:
        Transaction details and updated portfolio
        
    Examples:
        POST /api/portfolio/1/sell
        {
          "symbol": "AAPL",
          "shares": 5
        }
        
        POST /api/portfolio/1/sell
        {
          "symbol": "AAPL",
          "amount": 500
        }
    """
    try:
        result = sell_stock(db, portfolio_id, request.symbol, request.shares, request.amount)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selling stock: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{portfolio_id}/transactions")
def get_transactions(
    portfolio_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        limit: Maximum number of transactions to return (default 50)
        
    Returns:
        List of transactions ordered by most recent first
    """
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        transactions = db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        ).order_by(Transaction.transaction_date.desc()).limit(limit).all()
        
        transactions_data = []
        for txn in transactions:
            stock = db.query(Stock).filter(Stock.id == txn.stock_id).first()
            if stock:
                transactions_data.append({
                    "id": txn.id,
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "type": txn.transaction_type,
                    "shares": txn.shares,
                    "price_per_share": round(txn.price_per_share, 2),
                    "total_amount": round(txn.total_amount, 2),
                    "created_at": str(txn.transaction_date)
                })
        
        return {
            "portfolio_id": portfolio_id,
            "transactions": transactions_data,
            "count": len(transactions_data),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions for portfolio {portfolio_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")
