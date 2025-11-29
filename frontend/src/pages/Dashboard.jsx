import React, { useState } from 'react';
import { BarChart3, Brain } from 'lucide-react';
import StockSelector from '../components/StockSelector';
import TimeframeSelector from '../components/TimeframeSelector';
import PredictionSelector from '../components/PredictionSelector';
import StockChart from '../components/StockChart';
import { useStockHistory } from '../hooks/useStocks';
import { usePredictionPath, useLatestPredictions } from '../hooks/usePredictions';

function Dashboard() {
  const [selectedStock, setSelectedStock] = useState(null);
  const [timeframe, setTimeframe] = useState('6mo');
  const [showPredictions, setShowPredictions] = useState(false);
  const [selectedModel, setSelectedModel] = useState('lstm');
  const [predictionHorizon, setPredictionHorizon] = useState('1month');

  // Fetch historical data
  const { 
    data: historyData, 
    isLoading: historyLoading 
  } = useStockHistory(selectedStock?.symbol, timeframe);

  // Fetch prediction path when predictions are enabled
  const { 
    data: predictionPathData,
    isLoading: predictionLoading 
  } = usePredictionPath(
    selectedStock?.symbol,
    showPredictions ? predictionHorizon : null
  );

  // Fetch latest predictions for summary
  const { 
    data: latestPredictionsData 
  } = useLatestPredictions(selectedStock?.symbol);

  const historicalPrices = historyData?.data?.data || [];
  const predictionPath = predictionPathData?.path || [];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar - Controls */}
        <div className="lg:col-span-1 space-y-6">
          {/* Stock Selection Card */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary-600" />
              Select Stock
            </h2>
            <StockSelector
              selectedStock={selectedStock}
              onSelectStock={setSelectedStock}
            />
          </div>

          {/* Timeframe Selection */}
          {selectedStock && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Historical Timeframe
              </h2>
              <TimeframeSelector
                selected={timeframe}
                onChange={setTimeframe}
              />
            </div>
          )}

          {/* Prediction Controls */}
          {selectedStock && (
            <div className="card">
              <PredictionSelector
                showPredictions={showPredictions}
                onTogglePredictions={() => setShowPredictions(!showPredictions)}
                selectedModel={selectedModel}
                onSelectModel={setSelectedModel}
                selectedHorizon={predictionHorizon}
                onSelectHorizon={setPredictionHorizon}
              />
            </div>
          )}

          {/* Prediction Summary */}
          {selectedStock && latestPredictionsData && (
            <div className="card bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200">
              <h3 className="text-sm font-semibold text-primary-900 mb-3">
                Latest Predictions
              </h3>
              <div className="space-y-2">
                {latestPredictionsData.predictions?.map((pred) => (
                  <div
                    key={pred.horizon_type}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-primary-700 font-medium">
                      {pred.horizon_type}
                    </span>
                    <div className="text-right">
                      <div className="font-semibold text-primary-900">
                        ${pred.predicted_price?.toFixed(2)}
                      </div>
                      <div className={`text-xs ${pred.direction === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                        {pred.price_change >= 0 ? '+' : ''}{pred.price_change_pct?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Main Area - Chart */}
        <div className="lg:col-span-2">
          {!selectedStock ? (
            <div className="card h-96 flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">
                  Select a Stock to Get Started
                </h3>
                <p className="text-gray-500">
                  Choose from 50 top stocks to view historical data and AI predictions
                </p>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedStock.symbol} - {selectedStock.name}
                </h2>
                <p className="text-sm text-gray-600">{selectedStock.sector}</p>
              </div>

              <StockChart
                historicalData={historicalPrices}
                predictionData={predictionPath}
                symbol={selectedStock.symbol}
                isLoading={historyLoading || (showPredictions && predictionLoading)}
                showPredictions={showPredictions}
              />

              {/* Data Source Info */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>
                    Source: {historyData?.source || 'Loading...'}
                  </span>
                  {showPredictions && (
                    <span className="flex items-center gap-1">
                      <Brain className="w-3 h-3" />
                      Model: {selectedModel.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default Dashboard;
