import React, { useState } from 'react';
import { TrendingUp, TrendingDown, ChevronUp, ChevronDown } from 'lucide-react';

function HoldingsTable({ holdings, onBuyMore, onSell }) {
  const [sortField, setSortField] = useState('market_value');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!holdings || holdings.length === 0) {
    return (
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Your Holdings</h2>
        <div className="text-center py-12">
          <p className="text-gray-500">No holdings yet. Start by buying some stocks!</p>
        </div>
      </div>
    );
  }

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedHoldings = [...holdings].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (typeof aValue === 'string') {
      return sortDirection === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    
    return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronDown className="w-4 h-4 text-gray-300" />;
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-4 h-4 text-primary-600" />
    ) : (
      <ChevronDown className="w-4 h-4 text-primary-600" />
    );
  };

  const columns = [
    { field: 'symbol', label: 'Symbol', align: 'left' },
    { field: 'shares', label: 'Shares', align: 'right' },
    { field: 'average_cost', label: 'Avg Cost', align: 'right' },
    { field: 'current_price', label: 'Current Price', align: 'right' },
    { field: 'market_value', label: 'Market Value', align: 'right' },
    { field: 'profit_loss', label: 'P&L', align: 'right' },
    { field: 'profit_loss_percent', label: 'P&L %', align: 'right' },
  ];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Your Holdings</h2>
        <p className="text-sm text-gray-600">{holdings.length} positions</p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.field}
                  className={`px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors ${
                    col.align === 'right' ? 'text-right' : 'text-left'
                  }`}
                  onClick={() => handleSort(col.field)}
                >
                  <div className={`flex items-center gap-1 ${col.align === 'right' ? 'justify-end' : 'justify-start'}`}>
                    {col.label}
                    <SortIcon field={col.field} />
                  </div>
                </th>
              ))}
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedHoldings.map((holding) => {
              const isProfitable = holding.profit_loss >= 0;
              return (
                <tr key={holding.symbol} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{holding.symbol}</span>
                      {holding.name && (
                        <span className="text-xs text-gray-500">{holding.name}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {holding.shares.toFixed(2)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatCurrency(holding.average_cost)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatCurrency(holding.current_price)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                    {formatCurrency(holding.market_value)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right">
                    <div className={`flex items-center justify-end gap-1 ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                      {isProfitable ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      <span className="font-semibold">{formatCurrency(holding.profit_loss)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isProfitable
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {isProfitable ? '+' : ''}{holding.profit_loss_percent.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-right text-sm">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onBuyMore(holding.symbol)}
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        Buy
                      </button>
                      <button
                        onClick={() => onSell(holding.symbol)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Sell
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Total Market Value</span>
          <span className="font-bold text-gray-900">
            {formatCurrency(holdings.reduce((sum, h) => sum + h.market_value, 0))}
          </span>
        </div>
      </div>
    </div>
  );
}

export default HoldingsTable;
