"""
LSTM TRAINING MODULE

Handles the complete training pipeline for LSTM models.
- Builds model
- Sets up callbacks
- Trains model
- Saves best model based on validation loss
- Comprehensive training with evaluation and artifacts
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import json
import shutil
import numpy as np
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from typing import Tuple, Dict
from datetime import datetime

from .model import build_lstm_model, print_model_summary
from .hyperparameters import LSTM_HYPERPARAMETERS
from .evaluation import evaluate_model, print_evaluation_report, calculate_confidence_score


def train_lstm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    symbol: str,
    hyperparams: dict = None,
    model_save_dir: str = 'data/models/lstm',
    verbose: int = 1
) -> Tuple[object, Dict]:
    """
    Train LSTM model with optimal parameters.
    
    Args:
        X_train: Training sequences
        y_train: Training targets
        X_val: Validation sequences
        y_val: Validation targets
        symbol: Stock symbol (for file naming)
        hyperparams: Hyperparameters dict (uses defaults if None)
        model_save_dir: Directory to save model
        verbose: Verbosity level (0=silent, 1=progress, 2=detailed)
        
    Returns:
        (trained_model, training_history)
    """
    # Use default hyperparameters if not provided
    if hyperparams is None:
        hyperparams = LSTM_HYPERPARAMETERS
    
    print("\n" + "="*70)
    print(f"TRAINING LSTM MODEL FOR {symbol}")
    print("="*70)
    print(f"Training samples: {len(X_train)} (70%)")
    print(f"Validation samples: {len(X_val)} (20%)")
    print(f"Input shape: {X_train.shape}")
    print(f"Epochs: {hyperparams['epochs']}")
    print(f"Batch size: {hyperparams['batch_size']}")
    print("="*70 + "\n")
    
    # Build model
    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_lstm_model(
        input_shape=input_shape,
        lstm_units=hyperparams['lstm_units'],
        dropout_rate=hyperparams['dropout_rate'],
        dense_units=hyperparams['dense_units'],
        activation=hyperparams['activation'],
        learning_rate=hyperparams['learning_rate'],
        loss=hyperparams['loss']
    )
    
    if verbose >= 2:
        print_model_summary(model)
    
    # Setup callbacks
    callbacks = []
    
    # Create save directory
    os.makedirs(model_save_dir, exist_ok=True)
    model_path = os.path.join(model_save_dir, f'{symbol}_best_model.keras')
    
    # Early Stopping - stop training if no improvement
    early_stop = EarlyStopping(
        monitor=hyperparams['early_stopping']['monitor'],
        patience=hyperparams['early_stopping']['patience'],
        restore_best_weights=hyperparams['early_stopping']['restore_best_weights'],
        min_delta=hyperparams['early_stopping']['min_delta'],
        verbose=verbose
    )
    callbacks.append(early_stop)
    
    # Learning Rate Reduction - reduce LR when stuck
    reduce_lr = ReduceLROnPlateau(
        monitor=hyperparams['reduce_lr']['monitor'],
        factor=hyperparams['reduce_lr']['factor'],
        patience=hyperparams['reduce_lr']['patience'],
        min_lr=hyperparams['reduce_lr']['min_lr'],
        verbose=hyperparams['reduce_lr']['verbose']
    )
    callbacks.append(reduce_lr)
    
    # Model Checkpoint - save best model
    checkpoint = ModelCheckpoint(
        model_path,
        monitor=hyperparams['checkpoint']['monitor'],
        save_best_only=hyperparams['checkpoint']['save_best_only'],
        save_weights_only=hyperparams['checkpoint']['save_weights_only'],
        verbose=hyperparams['checkpoint']['verbose']
    )
    callbacks.append(checkpoint)
    
    # Train model
    print(f"🏋️ Training started at {datetime.now().strftime('%H:%M:%S')}\n")
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=hyperparams['epochs'],
        batch_size=hyperparams['batch_size'],
        callbacks=callbacks,
        shuffle=hyperparams['validation']['shuffle'],
        verbose=hyperparams['validation']['verbose']
    )
    
    print(f"\n✅ Training completed at {datetime.now().strftime('%H:%M:%S')}")
    
    # Training summary
    best_epoch = np.argmin(history.history['val_loss']) + 1
    best_val_loss = min(history.history['val_loss'])
    final_train_loss = history.history['loss'][-1]
    
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    print(f"Total epochs run: {len(history.history['loss'])}")
    print(f"Best epoch: {best_epoch}")
    print(f"Best validation loss: {best_val_loss:.6f}")
    print(f"Final training loss: {final_train_loss:.6f}")
    print(f"Model saved to: {model_path}")
    print("="*70 + "\n")
    
    return model, history.history


def train_multiple_stocks(
    symbols: list,
    hyperparams: dict = None,
    model_save_dir: str = 'data/models/lstm'
) -> Dict[str, Dict]:
    """
    Train LSTM models for multiple stocks.
    
    Args:
        symbols: List of stock symbols
        hyperparams: Hyperparameters dict
        model_save_dir: Directory to save models
        
    Returns:
        Dictionary mapping symbols to training results
    """
    from .data import get_data_for_training
    
    results = {}
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(symbols)}] Processing {symbol}")
        print(f"{'='*70}\n")
        
        try:
            # Get data
            X_train, X_val, X_test, y_train, y_val, y_test, scalers = \
                get_data_for_training(
                    symbol,
                    features=hyperparams['features'] if hyperparams else None
                )
            
            # Train model
            model, history = train_lstm(
                X_train, y_train,
                X_val, y_val,
                symbol=symbol,
                hyperparams=hyperparams,
                model_save_dir=model_save_dir
            )
            
            results[symbol] = {
                'status': 'success',
                'history': history,
                'best_val_loss': min(history['val_loss'])
            }
            
        except Exception as e:
            print(f"❌ Failed to train {symbol}: {str(e)}")
            results[symbol] = {
                'status': 'failed',
                'error': str(e)
            }
    
    # Print summary
    print("\n" + "="*70)
    print("BATCH TRAINING SUMMARY")
    print("="*70)
    
    successful = [s for s, r in results.items() if r['status'] == 'success']
    failed = [s for s, r in results.items() if r['status'] == 'failed']
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_loss = np.mean([results[s]['best_val_loss'] for s in successful])
        print(f"\n📊 Average best validation loss: {avg_loss:.6f}")
    
    if failed:
        print(f"\n❌ Failed stocks: {', '.join(failed)}")
    
    print("="*70 + "\n")
    
    return results


# ============================================================================
# COMPREHENSIVE TRAINING WITH EVALUATION AND ARTIFACTS
# ============================================================================

def save_scalers(scalers: dict, save_dir: str):
    """Save scalers to JSON file."""
    scalers_data = {}
    for feature, scaler in scalers.items():
        scalers_data[feature] = {
            'min': scaler.min_.tolist(),
            'scale': scaler.scale_.tolist(),
            'data_min': scaler.data_min_.tolist(),
            'data_max': scaler.data_max_.tolist()
        }
    
    with open(os.path.join(save_dir, 'scalers.json'), 'w') as f:
        json.dump(scalers_data, f, indent=2)
    
    print(f"✅ Scalers saved to {save_dir}/scalers.json")


def save_metadata(symbol: str, hyperparams: dict, history: dict, 
                  metrics: dict, confidence: float, save_dir: str):
    """Save model metadata."""
    metadata = {
        'symbol': symbol,
        'training_date': datetime.now().isoformat(),
        'model_version': 'v1.0',
        'sequence_length': hyperparams['sequence_length'],
        'features': hyperparams['features'],
        'target_column': hyperparams['target_column'],
        
        # Model architecture
        'lstm_units': hyperparams['lstm_units'],
        'dropout_rate': hyperparams['dropout_rate'],
        'dense_units': hyperparams['dense_units'],
        
        # Training info
        'epochs_run': len(history['loss']),
        'batch_size': hyperparams['batch_size'],
        'learning_rate': hyperparams['learning_rate'],
        'optimizer': hyperparams.get('optimizer', 'adamw'),
        
        # Performance
        'best_val_loss': float(min(history['val_loss'])),
        'final_train_loss': float(history['loss'][-1]),
        'confidence_score': float(confidence),
        
        # Test metrics
        'test_metrics': {
            'rmse': float(metrics['rmse']),
            'mae': float(metrics['mae']),
            'r2': float(metrics['r2']),
            'mape': float(metrics['mape']),
            'directional_accuracy': float(metrics['directional_accuracy']) if metrics['directional_accuracy'] else None
        }
    }
    
    with open(os.path.join(save_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to {save_dir}/metadata.json")


def save_training_history(history: dict, save_dir: str):
    """Save training history for visualization."""
    # Convert numpy types to Python native types
    history_json = {}
    for key, values in history.items():
        history_json[key] = [float(v) for v in values]
    
    with open(os.path.join(save_dir, 'training_history.json'), 'w') as f:
        json.dump(history_json, f, indent=2)
    
    print(f"✅ Training history saved to {save_dir}/training_history.json")


def train_comprehensive(
    symbol: str,
    epochs: int = None,
    generate_predictions: bool = True,
    verbose: int = 1
) -> bool:
    """
    Comprehensive training pipeline for a single stock.
    
    Includes:
    - Data loading and preprocessing
    - Model training with callbacks
    - Evaluation on test set
    - Saving model, scalers, metadata, and history
    - Optional multi-horizon prediction generation
    
    Args:
        symbol: Stock symbol to train
        epochs: Number of epochs (None = use default from hyperparams)
        generate_predictions: Whether to generate multi-horizon predictions
        verbose: Verbosity level
        
    Returns:
        True if successful, False otherwise
    """
    from .data import get_data_for_training
    from .multi_horizon_paths import update_multi_horizon_with_paths
    
    print("\n" + "="*80)
    print(f"COMPREHENSIVE LSTM TRAINING FOR {symbol}")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # ========== STEP 1: DATA PREPARATION ==========
    print("📊 STEP 1: Data Preparation")
    print("-"*80)
    
    hyperparams = LSTM_HYPERPARAMETERS.copy()
    if epochs:
        hyperparams['epochs'] = epochs
    
    try:
        X_train, X_val, X_test, y_train, y_val, y_test, scalers = \
            get_data_for_training(
                symbol,
                features=hyperparams['features'],
                sequence_length=hyperparams['sequence_length']
            )
        
        print(f"✅ Data loaded successfully")
        print(f"   Training: {len(X_train)} samples")
        print(f"   Validation: {len(X_val)} samples")
        print(f"   Test: {len(X_test)} samples")
        print(f"   Features: {len(hyperparams['features'])}")
        print(f"   Sequence length: {hyperparams['sequence_length']} days")
        
    except Exception as e:
        print(f"❌ Failed to load data: {str(e)}")
        return False
    
    # ========== STEP 2: MODEL TRAINING ==========
    print(f"\n🏋️ STEP 2: Model Training ({hyperparams['epochs']} epochs)")
    print("-"*80)
    
    model_save_dir = f'data/models/lstm/{symbol}'
    os.makedirs(model_save_dir, exist_ok=True)
    
    try:
        model, history = train_lstm(
            X_train, y_train,
            X_val, y_val,
            symbol=symbol,
            hyperparams=hyperparams,
            model_save_dir='data/models/lstm',  # Will save as {symbol}_best_model.keras
            verbose=verbose
        )
        
        print("✅ Training completed successfully")
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        return False
    
    # ========== STEP 3: MODEL EVALUATION ==========
    print("\n📈 STEP 3: Model Evaluation on Test Set")
    print("-"*80)
    
    try:
        metrics = evaluate_model(
            model,
            X_test,
            y_test,
            scalers,
            target_column=hyperparams['target_column'],
            denormalize=True
        )
        
        print_evaluation_report(metrics, symbol)
        
        # Calculate confidence score
        confidence = calculate_confidence_score(metrics)
        print(f"📊 Overall Confidence Score: {confidence:.2%}\n")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {str(e)}")
        return False
    
    # ========== STEP 4: SAVE ARTIFACTS ==========
    print("💾 STEP 4: Saving Model Artifacts")
    print("-"*80)
    
    # Move model to proper directory
    old_path = f'data/models/lstm/{symbol}_best_model.keras'
    new_path = f'{model_save_dir}/lstm_model.keras'
    if os.path.exists(old_path):
        shutil.move(old_path, new_path)
        print(f"✅ Model saved to {new_path}")
    
    # Save scalers
    save_scalers(scalers, model_save_dir)
    
    # Save metadata
    save_metadata(symbol, hyperparams, history, metrics, confidence, model_save_dir)
    
    # Save training history
    save_training_history(history, model_save_dir)
    
    # ========== STEP 5: GENERATE PREDICTIONS ==========
    if generate_predictions:
        print("\n🔮 STEP 5: Generating Multi-Horizon Predictions")
        print("-"*80)
        
        try:
            update_multi_horizon_with_paths(symbol)
            print(f"✅ Multi-horizon predictions generated and saved to database")
            print("   - 1 day: 1 point")
            print("   - 1 week: 5 points")
            print("   - 1 month: 21 points")
            print("   - 6 months: 126 points")
            print(f"   Total: 153 prediction path points")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not generate predictions: {str(e)}")
    
    # ========== FINAL SUMMARY ==========
    print("\n" + "="*80)
    print("✅ TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Symbol: {symbol}")
    print(f"Model: {new_path}")
    print(f"Best Validation Loss: {min(history['val_loss']):.6f}")
    print(f"Test RMSE: ${metrics['rmse']:.2f}")
    print(f"Test MAE: ${metrics['mae']:.2f}")
    print(f"Test R²: {metrics['r2']:.4f}")
    print(f"Directional Accuracy: {metrics['directional_accuracy']:.2f}%" if metrics['directional_accuracy'] else "N/A")
    print(f"Confidence Score: {confidence:.2%}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    return True


def train_multiple_comprehensive(
    symbols: list,
    epochs: int = None,
    generate_predictions: bool = True
) -> Dict[str, str]:
    """
    Train multiple stocks with comprehensive pipeline.
    
    Args:
        symbols: List of stock symbols
        epochs: Number of epochs (None = use default)
        generate_predictions: Whether to generate multi-horizon predictions
        
    Returns:
        Dictionary mapping symbols to status ('success' or 'failed')
    """
    print("\n" + "="*80)
    print(f"BATCH TRAINING: {len(symbols)} STOCKS")
    print("="*80)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    results = {}
    successful = []
    failed = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(symbols)}] Training {symbol}")
        print(f"{'='*80}\n")
        
        success = train_comprehensive(
            symbol,
            epochs=epochs,
            generate_predictions=generate_predictions,
            verbose=1
        )
        
        if success:
            successful.append(symbol)
            results[symbol] = 'success'
        else:
            failed.append(symbol)
            results[symbol] = 'failed'
        
        print(f"\nProgress: {i}/{len(symbols)} completed")
    
    # Final summary
    print("\n" + "="*80)
    print("BATCH TRAINING SUMMARY")
    print("="*80)
    print(f"Total stocks: {len(symbols)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        print(f"\n✅ Successfully trained: {', '.join(successful)}")
    
    if failed:
        print(f"\n❌ Failed to train: {', '.join(failed)}")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    return results
