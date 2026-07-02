"""
RISK CALCULATOR SERVICE - Portfolio risk metrics
Calculates basic risk metrics for stocks and portfolios
"""

import numpy as np
import pandas as pd
from typing import List, Dict


def calculate_volatility(prices: List[float], annualize: bool = True) -> float:
    """
    Calculate volatility (standard deviation of returns)
    
    Args:
        prices: List of stock prices
        annualize: If True, annualize the volatility (assumes daily data)
        
    Returns:
        Volatility as a decimal (e.g., 0.25 = 25% volatility)
        
    Example:
        prices = [100, 102, 101, 103, 105]
        volatility = calculate_volatility(prices)  # Returns annualized volatility
    """
    if len(prices) < 2:
        return 0.0
    
    # Convert to pandas Series for easier calculation
    prices_series = pd.Series(prices)
    
    # Calculate daily returns: (price_today - price_yesterday) / price_yesterday
    returns = prices_series.pct_change().dropna()
    
    # Calculate standard deviation of returns
    volatility = returns.std()
    
    # Annualize if requested (multiply by sqrt of 252 trading days)
    if annualize:
        volatility = volatility * np.sqrt(252)
    
    return float(volatility)


def calculate_sharpe_ratio(prices: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe Ratio - measures risk-adjusted return
    Higher is better (> 1 is good, > 2 is very good, > 3 is excellent)
    
    Formula: (Average Return - Risk Free Rate) / Volatility
    
    Args:
        prices: List of stock prices
        risk_free_rate: Annual risk-free rate (default 2% = 0.02)
        
    Returns:
        Sharpe ratio (unitless number)
        
    Example:
        prices = [100, 102, 101, 103, 105]
        sharpe = calculate_sharpe_ratio(prices, risk_free_rate=0.02)
    """
    if len(prices) < 2:
        return 0.0
    
    # Convert to pandas Series
    prices_series = pd.Series(prices)
    
    # Calculate daily returns
    returns = prices_series.pct_change().dropna()
    
    # Calculate annualized average return
    avg_return = returns.mean() * 252
    
    # Calculate annualized volatility
    volatility = returns.std() * np.sqrt(252)
    
    # Avoid division by zero
    if volatility == 0:
        return 0.0
    
    # Sharpe Ratio = (Return - Risk Free Rate) / Volatility
    sharpe_ratio = (avg_return - risk_free_rate) / volatility
    
    return float(sharpe_ratio)


def calculate_portfolio_risk(holdings_data: List[Dict]) -> Dict:
    """
    Calculate risk metrics for an entire portfolio
    
    Args:
        holdings_data: List of holdings with price history
                      Each holding should have:
                      {
                          "symbol": "AAPL",
                          "shares": 10,
                          "prices": [150, 152, 151, ...]  # Historical prices
                      }
    
    Returns:
        Dictionary with portfolio-level risk metrics
        
    Example:
        holdings = [
            {"symbol": "AAPL", "shares": 10, "prices": [150, 152, 151, 153]},
            {"symbol": "GOOGL", "shares": 5, "prices": [2800, 2820, 2810, 2830]}
        ]
        risk = calculate_portfolio_risk(holdings)
    """
    if not holdings_data:
        return {
            "portfolio_volatility": 0.0,
            "portfolio_sharpe": 0.0,
            "total_holdings": 0
        }
    
    # Calculate individual volatilities and Sharpe ratios
    stock_metrics = []
    for holding in holdings_data:
        vol = calculate_volatility(holding["prices"])
        sharpe = calculate_sharpe_ratio(holding["prices"])
        stock_metrics.append({
            "symbol": holding["symbol"],
            "volatility": vol,
            "sharpe_ratio": sharpe,
            "shares": holding.get("shares", 0)
        })
    
    # Simple portfolio volatility (average of individual volatilities)
    # Note: This is simplified - proper calculation requires correlation matrix
    avg_volatility = sum(m["volatility"] for m in stock_metrics) / len(stock_metrics)
    avg_sharpe = sum(m["sharpe_ratio"] for m in stock_metrics) / len(stock_metrics)
    
    return {
        "portfolio_volatility": avg_volatility,
        "portfolio_sharpe": avg_sharpe,
        "total_holdings": len(holdings_data),
        "individual_stocks": stock_metrics
    }
