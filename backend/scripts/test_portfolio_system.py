"""
TEST PORTFOLIO SYSTEM - Complete workflow demonstration

This script tests the entire virtual portfolio system:
1. Create a portfolio with $100,000
2. Buy stocks using virtual cash
3. Check portfolio summary and performance
4. Calculate risk metrics (volatility, Sharpe ratio)
5. Calculate portfolio returns
6. Test optimization strategies

Run this inside the Docker container:
docker exec ml_trading_backend python scripts/test_portfolio_system.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from backend.database.db_models import Stock, StockPrice, Portfolio
from services.portfolio_manager import (
    create_portfolio,
    buy_stock,
    sell_stock,
    get_portfolio_summary
)
from services.risk_calculator import (
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_portfolio_risk
)
from services.portfolio_optimizer import (
    calculate_portfolio_return,
    calculate_equal_weight_portfolio
)
from datetime import datetime, timedelta


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_portfolio_system():
    """Main test function - runs through complete workflow"""
    
    db = SessionLocal()
    
    try:
        print_section("🎮 VIRTUAL PORTFOLIO SYSTEM TEST")
        print("\nThis script demonstrates:")
        print("✓ Creating a portfolio with $100,000")
        print("✓ Buying stocks with virtual cash")
        print("✓ Tracking positions and profit/loss")
        print("✓ Calculating risk metrics")
        print("✓ Portfolio optimization")
        
        # ============================================================
        # STEP 1: Create Portfolio
        # ============================================================
        print_section("STEP 1: Create Portfolio with $100,000")
        
        # Create a unique user ID for testing
        user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        portfolio = create_portfolio(
            db=db,
            user_id=user_id,
            name="Test Tech Portfolio"
        )
        
        print(f"\n✓ Portfolio created!")
        print(f"  User ID: {portfolio.user_id}")
        print(f"  Portfolio ID: {portfolio.id}")
        print(f"  Starting Cash: ${portfolio.cash_balance:,.2f}")
        print(f"  Total Invested: ${portfolio.total_invested:,.2f}")
        
        # ============================================================
        # STEP 2: Buy Stocks (Dollar Amount Method)
        # ============================================================
        print_section("STEP 2: Buy Stocks Using Dollar Amounts")
        
        print("\n📊 Building a diversified portfolio...")
        print("Strategy: Equal allocation across 5 tech stocks\n")
        
        # Invest $20,000 in each stock (5 × $20k = $100k total)
        investments = [
            {"symbol": "AAPL", "amount": 20000, "name": "Apple"},
            {"symbol": "GOOGL", "amount": 20000, "name": "Google"},
            {"symbol": "MSFT", "amount": 20000, "name": "Microsoft"},
            {"symbol": "NVDA", "amount": 20000, "name": "NVIDIA"},
            {"symbol": "META", "amount": 20000, "name": "Meta"}
        ]
        
        for inv in investments:
            result = buy_stock(
                db=db,
                portfolio_id=portfolio.id,
                stock_symbol=inv["symbol"],
                amount=inv["amount"]
            )
            
            if result["success"]:
                txn = result["transaction"]
                print(f"✓ Bought {inv['name']} ({inv['symbol']})")
                print(f"  Shares: {txn['shares']:.4f}")
                print(f"  Price: ${txn['price_per_share']:.2f}")
                print(f"  Total Cost: ${txn['total_cost']:,.2f}")
                print(f"  Remaining Cash: ${result['portfolio']['cash_balance']:,.2f}\n")
            else:
                print(f"✗ Failed to buy {inv['symbol']}: {result['error']}\n")
        
        # ============================================================
        # STEP 3: Portfolio Summary
        # ============================================================
        print_section("STEP 3: Portfolio Summary")
        
        summary = get_portfolio_summary(db, portfolio.id)
        
        if summary["success"]:
            portfolio_data = summary["portfolio"]
            holdings = summary["holdings"]
            
            print(f"\n💼 Portfolio Overview:")
            print(f"  Total Value: ${portfolio_data['total_value']:,.2f}")
            print(f"  Cash Balance: ${portfolio_data['cash_balance']:,.2f}")
            print(f"  Invested Value: ${portfolio_data['invested_value']:,.2f}")
            print(f"  Total Return: ${portfolio_data['total_return']:,.2f} ({portfolio_data['total_return_percent']:.2f}%)")
            print(f"  Number of Holdings: {portfolio_data['number_of_holdings']}")
            
            print(f"\n📈 Individual Holdings:")
            print(f"{'Symbol':<8} {'Shares':<12} {'Avg Cost':<12} {'Current':<12} {'Market Value':<15} {'P&L':<12} {'P&L %':<8}")
            print("-" * 90)
            
            for holding in holdings:
                print(f"{holding['symbol']:<8} "
                      f"{holding['shares']:<12.4f} "
                      f"${holding['average_cost']:<11.2f} "
                      f"${holding['current_price']:<11.2f} "
                      f"${holding['market_value']:<14,.2f} "
                      f"${holding['profit_loss']:<11,.2f} "
                      f"{holding['profit_loss_percent']:<7.2f}%")
        
        # ============================================================
        # STEP 4: Calculate Risk Metrics
        # ============================================================
        print_section("STEP 4: Calculate Risk Metrics")
        
        print("\n📊 Fetching historical price data for risk analysis...")
        
        # Get historical prices for each holding (last 30 days)
        holdings_with_prices = []
        
        for holding in holdings:
            stock = db.query(Stock).filter(Stock.symbol == holding['symbol']).first()
            
            if stock:
                # Get last 30 days of prices
                prices_query = db.query(StockPrice).filter(
                    StockPrice.stock_id == stock.id
                ).order_by(StockPrice.date.desc()).limit(30).all()
                
                if prices_query:
                    # Extract closing prices (reverse to chronological order)
                    prices = [p.close for p in reversed(prices_query)]
                    
                    # Calculate individual stock risk
                    volatility = calculate_volatility(prices)
                    sharpe = calculate_sharpe_ratio(prices)
                    
                    holdings_with_prices.append({
                        "symbol": holding['symbol'],
                        "shares": holding['shares'],
                        "prices": prices
                    })
                    
                    print(f"\n{holding['symbol']} Risk Metrics:")
                    print(f"  Volatility: {volatility:.2%} (annualized)")
                    print(f"  Sharpe Ratio: {sharpe:.2f}")
                    
                    if volatility < 0.20:
                        risk_level = "LOW"
                    elif volatility < 0.35:
                        risk_level = "MEDIUM"
                    else:
                        risk_level = "HIGH"
                    
                    print(f"  Risk Level: {risk_level}")
        
        # Calculate portfolio-level risk
        if holdings_with_prices:
            print("\n" + "-" * 80)
            print("💼 Portfolio-Level Risk:")
            
            portfolio_risk = calculate_portfolio_risk(holdings_with_prices)
            
            print(f"  Portfolio Volatility: {portfolio_risk['portfolio_volatility']:.2%}")
            print(f"  Portfolio Sharpe Ratio: {portfolio_risk['portfolio_sharpe']:.2f}")
            print(f"  Total Holdings Analyzed: {portfolio_risk['total_holdings']}")
            
            if portfolio_risk['portfolio_sharpe'] > 2.0:
                rating = "EXCELLENT"
            elif portfolio_risk['portfolio_sharpe'] > 1.0:
                rating = "GOOD"
            elif portfolio_risk['portfolio_sharpe'] > 0.5:
                rating = "FAIR"
            else:
                rating = "POOR"
            
            print(f"  Risk-Adjusted Rating: {rating}")
        
        # ============================================================
        # STEP 5: Portfolio Returns & Optimization
        # ============================================================
        print_section("STEP 5: Portfolio Returns & Optimization")
        
        if holdings_with_prices:
            # Calculate returns for each stock
            returns_data = []
            for holding in holdings_with_prices:
                prices = holding['prices']
                if len(prices) > 1:
                    # Calculate daily returns
                    returns = []
                    for i in range(1, len(prices)):
                        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                        returns.append(daily_return)
                    returns_data.append(returns)
            
            if returns_data and len(returns_data) == len(holdings_with_prices):
                # Current allocation (equal weight)
                num_stocks = len(holdings_with_prices)
                current_weights = calculate_equal_weight_portfolio(num_stocks)
                
                print(f"\n📊 Current Allocation Strategy: Equal Weight")
                print(f"  Number of stocks: {num_stocks}")
                print(f"  Weight per stock: {current_weights[0]:.2%} (${100000 * current_weights[0]:,.2f})")
                
                # Calculate expected return
                expected_return = calculate_portfolio_return(current_weights, returns_data)
                
                print(f"\n📈 Expected Portfolio Return:")
                print(f"  Annual Return: {expected_return:.2%}")
                print(f"  Expected Value in 1 year: ${100000 * (1 + expected_return):,.2f}")
                
                # Show allocation breakdown
                print(f"\n💡 Allocation Breakdown:")
                for i, holding in enumerate(holdings_with_prices):
                    allocation = current_weights[i] * 100000
                    print(f"  {holding['symbol']}: {current_weights[i]:.2%} (${allocation:,.2f})")
        
        # ============================================================
        # STEP 6: Test Selling
        # ============================================================
        print_section("STEP 6: Test Selling Stocks")
        
        print("\n💰 Testing sell functionality...")
        print("Selling $5,000 worth of Apple (AAPL)\n")
        
        sell_result = sell_stock(
            db=db,
            portfolio_id=portfolio.id,
            stock_symbol="AAPL",
            amount=5000
        )
        
        if sell_result["success"]:
            txn = sell_result["transaction"]
            print(f"✓ Sold {txn['symbol']}")
            print(f"  Shares Sold: {txn['shares']:.4f}")
            print(f"  Price: ${txn['price_per_share']:.2f}")
            print(f"  Total Proceeds: ${txn['total_proceeds']:,.2f}")
            print(f"  Profit/Loss: ${txn['profit_loss']:,.2f} ({txn['profit_loss_percent']:.2f}%)")
            print(f"  New Cash Balance: ${sell_result['portfolio']['cash_balance']:,.2f}")
        else:
            print(f"✗ Failed to sell: {sell_result['error']}")
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print_section("FINAL PORTFOLIO SUMMARY")
        
        final_summary = get_portfolio_summary(db, portfolio.id)
        
        if final_summary["success"]:
            portfolio_data = final_summary["portfolio"]
            
            print(f"\n💼 Final Portfolio State:")
            print(f"  Total Value: ${portfolio_data['total_value']:,.2f}")
            print(f"  Cash Balance: ${portfolio_data['cash_balance']:,.2f}")
            print(f"  Invested Value: ${portfolio_data['invested_value']:,.2f}")
            print(f"  Total Return: ${portfolio_data['total_return']:,.2f} ({portfolio_data['total_return_percent']:.2f}%)")
            print(f"  Number of Holdings: {portfolio_data['number_of_holdings']}")
        
        print_section("✅ TEST COMPLETED SUCCESSFULLY")
        
        print("\n🎯 What This Demonstrates:")
        print("  ✓ Virtual portfolio creation ($100k starting balance)")
        print("  ✓ Buying stocks with dollar amounts (fractional shares)")
        print("  ✓ Real-time portfolio tracking and P&L calculation")
        print("  ✓ Risk metrics (volatility, Sharpe ratio)")
        print("  ✓ Portfolio-level risk analysis")
        print("  ✓ Expected returns calculation")
        print("  ✓ Equal-weight optimization strategy")
        print("  ✓ Selling stocks and profit/loss tracking")
        
        print("\n🚀 Next Steps:")
        print("  1. Integrate LSTM model for price predictions")
        print("  2. Integrate Transformer model for advanced forecasting")
        print("  3. Use predictions to optimize portfolio allocation")
        print("  4. Create API endpoints for frontend")
        print("  5. Build dashboard UI to visualize everything")
        
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_portfolio_system()
