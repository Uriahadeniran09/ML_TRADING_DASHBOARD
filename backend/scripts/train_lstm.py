"""
UNIFIED LSTM TRAINING SCRIPT

Single entry point for all LSTM training modes.
- Quick test: Few epochs for debugging
- Single stock: Train one stock with specified epochs
- Batch: Train multiple stocks
- Optional: Generate multi-horizon predictions

Usage:
    # Quick test (default 20 epochs)
    python train_lstm.py --symbol AAPL --quick
    
    # Single stock (default 100 epochs)
    python train_lstm.py --symbol AAPL
    python train_lstm.py --symbol AAPL --epochs 50
    
    # Multiple stocks
    python train_lstm.py --symbols AAPL GOOGL MSFT TSLA
    python train_lstm.py --symbols AAPL GOOGL MSFT TSLA --epochs 75
    
    # Skip prediction generation
    python train_lstm.py --symbol AAPL --no-predictions
    
    # All 50 stocks
    python train_lstm.py --all
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
from models.lstm.train import train_comprehensive, train_multiple_comprehensive
from config.stocks import get_all_stocks


def main():
    parser = argparse.ArgumentParser(
        description='Train LSTM models for stock price prediction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Training modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--symbol',
        type=str,
        help='Single stock symbol to train (e.g., AAPL)'
    )
    mode_group.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        help='Multiple stock symbols (e.g., AAPL GOOGL MSFT TSLA)'
    )
    mode_group.add_argument(
        '--all',
        action='store_true',
        help='Train all 50 stocks'
    )
    
    # Training options
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (5 epochs instead of default)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        help='Number of training epochs (default: 20 for --quick, 100 for normal)'
    )
    parser.add_argument(
        '--no-predictions',
        action='store_true',
        help='Skip multi-horizon prediction generation after training'
    )
    
    args = parser.parse_args()
    
    # Determine symbols to train
    if args.all:
        symbols = [stock['symbol'] for stock in get_all_stocks()]
        print(f"📊 Training all {len(symbols)} stocks")
    elif args.symbols:
        symbols = args.symbols
    else:  # args.symbol
        symbols = [args.symbol]
    
    # Determine epochs
    if args.epochs:
        epochs = args.epochs
    elif args.quick:
        epochs = 5
    else:
        epochs = 100
    
    generate_predictions = not args.no_predictions
    
    # Run training
    print("\n" + "="*80)
    print(f"LSTM TRAINING - {len(symbols)} stock(s)")
    print("="*80)
    print(f"Mode: {'Quick test' if args.quick else 'Standard training'}")
    print(f"Epochs: {epochs}")
    print(f"Predictions: {'Yes' if generate_predictions else 'No'}")
    print(f"Symbols: {', '.join(symbols)}")
    print("="*80 + "\n")
    
    if len(symbols) == 1:
        # Single stock training
        success = train_comprehensive(
            symbols[0],
            epochs=epochs,
            generate_predictions=generate_predictions,
            verbose=1
        )
        
        if success:
            print("\n✅ Training completed successfully!")
        else:
            print("\n❌ Training failed!")
            sys.exit(1)
    else:
        # Multiple stocks training
        results = train_multiple_comprehensive(
            symbols,
            epochs=epochs,
            generate_predictions=generate_predictions
        )
        
        # Check results
        failed = [s for s, status in results.items() if status == 'failed']
        if failed:
            print(f"\n⚠️  {len(failed)} stock(s) failed to train")
            sys.exit(1)
        else:
            print("\n✅ All stocks trained successfully!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
