import React, { useState, useEffect } from 'react';
import { X, DollarSign, TrendingUp, AlertCircle } from 'lucide-react';
import { useStocks } from '../hooks/useStocks';
import { stocksApi } from '../services/api';

function BuyStockModal({ isOpen, onClose, onBuy, portfolio, preselectedSymbol = null }) {
  const [selectedStock, setSelectedStock] = useState(preselectedSymbol || '');
  const [inputMode, setInputMode] = useState('amount'); // 'amount' or 'shares'
  const [amount, setAmount] = useState('');
  const [shares, setShares] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [error, setError] = useState(null);

  const { data: stocksData } = useStocks();
  const stocks = stocksData?.stocks || [];

  // Fetch current price when stock is selected
  useEffect(() => {
    if (selectedStock) {
      setLoadingPrice(true);
      setError(null);
      stocksApi
        .getCurrentPrice(selectedStock)
        .then((data) => {
          setCurrentPrice(data.price);
          setLoadingPrice(false);
        })
        .catch((err) => {
          setError('Failed to fetch price');
          setLoadingPrice(false);
        });
    }
  }, [selectedStock]);

  // Calculate shares from amount or vice versa
  const calculatedShares = currentPrice && amount ? parseFloat(amount) / currentPrice : 0;
  const calculatedAmount = currentPrice && shares ? parseFloat(shares) * currentPrice : 0;

  const displayShares = inputMode === 'amount' ? calculatedShares : parseFloat(shares) || 0;
  const displayAmount = inputMode === 'shares' ? calculatedAmount : parseFloat(amount) || 0;

  const canAfford = displayAmount <= (portfolio?.cash_balance || 0);
  const isValid = selectedStock && currentPrice && displayAmount > 0 && canAfford;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid) return;

    const buyData = {
      portfolioId: portfolio.id,
      symbol: selectedStock,
      amount: inputMode === 'amount' ? parseFloat(amount) : null,
      shares: inputMode === 'shares' ? parseFloat(shares) : null,
    };

    onBuy(buyData);
    handleClose();
  };

  const handleClose = () => {
    setSelectedStock(preselectedSymbol || '');
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
            <div className="bg-green-100 p-2 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Buy Stock</h2>
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
          {/* Stock Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Stock
            </label>
            <select
              value={selectedStock}
              onChange={(e) => setSelectedStock(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              disabled={!!preselectedSymbol}
            >
              <option value="">Choose a stock...</option>
              {stocks.map((stock) => (
                <option key={stock.symbol} value={stock.symbol}>
                  {stock.symbol} - {stock.name}
                </option>
              ))}
            </select>
          </div>

          {/* Current Price */}
          {selectedStock && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Current Price</span>
                {loadingPrice ? (
                  <div className="animate-pulse h-6 w-20 bg-gray-200 rounded"></div>
                ) : (
                  <span className="text-lg font-bold text-gray-900">
                    {formatCurrency(currentPrice)}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Input Mode Toggle */}
          {selectedStock && currentPrice && (
            <>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setInputMode('amount')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputMode === 'amount'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Buy by Amount
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('shares')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    inputMode === 'shares'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Buy by Shares
                </button>
              </div>

              {/* Amount Input */}
              {inputMode === 'amount' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Amount to Invest
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={portfolio?.cash_balance}
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="0.00"
                    />
                  </div>
                  {displayAmount > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      ≈ {displayShares.toFixed(4)} shares
                    </p>
                  )}
                </div>
              )}

              {/* Shares Input */}
              {inputMode === 'shares' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Shares
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="0.00"
                  />
                  {displayShares > 0 && (
                    <p className="mt-2 text-sm text-gray-600">
                      Total: {formatCurrency(displayAmount)}
                    </p>
                  )}
                </div>
              )}

              {/* Cash Balance Info */}
              <div className="bg-blue-50 p-4 rounded-lg space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Available Cash</span>
                  <span className="font-semibold text-gray-900">
                    {formatCurrency(portfolio?.cash_balance)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">After Purchase</span>
                  <span className="font-semibold text-gray-900">
                    {formatCurrency((portfolio?.cash_balance || 0) - displayAmount)}
                  </span>
                </div>
              </div>

              {/* Error Message */}
              {!canAfford && displayAmount > 0 && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span className="text-sm">Insufficient cash balance</span>
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
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
            >
              Buy {selectedStock || 'Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BuyStockModal;
