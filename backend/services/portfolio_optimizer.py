"""
PORTFOLIO OPTIMIZER SERVICE - Asset allocation optimization
Helps determine optimal weights for a portfolio of stocks
"""

import numpy as np
import pandas as pd
from typing import List, Dict


def calculate_portfolio_return(weights: List[float], returns: List[List[float]]) -> float:
    """
    Calculate expected portfolio return based on weights and historical returns
    
    Args:
        weights: List of portfolio weights (should sum to 1.0)
                Example: [0.4, 0.3, 0.3] means 40% stock1, 30% stock2, 30% stock3
        returns: List of return lists for each stock
                Example: [[0.01, 0.02, -0.01], [0.005, 0.015, 0.02]]
        
    Returns:
        Expected annual return as decimal (e.g., 0.12 = 12% expected return)
        
    Example:
        weights = [0.5, 0.5]  # 50% in each stock
        returns = [
            [0.01, 0.02, -0.01, 0.03],  # Stock 1 daily returns
            [0.005, 0.015, 0.01, 0.02]   # Stock 2 daily returns
        ]
        expected_return = calculate_portfolio_return(weights, returns)
    """
    if len(weights) != len(returns):
        raise ValueError("Number of weights must match number of stocks")
    
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("Weights must sum to 1.0")
    
    # Convert to numpy arrays
    weights_array = np.array(weights)
    
    # Calculate mean return for each stock
    mean_returns = []
    for stock_returns in returns:
        mean_returns.append(np.mean(stock_returns))
    
    mean_returns_array = np.array(mean_returns)
    
    # Portfolio return = weighted sum of individual returns
    portfolio_return = np.dot(weights_array, mean_returns_array)
    
    # Annualize (multiply by 252 trading days)
    annualized_return = portfolio_return * 252
    
    return float(annualized_return)


def calculate_equal_weight_portfolio(num_stocks: int) -> List[float]:
    """
    Calculate equal weights for a portfolio (simplest allocation strategy)
    
    This is a baseline strategy where each stock gets the same allocation.
    For example, with 4 stocks, each gets 25% (0.25) of the portfolio.
    
    Args:
        num_stocks: Number of stocks in the portfolio
        
    Returns:
        List of equal weights that sum to 1.0
        
    Example:
        weights = calculate_equal_weight_portfolio(4)
        # Returns [0.25, 0.25, 0.25, 0.25]
    """
    if num_stocks <= 0:
        raise ValueError("Number of stocks must be positive")
    
    # Each stock gets equal weight
    equal_weight = 1.0 / num_stocks
    
    # Create list of equal weights
    weights = [equal_weight] * num_stocks
    
    return weights
