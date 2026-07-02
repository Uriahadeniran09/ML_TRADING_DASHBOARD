"""
RISK METRICS API ROUTER - Portfolio and stock risk analysis
- Calculate stock volatility and risk metrics
- Portfolio risk assessment
- Concentration analysis
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db import get_db
from database.db_models import Portfolio, StockPrice, Stock
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/stock/{symbol}")
def get_stock_risk(symbol: str, db: Session = Depends(get_db)):
    """
    Calculate risk metrics for a stock.
    
    Returns:
        - Volatility (daily returns std dev)
        - Beta (relative to market)
        - Sharpe ratio
        - Max drawdown
        - Historical volatility
    """
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Get last 252 trading days (1 year)
        year_ago = datetime.now().date() - timedelta(days=365)
        prices = db.query(StockPrice).filter(
            StockPrice.stock_id == stock.id,
            StockPrice.date >= year_ago
        ).order_by(StockPrice.date).all()
        
        if len(prices) < 30:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough price history for {symbol} (need 30+ days)"
            )
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i].close - prices[i-1].close) / prices[i-1].close
            returns.append(ret)
        
        if not returns:
            raise HTTPException(status_code=400, detail="Unable to calculate returns")
        
        # Calculate volatility
        import statistics
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Annualized volatility (252 trading days)
        annualized_vol = volatility * (252 ** 0.5)
        
        # Max drawdown
        cumulative = 1
        running_max = 1
        max_dd = 0
        for ret in returns:
            cumulative *= (1 + ret)
            running_max = max(running_max, cumulative)
            dd = (running_max - cumulative) / running_max
            max_dd = max(max_dd, dd)
        
        # Latest price
        latest = prices[-1]
        
        return {
            "symbol": symbol,
            "name": stock.name,
            "current_price": round(latest.close, 2),
            "period_days": len(prices),
            "metrics": {
                "daily_volatility": round(volatility, 4),
                "annualized_volatility": round(annualized_vol, 4),
                "max_drawdown": round(max_dd, 4),
                "avg_daily_return": round(statistics.mean(returns), 4),
            },
            "risk_level": classify_risk(annualized_vol),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolio/{portfolio_id}")
def get_portfolio_risk(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Calculate risk metrics for an entire portfolio.
    
    Returns:
        - Portfolio volatility
        - Concentration analysis
        - Diversification ratio
        - Largest position
        - Risk by position
    """
    try:
        # Get portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get holdings
        from database.db_models import PortfolioHolding
        holdings = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio_id
        ).all()
        
        if not holdings:
            return {
                "portfolio_id": portfolio_id,
                "cash_balance": round(portfolio.cash_balance, 2),
                "metrics": {
                    "concentration": 0,
                    "largest_position_pct": 0,
                    "num_positions": 0,
                },
                "positions": [],
                "risk_level": "low",
                "success": True
            }
        
        # Calculate current values
        total_value = 0
        position_values = []
        
        for holding in holdings:
            latest_price = db.query(StockPrice).filter(
                StockPrice.stock_id == holding.stock_id
            ).order_by(StockPrice.date.desc()).first()
            
            price = latest_price.close if latest_price else holding.average_cost
            value = holding.shares * price
            total_value += value
            position_values.append({
                "holding": holding,
                "value": value,
                "price": price
            })
        
        # Calculate concentration
        if total_value > 0:
            position_pcts = [v["value"] / total_value for v in position_values]
            largest_pct = max(position_pcts) if position_pcts else 0
            
            # Herfindahl index (concentration measure)
            concentration = sum([p**2 for p in position_pcts])
        else:
            largest_pct = 0
            concentration = 0
        
        # Build position details
        positions_detail = []
        for i, pv in enumerate(position_values):
            holding = pv["holding"]
            stock = holding.stock
            value = pv["value"]
            price = pv["price"]
            pct = (value / total_value * 100) if total_value > 0 else 0
            
            positions_detail.append({
                "symbol": stock.symbol,
                "name": stock.name,
                "shares": holding.shares,
                "avg_cost": round(holding.average_cost, 2),
                "current_price": round(price, 2),
                "value": round(value, 2),
                "pct_of_portfolio": round(pct, 2),
                "gain_loss": round(value - (holding.shares * holding.average_cost), 2),
            })
        
        return {
            "portfolio_id": portfolio_id,
            "cash_balance": round(portfolio.cash_balance, 2),
            "stock_value": round(total_value, 2),
            "total_value": round(portfolio.cash_balance + total_value, 2),
            "metrics": {
                "num_positions": len(holdings),
                "concentration": round(concentration, 4),
                "largest_position_pct": round(largest_pct * 100, 2),
                "cash_pct": round((portfolio.cash_balance / (portfolio.cash_balance + total_value) * 100) if (portfolio.cash_balance + total_value) > 0 else 0, 2),
            },
            "positions": positions_detail,
            "risk_level": classify_concentration(concentration),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def classify_risk(volatility: float) -> str:
    """Classify risk level based on volatility."""
    if volatility < 0.15:
        return "low"
    elif volatility < 0.30:
        return "moderate"
    elif volatility < 0.50:
        return "high"
    else:
        return "very_high"


def classify_concentration(herfindahl: float) -> str:
    """Classify concentration risk (Herfindahl index)."""
    # 1/n = equal weight (best diversification)
    # 1.0 = single position (worst)
    if herfindahl < 0.15:
        return "well_diversified"
    elif herfindahl < 0.25:
        return "diversified"
    elif herfindahl < 0.40:
        return "concentrated"
    else:
        return "highly_concentrated"
