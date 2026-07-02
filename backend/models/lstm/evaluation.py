"""
LSTM MODEL EVALUATION

Comprehensive evaluation metrics for LSTM model performance.
Includes regression metrics, classification metrics, and custom metrics for trading.
"""

import numpy as np
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    confusion_matrix, classification_report
)
from typing import Tuple, Dict
import pandas as pd


def evaluate_model(
    model: object,
    X_test: np.ndarray,
    y_test: np.ndarray,
    scalers: dict,
    target_column: str = 'close',
    denormalize: bool = True
) -> Dict[str, float]:
    """
    Comprehensive evaluation of LSTM model.
    
    Args:
        model: Trained Keras model
        X_test: Test sequences
        y_test: Test targets (normalized)
        scalers: Dictionary of scalers
        target_column: Target feature name
        denormalize: Whether to denormalize predictions
        
    Returns:
        Dictionary of evaluation metrics
    """
    # Make predictions
    y_pred = model.predict(X_test, verbose=0).flatten()
    
    # Denormalize if requested
    if denormalize and target_column in scalers:
        scaler = scalers[target_column]
        y_pred_denorm = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
        y_test_denorm = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    else:
        y_pred_denorm = y_pred
        y_test_denorm = y_test
    
    # ========== REGRESSION METRICS ==========
    mse = mean_squared_error(y_test_denorm, y_pred_denorm)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test_denorm, y_pred_denorm)
    r2 = r2_score(y_test_denorm, y_pred_denorm)
    
    # Mean Absolute Percentage Error
    mape = np.mean(np.abs(
        (y_test_denorm - y_pred_denorm) / y_test_denorm
    )) * 100
    
    # ========== DIRECTIONAL METRICS ==========
    # Directional accuracy (did we predict UP/DOWN correctly?)
    if len(y_test_denorm) > 1:
        actual_direction = np.diff(y_test_denorm) > 0
        pred_direction = np.diff(y_pred_denorm) > 0
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
        
        # Confusion matrix for direction
        cm = confusion_matrix(actual_direction, pred_direction)
    else:
        directional_accuracy = None
        cm = None
    
    # ========== TRADING METRICS ==========
    # Profit from perfect trading vs model trading
    if len(y_test_denorm) > 1:
        # Simulated returns if we follow predictions
        actual_returns = np.diff(y_test_denorm) / y_test_denorm[:-1]
        
        # If we predict UP, buy; if predict DOWN, sell
        predicted_positions = pred_direction.astype(int)  # 1 = buy, 0 = sell
        strategy_returns = actual_returns * (2 * predicted_positions - 1)
        
        cumulative_return = np.prod(1 + strategy_returns) - 1
        sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) if np.std(strategy_returns) > 0 else 0
    else:
        cumulative_return = None
        sharpe_ratio = None
    
    # ========== COMPILE METRICS ==========
    metrics = {
        # Regression Metrics
        'mse': float(mse),
        'rmse': float(rmse),
        'mae': float(mae),
        'r2': float(r2),
        'mape': float(mape),
        
        # Directional Metrics
        'directional_accuracy': float(directional_accuracy) if directional_accuracy else None,
        
        # Trading Metrics
        'cumulative_return': float(cumulative_return) if cumulative_return else None,
        'sharpe_ratio': float(sharpe_ratio) if sharpe_ratio else None,
        
        # Additional Info
        'num_test_samples': len(y_test),
        'mean_actual_price': float(np.mean(y_test_denorm)),
        'mean_predicted_price': float(np.mean(y_pred_denorm))
    }
    
    return metrics


def print_evaluation_report(metrics: Dict[str, float], symbol: str = None):
    """
    Print formatted evaluation report.
    
    Args:
        metrics: Dictionary of metrics
        symbol: Stock symbol (optional)
    """
    print("\n" + "="*70)
    if symbol:
        print(f"EVALUATION REPORT FOR {symbol}")
    else:
        print("EVALUATION REPORT")
    print("="*70)
    
    print("\n📊 REGRESSION METRICS:")
    print(f"   MSE:  {metrics['mse']:,.2f}")
    print(f"   RMSE: ${metrics['rmse']:.2f}")
    print(f"   MAE:  ${metrics['mae']:.2f}")
    print(f"   R²:   {metrics['r2']:.4f}")
    print(f"   MAPE: {metrics['mape']:.2f}%")
    
    print("\n📈 DIRECTIONAL METRICS:")
    if metrics['directional_accuracy']:
        print(f"   Directional Accuracy: {metrics['directional_accuracy']:.2f}%")
    else:
        print("   Directional Accuracy: N/A")
    
    print("\n💰 TRADING METRICS:")
    if metrics['cumulative_return']:
        print(f"   Cumulative Return: {metrics['cumulative_return']*100:+.2f}%")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
    else:
        print("   Trading Metrics: N/A")
    
    print("\n📋 SUMMARY:")
    print(f"   Test Samples: {metrics['num_test_samples']}")
    print(f"   Avg Actual Price: ${metrics['mean_actual_price']:.2f}")
    print(f"   Avg Predicted Price: ${metrics['mean_predicted_price']:.2f}")
    
    # Performance assessment
    print("\n⭐ PERFORMANCE ASSESSMENT:")
    if metrics['r2'] > 0.7:
        print("   ✅ Excellent model (R² > 0.7)")
    elif metrics['r2'] > 0.5:
        print("   ✔️  Good model (R² > 0.5)")
    elif metrics['r2'] > 0:
        print("   ⚠️  Fair model (R² > 0)")
    else:
        print("   ❌ Poor model (R² < 0) - needs improvement")
    
    if metrics['directional_accuracy'] and metrics['directional_accuracy'] > 55:
        print("   ✅ Good directional accuracy (> 55%)")
    elif metrics['directional_accuracy'] and metrics['directional_accuracy'] > 50:
        print("   ✔️  Acceptable directional accuracy (> 50%)")
    else:
        print("   ⚠️  Low directional accuracy (< 50%)")
    
    print("="*70 + "\n")


def compare_models(
    metrics_list: list,
    model_names: list
) -> pd.DataFrame:
    """
    Compare multiple models' metrics.
    
    Args:
        metrics_list: List of metrics dictionaries
        model_names: List of model names
        
    Returns:
        DataFrame with comparison
    """
    comparison = pd.DataFrame(metrics_list, index=model_names)
    
    # Select key metrics
    key_metrics = ['rmse', 'mae', 'r2', 'mape', 'directional_accuracy', 'sharpe_ratio']
    available_metrics = [m for m in key_metrics if m in comparison.columns]
    
    return comparison[available_metrics]


def calculate_confidence_score(metrics: Dict[str, float]) -> float:
    """
    Calculate an overall confidence score based on multiple metrics.
    
    Args:
        metrics: Dictionary of evaluation metrics
        
    Returns:
        Confidence score (0-1)
    """
    score = 0.0
    weights = {
        'r2': 0.4,
        'directional_accuracy': 0.3,
        'mape': 0.3
    }
    
    # R² score (0 to 1, higher is better)
    if metrics.get('r2'):
        r2_normalized = max(0, min(1, (metrics['r2'] + 1) / 2))  # Normalize from [-1,1] to [0,1]
        score += weights['r2'] * r2_normalized
    
    # Directional accuracy (0 to 100, convert to 0-1)
    if metrics.get('directional_accuracy'):
        dir_acc_normalized = metrics['directional_accuracy'] / 100
        score += weights['directional_accuracy'] * dir_acc_normalized
    
    # MAPE (lower is better, invert and normalize)
    if metrics.get('mape'):
        mape_normalized = max(0, 1 - (metrics['mape'] / 100))
        score += weights['mape'] * mape_normalized
    
    return score


def generate_evaluation_summary(
    metrics: Dict[str, float],
    symbol: str
) -> dict:
    """
    Generate a comprehensive evaluation summary.
    
    Args:
        metrics: Evaluation metrics
        symbol: Stock symbol
        
    Returns:
        Dictionary with summary
    """
    confidence = calculate_confidence_score(metrics)
    
    # Determine performance level
    if metrics['r2'] > 0.7 and metrics.get('directional_accuracy', 0) > 55:
        performance = 'excellent'
    elif metrics['r2'] > 0.5 and metrics.get('directional_accuracy', 0) > 50:
        performance = 'good'
    elif metrics['r2'] > 0:
        performance = 'fair'
    else:
        performance = 'poor'
    
    return {
        'symbol': symbol,
        'confidence_score': confidence,
        'performance_level': performance,
        'metrics': metrics,
        'recommendation': _get_recommendation(performance, confidence)
    }


def _get_recommendation(performance: str, confidence: float) -> str:
    """Generate recommendation based on performance."""
    if performance == 'excellent':
        return "Model is ready for production use."
    elif performance == 'good':
        return "Model performs well. Consider using in production with monitoring."
    elif performance == 'fair':
        return "Model shows promise but needs improvement. Retrain with more data or tune hyperparameters."
    else:
        return "Model needs significant improvement. Consider different features or architecture."
