import React, { useState } from 'react';
import { History, ArrowUpRight, ArrowDownLeft, Filter } from 'lucide-react';
import { useTransactions } from '../hooks/usePortfolio';
import { format } from 'date-fns';

function TransactionHistory({ portfolioId }) {
  const [filter, setFilter] = useState('all'); // 'all', 'buy', 'sell'
  const [limit, setLimit] = useState(50);

  const { data, isLoading, error } = useTransactions(portfolioId, limit);

  if (isLoading) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">Transaction History</h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">Transaction History</h2>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No transactions yet</p>
        </div>
      </div>
    );
  }

  const transactions = data.transactions || [];
  const filteredTransactions = transactions.filter((t) => {
    if (filter === 'all') return true;
    return t.transaction_type.toLowerCase() === filter;
  });

  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0);

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">Transaction History</h2>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('buy')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === 'buy'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Buys
            </button>
            <button
              onClick={() => setFilter('sell')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === 'sell'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Sells
            </button>
          </div>
        </div>
      </div>

      {filteredTransactions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No {filter !== 'all' ? filter : ''} transactions yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTransactions.map((transaction) => {
            const isBuy = transaction.transaction_type === 'BUY';
            return (
              <div
                key={transaction.id}
                className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {/* Icon */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    isBuy ? 'bg-green-100' : 'bg-red-100'
                  }`}
                >
                  {isBuy ? (
                    <ArrowDownLeft className="w-5 h-5 text-green-600" />
                  ) : (
                    <ArrowUpRight className="w-5 h-5 text-red-600" />
                  )}
                </div>

                {/* Transaction Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">
                      {isBuy ? 'Bought' : 'Sold'} {transaction.symbol}
                    </span>
                    <span className="text-xs text-gray-500">
                      {transaction.shares.toFixed(2)} shares
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    @ {formatCurrency(transaction.price_per_share)} • {formatDate(transaction.transaction_date)}
                  </div>
                </div>

                {/* Amount */}
                <div className="text-right">
                  <div
                    className={`font-bold ${
                      isBuy ? 'text-red-600' : 'text-green-600'
                    }`}
                  >
                    {isBuy ? '-' : '+'}
                    {formatCurrency(transaction.total_amount)}
                  </div>
                  {transaction.profit_loss !== undefined && !isBuy && (
                    <div
                      className={`text-xs ${
                        transaction.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {transaction.profit_loss >= 0 ? 'Gain' : 'Loss'}:{' '}
                      {formatCurrency(Math.abs(transaction.profit_loss))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Show More Button */}
      {transactions.length >= limit && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setLimit(limit + 50)}
            className="text-sm text-primary-600 hover:text-primary-800 font-medium"
          >
            Load More Transactions
          </button>
        </div>
      )}

      {/* Summary */}
      {transactions.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {filteredTransactions.length} of {transactions.length} transactions
            </span>
            <span>
              {transactions.filter((t) => t.transaction_type === 'BUY').length} buys,{' '}
              {transactions.filter((t) => t.transaction_type === 'SELL').length} sells
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default TransactionHistory;
