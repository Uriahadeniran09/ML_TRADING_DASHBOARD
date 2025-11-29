import React, { useState } from 'react';
import { Plus, RefreshCw, Loader2 } from 'lucide-react';
import PortfolioHeader from '../components/PortfolioHeader';
import HoldingsTable from '../components/HoldingsTable';
import BuyStockModal from '../components/BuyStockModal';
import SellStockModal from '../components/SellStockModal';
import PredictionsPanel from '../components/PredictionsPanel';
import RiskMetricsPanel from '../components/RiskMetricsPanel';
import TransactionHistory from '../components/TransactionHistory';
import { usePortfolio, useBuyStock, useSellStock } from '../hooks/usePortfolio';

function Portfolio() {
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [selectedHolding, setSelectedHolding] = useState(null);

  // Get or create portfolio for default user
  const { portfolio, holdings, isLoading, error } = usePortfolio('default_user');

  // Mutations for buy/sell
  const buyMutation = useBuyStock();
  const sellMutation = useSellStock();

  const handleBuyClick = (symbol = null) => {
    setSelectedSymbol(symbol);
    setShowBuyModal(true);
  };

  const handleSellClick = (symbol) => {
    const holding = holdings?.find((h) => h.symbol === symbol);
    setSelectedSymbol(symbol);
    setSelectedHolding(holding);
    setShowSellModal(true);
  };

  const handleBuy = (buyData) => {
    buyMutation.mutate(buyData, {
      onSuccess: () => {
        // Modal will close automatically
      },
      onError: (error) => {
        alert(`Error buying stock: ${error.message}`);
      },
    });
  };

  const handleSell = (sellData) => {
    sellMutation.mutate(sellData, {
      onSuccess: () => {
        // Modal will close automatically
      },
      onError: (error) => {
        alert(`Error selling stock: ${error.message}`);
      },
    });
  };

  if (error) {
    return (
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card text-center py-12">
          <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Portfolio</h2>
          <p className="text-gray-600">{error.message}</p>
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Portfolio</h1>
          <p className="text-gray-600 mt-1">
            Manage your investments and track performance
          </p>
        </div>
        <button
          onClick={() => handleBuyClick()}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          Buy Stock
        </button>
      </div>

      {/* Portfolio Summary Cards */}
      <PortfolioHeader portfolio={portfolio} />

      {/* Holdings Table */}
      <div className="mb-6">
        <HoldingsTable
          holdings={holdings || []}
          onBuyMore={handleBuyClick}
          onSell={handleSellClick}
        />
      </div>

      {/* Predictions and Risk Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <PredictionsPanel holdings={holdings || []} />
        <RiskMetricsPanel portfolioId={portfolio?.id} />
      </div>

      {/* Transaction History */}
      <TransactionHistory portfolioId={portfolio?.id} />

      {/* Modals */}
      <BuyStockModal
        isOpen={showBuyModal}
        onClose={() => {
          setShowBuyModal(false);
          setSelectedSymbol(null);
        }}
        onBuy={handleBuy}
        portfolio={portfolio}
        preselectedSymbol={selectedSymbol}
      />

      <SellStockModal
        isOpen={showSellModal}
        onClose={() => {
          setShowSellModal(false);
          setSelectedSymbol(null);
          setSelectedHolding(null);
        }}
        onSell={handleSell}
        portfolio={portfolio}
        symbol={selectedSymbol}
        holding={selectedHolding}
      />

      {/* Loading Overlay */}
      {(buyMutation.isPending || sellMutation.isPending) && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-40">
          <div className="bg-white p-6 rounded-lg shadow-xl flex items-center gap-3">
            <RefreshCw className="w-5 h-5 text-primary-600 animate-spin" />
            <span className="font-medium text-gray-900">
              {buyMutation.isPending ? 'Processing purchase...' : 'Processing sale...'}
            </span>
          </div>
        </div>
      )}
    </main>
  );
}

export default Portfolio;
