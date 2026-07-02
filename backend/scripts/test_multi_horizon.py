"""
TEST MULTI-HORIZON PREDICTIONS

Tests the multi-horizon prediction system with 1 day, 1 week, 1 month, and 6 month forecasts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lstm.multi_horizon import (
    update_multi_horizon_predictions,
    get_prediction_summary,
    FORECAST_HORIZONS
)


def test_single_stock(symbol: str = 'AAPL'):
    """
    Test multi-horizon predictions for a single stock.
    
    Args:
        symbol: Stock symbol to test
    """
    print("\n" + "="*80)
    print(f"TESTING MULTI-HORIZON PREDICTIONS FOR {symbol}")
    print("="*80 + "\n")
    
    # Generate predictions for all horizons
    results = update_multi_horizon_predictions(symbol)
    
    # Display results
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80 + "\n")
    
    for horizon_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        days = FORECAST_HORIZONS[horizon_name]
        print(f"{horizon_name:12} ({days:3} days): {status}")
    
    # Get detailed summary
    print("\n" + "="*80)
    print("PREDICTION DETAILS")
    print("="*80 + "\n")
    
    summary = get_prediction_summary(symbol)
    
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
        return
    
    predictions = summary.get('predictions', {})
    
    print(f"Symbol: {symbol}\n")
    print(f"{'Horizon':<12} {'Days':<6} {'Price':<12} {'Change %':<12} {'Confidence':<12} {'Target Date'}")
    print("-" * 80)
    
    for horizon_name in ['1day', '1week', '1month', '6months']:
        if horizon_name in predictions:
            pred = predictions[horizon_name]
            days = FORECAST_HORIZONS[horizon_name]
            price = pred['predicted_price']
            change_pct = pred['predicted_change_pct']
            confidence = pred['confidence']
            target = pred['target_date']
            
            change_str = f"{change_pct:+.2f}%"
            conf_str = f"{confidence:.1%}"
            
            print(f"{horizon_name:<12} {days:<6} ${price:<10.2f} {change_str:<12} {conf_str:<12} {target}")
    
    print("\n" + "="*80 + "\n")


def test_multiple_stocks(symbols: list = None):
    """
    Test multi-horizon predictions for multiple stocks.
    
    Args:
        symbols: List of stock symbols (defaults to a few popular ones)
    """
    if symbols is None:
        symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    print("\n" + "="*80)
    print(f"TESTING MULTI-HORIZON PREDICTIONS FOR {len(symbols)} STOCKS")
    print("="*80 + "\n")
    
    from models.lstm.multi_horizon import batch_update_multi_horizon
    
    # Generate predictions for all stocks
    all_results = batch_update_multi_horizon(symbols)
    
    # Summary table
    print("\n" + "="*80)
    print("SUMMARY BY STOCK")
    print("="*80 + "\n")
    
    print(f"{'Symbol':<10} {'1 Day':<10} {'1 Week':<10} {'1 Month':<10} {'6 Months':<10}")
    print("-" * 80)
    
    for symbol in symbols:
        if symbol in all_results:
            results = all_results[symbol]
            row = f"{symbol:<10}"
            
            for horizon in ['1day', '1week', '1month', '6months']:
                status = "✅" if results.get(horizon, False) else "❌"
                row += f" {status:<10}"
            
            print(row)
    
    print("\n" + "="*80 + "\n")


def display_prediction_comparison():
    """
    Display a comparison of predictions across different horizons.
    """
    from database.db import SessionLocal
    from database.db_models import Stock, StockPrice, LSTMPrediction
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("PREDICTION COMPARISON ACROSS HORIZONS")
        print("="*80 + "\n")
        
        # Get stocks with predictions
        stocks_with_preds = db.query(Stock).join(LSTMPrediction).distinct().all()
        
        for stock in stocks_with_preds[:5]:  # Limit to first 5 for display
            print(f"\n📊 {stock.symbol} - {stock.name}")
            print("-" * 80)
            
            # Get current price
            latest_price = db.query(StockPrice).filter(
                StockPrice.stock_id == stock.id
            ).order_by(StockPrice.date.desc()).first()
            
            if latest_price:
                current_price = latest_price.close
                print(f"Current Price: ${current_price:.2f}\n")
                
                # Get predictions for each horizon
                for horizon_name, horizon_days in FORECAST_HORIZONS.items():
                    pred = db.query(LSTMPrediction).filter(
                        LSTMPrediction.stock_id == stock.id,
                        LSTMPrediction.horizon_days == horizon_days
                    ).order_by(LSTMPrediction.prediction_date.desc()).first()
                    
                    if pred:
                        change_pct = ((pred.predicted_price - current_price) / current_price) * 100
                        print(f"{horizon_name:12} ({horizon_days:3}d): "
                              f"${pred.predicted_price:7.2f} "
                              f"({change_pct:+6.2f}%) "
                              f"Confidence: {pred.confidence_score:5.1%} "
                              f"Target: {pred.target_date}")
        
        print("\n" + "="*80 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test multi-horizon LSTM predictions')
    parser.add_argument('--symbol', type=str, help='Test single stock symbol')
    parser.add_argument('--multiple', nargs='+', help='Test multiple stock symbols')
    parser.add_argument('--compare', action='store_true', help='Compare predictions across horizons')
    
    args = parser.parse_args()
    
    if args.symbol:
        test_single_stock(args.symbol)
    elif args.multiple:
        test_multiple_stocks(args.multiple)
    elif args.compare:
        display_prediction_comparison()
    else:
        # Default: test with AAPL
        print("\nNo arguments provided. Running default test with AAPL...\n")
        test_single_stock('AAPL')
