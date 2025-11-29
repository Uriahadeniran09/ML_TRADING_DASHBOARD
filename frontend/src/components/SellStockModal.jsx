import React, { useState, useEffect } from 'react';
import { X, TrendingDown, AlertCircle } from 'lucide-react';
import { stocksApi } from '../services/api';

function SellStockModal({ isOpen, onClose, onSell, portfolio, symbol, holding }) {
  const [inputMode, setInputMode] = useState('shares'); // 'shares' or 'amount'
  const [amount, setAmount] = useState('');
  const [shares, setShares] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [error, setError] = useState(null);

  // Fetch current price when modal opens
  useEffect(() => {
    if (isOpen && symbol) {
      setLoadingPrice(true);
      setError(null);
      stocksApi
        .getCurrentPrice(symbol)
        .then((data) => {
          setCurrentPrice(data.price);
          setLoadingPrice(false);
        })
        .catch((err) => {
          setError('Failed to fetch price');
          setLoadingPrice(false);
        });
    }
  }, [isOpen, symbol]);

  const availableShares = holding?.shares || 0;
  const averageCost = holding?.average_cost || 0;

  // Calculate shares from amount or vice versa
  const calculatedShares = currentPrice && amount ? parseFloat(amount) / currentPrice : 0;
  const calculatedAmount = currentPrice && shares ? parseFloat(shares) * currentPrice : 0;

  const displayShares = inputMode === 'amount' ? calculatedShares : parseFloat(shares) || 0;
  const displayAmount = inputMode === 'shares' ? calculatedAmount : parseFloat(amount) || 0;

  const hasEnoughShares = displayShares <= availableShares;
  const isValid = symbol && currentPrice && displayShares > 0 && hasEnoughShares;

  // Calculate profit/loss for this sale
  const costBasis = displayShares * averageCost;
  const profitLoss = displayAmount - costBasis;
  const profitLossPercent = costBasis > 0 ? (profitLoss / costBasis) * 100 : 0;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid) return;

    const sellData = {
      portfolioId: portfolio.id,
      symbol: symbol,
      amount: inputMode === 'amount' ? parseFloat(amount) : null,
      shares: inputMode === 'shares' ? parseFloat(shares) : null,
    };

    onSell(sellData);
    handleClose();
  };

  const handleClose = () => {
    setAmount('');
    setShares('');
    setCurrentPrice(null);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="bg-red-100 p-2 rounded-lg">
              <TrendingDown className="w-5 h-5 text-red-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Sell {symbol}</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Current Position */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Shares Owned</span>
              <span className="font-semibold text-gray-900">
                {availableShares.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Average Cost</span>
              <span className="font-semibold text-gray-900">
                {formatCurrency(averageCost)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Current Price</span>
              {loadingPrice ? (
                <div className="animate-pulse h-5 w-16 bg-gray-200 rounded"></div>
              ) : (
                <span className="font-semibold text-gray-900">
                  {formatCurrency(currentPrice)}
                </span>
              )}
            </div>
            <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
              <span className="text-gray-600">Market Value</span>
              <span className="font-bold text-gray-900">
                {formatCurrency(availableShares * (currentPrice || 0))}
              </span>
            </div>
          </div>

          {currentPrice && (
            <>
              {/* Input Mode Toggle */}
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setInputMode('shares')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputMode === 'shares'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Sell by Shares
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('amount')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputMode === 'amount'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Sell by Amount
                </button>
              </div>

              {/* Shares Input */}
              {inputMode === 'shares' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Shares to Sell
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max={availableShares}
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="0.00"
                  />
                  <div className="mt-2 flex justify-between">
                    <button
                      type="button"
                      onClick={() => setShares((availableShares / 2).toFixed(2))}
                      className="text-sm text-primary-600 hover:text-primary-800"
                    >
                      Half
                    </button>
                    <button
                      type="button"
                      onClick={() => setShares(availableShares.toFixed(2))}
                      className="text-sm text-primary-600 hover:text-primary-800"
                    >
                      All
                    </button>
                  </div>
                  {displayShares > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      You'll receive: {formatCurrency(displayAmount)}
                    </p>
                  )}
                </div>
              )}

              {/* Amount Input */}
              {inputMode === 'amount' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dollar Amount to Sell
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max={availableShares * currentPrice}
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="0.00"
                  />
                  {displayAmount > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      ≈ {displayShares.toFixed(4)} shares
                    </p>
                  )}
                </div>
              )}

              {/* Profit/Loss Preview */}
              {displayShares > 0 && (
                <div className={`p-4 rounded-lg ${profitLoss >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Sale Proceeds</span>
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(displayAmount)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Cost Basis</span>
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(costBasis)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
                      <span className={`font-semibold ${profitLoss >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {profitLoss >= 0 ? 'Profit' : 'Loss'}
                      </span>
                      <div className="text-right">
                        <div className={`font-bold ${profitLoss >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                          {profitLoss >= 0 ? '+' : ''}{formatCurrency(profitLoss)}
                        </div>
                        <div className={`text-xs ${profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {profitLoss >= 0 ? '+' : ''}{profitLossPercent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {!hasEnoughShares && displayShares > 0 && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span className="text-sm">You don't own enough shares</span>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span className="text-sm">{error}</span>
                </div>
              )}
            </>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
            >
              Sell {symbol}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SellStockModal;
