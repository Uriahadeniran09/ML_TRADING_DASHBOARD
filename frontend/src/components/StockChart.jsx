import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { format } from 'date-fns';
import { TrendingUp, TrendingDown } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-900 mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-gray-600">{entry.name}:</span>
            <span className="text-sm font-semibold">
              ${entry.value?.toFixed(2)}
            </span>
            {entry.payload.confidence_score && (
              <span className="text-xs text-gray-500">
                ({(entry.payload.confidence_score * 100).toFixed(1)}% confidence)
              </span>
            )}
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const StockChart = ({ 
  historicalData, 
  predictionData, 
  symbol, 
  isLoading,
  showPredictions = false 
}) => {
  // Debug logging
  console.log('StockChart render:', {
    historicalCount: historicalData?.length,
    predictionCount: predictionData?.length,
    showPredictions,
    samplePrediction: predictionData?.[0]
  });

  if (isLoading) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chart data...</p>
        </div>
      </div>
    );
  }

  if (!historicalData || historicalData.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg">
        <p className="text-gray-600">No data available</p>
      </div>
    );
  }

  // Prepare chart data - REVERSE to get chronological order (oldest to newest)
  const chartData = historicalData
    .slice()
    .reverse()
    .map((item) => ({
      date: format(new Date(item.date), 'MMM dd, yy'),
      fullDate: item.date,
      price: parseFloat(item.close),
      volume: item.volume,
      type: 'historical',
    }));

  // Add prediction data if available
  if (showPredictions && predictionData && predictionData.length > 0) {
    // Get the last historical price as connection point
    const lastHistorical = chartData[chartData.length - 1];
    
    // Add connection point first (connects historical to prediction)
    if (lastHistorical) {
      chartData.push({
        date: format(new Date(lastHistorical.fullDate), 'MMM dd, yy'),
        fullDate: lastHistorical.fullDate,
        price: null, // Stop historical line
        prediction: lastHistorical.price, // Start prediction line
        type: 'connection',
      });
    }
    
    // Add all prediction points
    predictionData.forEach((pred) => {
      chartData.push({
        date: format(new Date(pred.target_date), 'MMM dd, yy'),
        fullDate: pred.target_date,
        price: null, // No historical data for future
        prediction: parseFloat(pred.predicted_price),
        confidence_score: pred.confidence_score,
        type: 'prediction',
      });
    });
  }

  // Calculate price change
  const firstPrice = chartData[0]?.price;
  const lastPrice = chartData[chartData.length - 1]?.price || chartData[chartData.length - 1]?.prediction;
  const priceChange = lastPrice - firstPrice;
  const priceChangePercent = (priceChange / firstPrice) * 100;
  const isPositive = priceChange >= 0;

  return (
    <div className="space-y-4">
      {/* Price Summary */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-gray-900">
            ${lastPrice?.toFixed(2)}
          </h3>
          <div className={`flex items-center gap-1 text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{isPositive ? '+' : ''}{priceChange.toFixed(2)}</span>
            <span>({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)</span>
          </div>
        </div>
        {showPredictions && predictionData && predictionData.length > 0 && (
          <div className="text-right">
            <p className="text-sm text-gray-600">Predicted Target</p>
            <p className="text-lg font-semibold text-primary-700">
              ${predictionData[predictionData.length - 1]?.predicted_price?.toFixed(2)}
            </p>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              domain={['auto', 'auto']}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Historical Price Line */}
            <Line
              type="monotone"
              dataKey="price"
              stroke="#0ea5e9"
              strokeWidth={3}
              dot={false}
              name="Historical Price"
              connectNulls={false}
            />
            
            {/* Prediction Line */}
            {showPredictions && (
              <Line
                type="monotone"
                dataKey="prediction"
                stroke="#f97316"
                strokeWidth={3}
                strokeDasharray="8 4"
                dot={{ fill: '#f97316', r: 4, strokeWidth: 2, stroke: '#fff' }}
                name="Predicted Price"
                connectNulls={true}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend Info */}
      {showPredictions && predictionData && predictionData.length > 0 && (
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-primary-500"></div>
            <span className="text-gray-600">Historical Data</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-orange-500 border-dashed border-t-2 border-orange-500"></div>
            <span className="text-gray-600">ML Prediction</span>
          </div>
        </div>
      )}
      
      {/* No Predictions Warning */}
      {showPredictions && (!predictionData || predictionData.length === 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            ⚠️ No predictions available for <strong>{symbol}</strong>. 
            Only <strong>AAPL</strong> currently has trained LSTM predictions. 
            Train a model for this stock to see predictions.
          </p>
        </div>
      )}
    </div>
  );
};

export default StockChart;
