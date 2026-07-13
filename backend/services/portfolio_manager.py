"""
PORTFOLIO MANAGER SERVICE - Virtual portfolio management
Handles creating portfolios, buying/selling stocks, tracking positions
Each user gets $100,000 virtual cash to build a portfolio
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.db_models import Portfolio, PortfolioHolding, Transaction, Stock, StockPrice
from database.crud import add_stock_price
from config.stocks import get_stock_by_symbol
from services.data_fetcher import get_current_price


def create_portfolio(db: Session, user_id: str, name: str = "My Portfolio") -> Portfolio:
    """
    Create a new virtual portfolio for a user with $100,000 starting cash
    
    Args:
        db: Database session
        user_id: Unique identifier for the user
        name: Optional portfolio name
        
    Returns:
        Created Portfolio object
        
    Example:
        portfolio = create_portfolio(db, user_id="user_123", name="Tech Portfolio")
    """
    portfolio = Portfolio(
        user_id=user_id,
        name=name,
        cash_balance=100000.0,
        total_invested=0.0
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def _resolve_stock(db: Session, stock_symbol: str) -> Optional[Stock]:
    """
    Get a stock from the database, or create it from the static stock registry
    if it is one of the tracked symbols.
    """
    symbol = stock_symbol.upper()

    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if stock:
        return stock

    stock_info = get_stock_by_symbol(symbol)
    if not stock_info:
        return None

    stock = Stock(symbol=stock_info["symbol"], name=stock_info["name"])
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def _get_current_stock_price(db: Session, stock: Stock) -> Optional[float]:
    """
    Return the latest stored daily price for a stock.

    If the database has no usable price row, fall back to Polygon and store
    the fetched daily price back into the database so the portfolio view is
    never empty.
    """
    latest_price = db.query(StockPrice).filter(
        StockPrice.stock_id == stock.id
    ).order_by(StockPrice.date.desc()).first()

    if latest_price and latest_price.close and latest_price.close > 0:
        return latest_price.close

    api_data = get_current_price(stock.symbol)
    if api_data.get("status") == "success":
        api_close = float(api_data.get("close") or 0)
        if api_close > 0:
            try:
                price_date = datetime.strptime(api_data.get("date"), "%Y-%m-%d").date()
            except Exception:
                price_date = datetime.utcnow().date()

            try:
                add_stock_price(
                    db=db,
                    symbol=stock.symbol,
                    date=datetime.combine(price_date, datetime.min.time()),
                    open_price=float(api_data.get("open") or api_close),
                    high=float(api_data.get("high") or api_close),
                    low=float(api_data.get("low") or api_close),
                    close=api_close,
                    volume=int(api_data.get("volume") or 0),
                )
            except Exception:
                # The price can still be used even if the cache write fails.
                pass

            return api_close

    return None


def buy_stock(db: Session, portfolio_id: int, stock_symbol: str, 
              shares: Optional[float] = None, amount: Optional[float] = None) -> Dict:
    """
    Buy shares of a stock using virtual cash
    
    You can buy either by:
    1. Specifying number of shares (e.g., 10 shares)
    2. Specifying dollar amount (e.g., $1,000 worth)
    
    Args:
        db: Database session
        portfolio_id: ID of the portfolio
        stock_symbol: Stock ticker symbol (e.g., "AAPL")
        shares: Number of shares to buy (optional, use this OR amount)
        amount: Dollar amount to invest (optional, use this OR shares)
        
    Returns:
        Dictionary with transaction details and updated portfolio
        
    Examples:
        # Buy by shares
        result = buy_stock(db, portfolio_id=1, stock_symbol="AAPL", shares=10)
        
        # Buy by dollar amount (easier!)
        result = buy_stock(db, portfolio_id=1, stock_symbol="AAPL", amount=1000)
    """
        # Validate input: must provide either shares OR amount, but not both
    if shares is None and amount is None:
        return {"success": False, "error": "Must provide either 'shares' or 'amount'"}
    
    if shares is not None and amount is not None:
        return {"success": False, "error": "Cannot provide both 'shares' and 'amount'. Choose one."}
    
    # Get portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        return {"success": False, "error": "Portfolio not found"}
    
    # Get stock (create it from the tracked stock registry if missing)
    stock = _resolve_stock(db, stock_symbol)
    if not stock:
        return {"success": False, "error": f"Stock {stock_symbol} not found"}
    
    price_per_share = _get_current_stock_price(db, stock)
    if not price_per_share or price_per_share <= 0:
        return {"success": False, "error": f"No price data for {stock_symbol}"}
    
    # Calculate shares and total cost based on what user provided
    if amount is not None:
        # User specified dollar amount - calculate how many shares they can buy
        shares = amount / price_per_share
        total_cost = amount
        
        # Check if user has enough cash
        if portfolio.cash_balance < amount:
            return {
                "success": False,
                "error": f"Insufficient funds. Need ${amount:.2f}, have ${portfolio.cash_balance:.2f}"
            }
    else:
        # User specified number of shares - calculate total cost
        total_cost = shares * price_per_share
        
        # Check if user has enough cash
        if portfolio.cash_balance < total_cost:
            return {
                "success": False,
                "error": f"Insufficient funds. Need ${total_cost:.2f}, have ${portfolio.cash_balance:.2f}"
            }
    
    # Update or create holding
    holding = db.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_id == portfolio_id,
        PortfolioHolding.stock_id == stock.id
    ).first()
    
    if holding:
        # Update existing holding - recalculate average cost
        total_shares = holding.shares + shares
        total_cost_basis = (holding.shares * holding.average_cost) + (shares * price_per_share)
        holding.shares = total_shares
        holding.average_cost = total_cost_basis / total_shares
    else:
        # Create new holding
        holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            shares=shares,
            average_cost=price_per_share
        )
        db.add(holding)
    
    # Update portfolio cash and invested amounts
    portfolio.cash_balance -= total_cost
    portfolio.total_invested += total_cost
    
    # Record transaction
    transaction = Transaction(
        portfolio_id=portfolio_id,
        stock_id=stock.id,
        transaction_type="BUY",
        shares=shares,
        price_per_share=price_per_share,
        total_amount=total_cost
    )
    db.add(transaction)
    
    db.commit()
    
    return {
        "success": True,
        "transaction": {
            "type": "BUY",
            "symbol": stock_symbol,
            "shares": shares,
            "price_per_share": price_per_share,
            "total_cost": total_cost
        },
        "portfolio": {
            "cash_balance": portfolio.cash_balance,
            "total_invested": portfolio.total_invested
        }
    }


def sell_stock(db: Session, portfolio_id: int, stock_symbol: str,
               shares: Optional[float] = None, amount: Optional[float] = None) -> Dict:
    """
    Sell shares of a stock and add cash to portfolio
    
    You can sell either by:
    1. Specifying number of shares (e.g., sell 10 shares)
    2. Specifying dollar amount (e.g., sell $1,000 worth)
    
    Args:
        db: Database session
        portfolio_id: ID of the portfolio
        stock_symbol: Stock ticker symbol
        shares: Number of shares to sell (optional, use this OR amount)
        amount: Dollar amount to sell (optional, use this OR shares)
        
    Returns:
        Dictionary with transaction details
        
    Examples:
        # Sell by shares
        result = sell_stock(db, portfolio_id=1, stock_symbol="AAPL", shares=5)
        
        # Sell by dollar amount (easier!)
        result = sell_stock(db, portfolio_id=1, stock_symbol="AAPL", amount=500)
    """
    # Validate input
    if shares is None and amount is None:
        return {"success": False, "error": "Must provide either 'shares' or 'amount'"}
    
    if shares is not None and amount is not None:
        return {"success": False, "error": "Cannot provide both 'shares' and 'amount'. Choose one."}
    
    # Get portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        return {"success": False, "error": "Portfolio not found"}
    
    # Get stock (create it from the tracked stock registry if missing)
    stock = _resolve_stock(db, stock_symbol)
    if not stock:
        return {"success": False, "error": f"Stock {stock_symbol} not found"}
    
    # Get holding
    holding = db.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_id == portfolio_id,
        PortfolioHolding.stock_id == stock.id
    ).first()
    
    if not holding:
        return {"success": False, "error": f"You don't own any {stock_symbol}"}
    
    price_per_share = _get_current_stock_price(db, stock)
    if not price_per_share or price_per_share <= 0:
        return {"success": False, "error": f"No price data for {stock_symbol}"}
    
    # Calculate shares to sell based on what user provided
    if amount is not None:
        # User specified dollar amount - calculate how many shares to sell
        shares_to_sell = amount / price_per_share
        
        # Check if user owns enough shares
        if holding.shares < shares_to_sell:
            max_can_sell = holding.shares * price_per_share
            return {
                "success": False,
                "error": f"Insufficient shares. Trying to sell ${amount:.2f} worth, but only own ${max_can_sell:.2f} worth ({holding.shares:.4f} shares)"
            }
        
        shares = shares_to_sell
        total_proceeds = amount
    else:
        # User specified number of shares
        if holding.shares < shares:
            return {
                "success": False,
                "error": f"Insufficient shares. Trying to sell {shares}, only own {holding.shares:.4f}"
            }
        
        total_proceeds = shares * price_per_share
    
    # Calculate profit/loss
    cost_basis = shares * holding.average_cost
    profit_loss = total_proceeds - cost_basis
    
    # Update holding
    holding.shares -= shares
    if holding.shares == 0:
        db.delete(holding)  # Remove holding if all shares sold
    
    # Update portfolio
    portfolio.cash_balance += total_proceeds
    portfolio.total_invested -= cost_basis
    
    # Record transaction
    transaction = Transaction(
        portfolio_id=portfolio_id,
        stock_id=stock.id,
        transaction_type="SELL",
        shares=shares,
        price_per_share=price_per_share,
        total_amount=total_proceeds
    )
    db.add(transaction)
    
    db.commit()
    
    return {
        "success": True,
        "transaction": {
            "type": "SELL",
            "symbol": stock_symbol,
            "shares": shares,
            "price_per_share": price_per_share,
            "total_proceeds": total_proceeds,
            "profit_loss": profit_loss,
            "profit_loss_percent": (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0
        },
        "portfolio": {
            "cash_balance": portfolio.cash_balance,
            "total_invested": portfolio.total_invested
        }
    }


def get_portfolio_summary(db: Session, portfolio_id: int) -> Dict:
    """
    Get complete portfolio summary including all holdings and current values
    
    Args:
        db: Database session
        portfolio_id: ID of the portfolio
        
    Returns:
        Dictionary with portfolio summary, holdings, and performance metrics
        
    Example:
        summary = get_portfolio_summary(db, portfolio_id=1)
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        return {"success": False, "error": "Portfolio not found"}
    
    holdings = db.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_id == portfolio_id
    ).all()
    
    holdings_data = []
    total_market_value = 0.0
    
    for holding in holdings:
        current_price = _get_current_stock_price(db, holding.stock)
        if not current_price or current_price <= 0:
            current_price = holding.average_cost

        market_value = holding.shares * current_price
        cost_basis = holding.shares * holding.average_cost
        profit_loss = market_value - cost_basis
        profit_loss_percent = (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0

        total_market_value += market_value

        holdings_data.append({
            "symbol": holding.stock.symbol,
            "name": holding.stock.name,
            "shares": holding.shares,
            "average_cost": holding.average_cost,
            "current_price": current_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent
        })
    
    # Calculate total portfolio value
    total_value = portfolio.cash_balance + total_market_value
    
    # Calculate overall return
    total_return = total_value - 100000.0  # Initial amount was $100k
    total_return_percent = (total_return / 100000.0) * 100
    
    return {
        "success": True,
        "portfolio": {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "cash_balance": portfolio.cash_balance,
            "invested_value": total_market_value,
            "total_value": total_value,
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "number_of_holdings": len(holdings_data)
        },
        "holdings": holdings_data
    }
