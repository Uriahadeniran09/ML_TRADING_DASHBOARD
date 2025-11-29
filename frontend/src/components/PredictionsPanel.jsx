import React from 'react';
import { Brain, TrendingUp, TrendingDown, Sparkles, AlertCircle } from 'lucide-react';
import { useLatestPredictions } from '../hooks/usePredictions';

function PredictionsPanel({ holdings }) {
  if (!holdings || holdings.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">AI Predictions</h2>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">Add holdings to see ML-driven predictions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-bold text-gray-900">AI Predictions</h2>
        <span className="ml-auto text-xs text-gray-500 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          LSTM Model
        </span>
      </div>

      <div className="space-y-4">
        {holdings.map((holding) => (
          <HoldingPrediction key={holding.symbol} holding={holding} />
        ))}
      </div>

      {/* Portfolio Summary */}
      <PortfolioPredictionSummary holdings={holdings} />
    </div>
  );
}

function HoldingPrediction({ holding }) {
  const { data, isLoading, error } = useLatestPredictions(holding.symbol);

  if (isLoading) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 rounded-lg">
        <div className="flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>No predictions for {holding.symbol}</span>
        </div>
      </div>
    );
  }

  // Get 1-month prediction
  const oneMonthPred = data?.predictions?.find((p) => p.horizon_type === '1month');
  if (!oneMonthPred) {
    return null;
  }

  const currentValue = holding.market_value;
  const predictedPrice = oneMonthPred.predicted_price;
  const predictedValue = holding.shares * predictedPrice;
  const expectedChange = predictedValue - currentValue;
  const expectedChangePercent = (expectedChange / currentValue) * 100;
  const isPositive = expectedChange >= 0;

  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0);

  return (
    <div className="p-3 bg-gradient-to-br from-primary-50 to-blue-50 rounded-lg border border-primary-100">
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="font-semibold text-gray-900">{holding.symbol}</div>
          <div className="text-xs text-gray-600">1-Month Forecast</div>
        </div>
        <div
          className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
            isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}
        >
          {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {isPositive ? '+' : ''}
          {expectedChangePercent.toFixed(1)}%
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-gray-600 text-xs">Current</div>
          <div className="font-semibold text-gray-900">{formatCurrency(currentValue)}</div>
        </div>
        <div>
          <div className="text-gray-600 text-xs">Predicted</div>
          <div className="font-semibold text-primary-700">{formatCurrency(predictedValue)}</div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-primary-200">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Expected Change</span>
          <span className={`font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}
            {formatCurrency(expectedChange)}
          </span>
        </div>
        <div className="mt-1 flex items-center justify-between text-xs">
          <span className="text-gray-600">Confidence</span>
          <div className="flex items-center gap-1">
            <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600 rounded-full"
                style={{ width: `${(oneMonthPred.confidence_score || 0) * 100}%` }}
              ></div>
            </div>
            <span className="text-gray-900 font-medium">
              {((oneMonthPred.confidence_score || 0) * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PortfolioPredictionSummary({ holdings }) {
  const [totalExpectedChange, setTotalExpectedChange] = React.useState(0);
  const [loadingCount, setLoadingCount] = React.useState(holdings.length);

  // Track predictions for all holdings
  const predictions = holdings.map((holding) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data } = useLatestPredictions(holding.symbol);
    return { holding, data };
  });

  React.useEffect(() => {
    let total = 0;
    let loaded = 0;

    predictions.forEach(({ holding, data }) => {
      if (data) {
        loaded++;
        const oneMonthPred = data.predictions?.find((p) => p.horizon_type === '1month');
        if (oneMonthPred) {
          const currentValue = holding.market_value;
          const predictedValue = holding.shares * oneMonthPred.predicted_price;
          total += predictedValue - currentValue;
        }
      }
    });

    setTotalExpectedChange(total);
    setLoadingCount(holdings.length - loaded);
  }, [predictions, holdings]);

  if (loadingCount > 0) {
    return null;
  }

  const isPositive = totalExpectedChange >= 0;
  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0);

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          Expected Portfolio Change (1 Month)
        </span>
        <div className="flex items-center gap-2">
          {isPositive ? (
            <TrendingUp className="w-4 h-4 text-green-600" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600" />
          )}
          <span className={`text-lg font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}
            {formatCurrency(totalExpectedChange)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default PredictionsPanel;
