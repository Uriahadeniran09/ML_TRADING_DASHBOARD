import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { useStocks } from '../hooks/useStocks';

const StockSelector = ({ selectedStock, onSelectStock }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const { data: stocksData, isLoading, error } = useStocks();

  const stocks = stocksData?.stocks || [];

  const filteredStocks = stocks.filter(
    (stock) =>
      stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (stock) => {
    onSelectStock(stock);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative w-full max-w-md">
      <div className="relative">
        <input
          type="text"
          placeholder="Search stocks (e.g., AAPL, Apple)..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className="w-full px-4 py-3 pl-12 bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary-500 transition-colors"
        />
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
      </div>

      {selectedStock && !isOpen && (
        <div className="mt-2 p-3 bg-primary-50 border-2 border-primary-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-bold text-primary-900">{selectedStock.symbol}</span>
              <span className="text-sm text-primary-700 ml-2">{selectedStock.name}</span>
            </div>
            <button
              onClick={() => onSelectStock(null)}
              className="text-primary-600 hover:text-primary-800 text-sm font-medium"
            >
              Change
            </button>
          </div>
        </div>
      )}

      {isOpen && (searchTerm || !selectedStock) && (
        <div className="absolute z-50 w-full mt-2 bg-white border-2 border-gray-200 rounded-lg shadow-xl max-h-96 overflow-y-auto">
          {isLoading && (
            <div className="p-4 text-center text-gray-500">Loading stocks...</div>
          )}
          
          {error && (
            <div className="p-4 text-center text-red-500">Error loading stocks</div>
          )}
          
          {!isLoading && !error && filteredStocks.length === 0 && (
            <div className="p-4 text-center text-gray-500">No stocks found</div>
          )}
          
          {!isLoading && !error && filteredStocks.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleSelect(stock)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-gray-900">{stock.symbol}</span>
                  <span className="text-sm text-gray-600 ml-2">{stock.name}</span>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {stock.sector}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default StockSelector;
