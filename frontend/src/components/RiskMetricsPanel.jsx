import React from 'react';
import { Shield, AlertTriangle, TrendingUp, Activity } from 'lucide-react';
import { usePortfolioRisk } from '../hooks/usePortfolio';

function RiskMetricsPanel({ portfolioId }) {
  const { data, isLoading, error } = usePortfolioRisk(portfolioId);

  if (isLoading) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">Risk Metrics</h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-6 bg-gray-200 rounded w-2/3"></div>
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
          <Shield className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-bold text-gray-900">Risk Metrics</h2>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">Add holdings to see risk analysis</p>
        </div>
      </div>
    );
  }

  const riskMetrics = data.risk_metrics || {};
  const volatility = riskMetrics.portfolio_volatility_percent || 0;
  const sharpeRatio = riskMetrics.portfolio_sharpe_ratio || 0;
  const riskRating = riskMetrics.overall_risk_rating || 'Unknown';
  const diversified = riskMetrics.diversification?.diversified || false;
  const holdingsCount = riskMetrics.diversification?.total_holdings || 0;

  const getRiskColor = (rating) => {
    const colors = {
      Low: 'text-green-600 bg-green-100',
      Medium: 'text-yellow-600 bg-yellow-100',
      High: 'text-orange-600 bg-orange-100',
      'Very High': 'text-red-600 bg-red-100',
    };
    return colors[rating] || 'text-gray-600 bg-gray-100';
  };

  const getSharpeRatingColor = (ratio) => {
    if (ratio > 2) return 'text-green-600';
    if (ratio > 1) return 'text-yellow-600';
    if (ratio > 0) return 'text-orange-600';
    return 'text-red-600';
  };

  const getSharpeRatingText = (ratio) => {
    if (ratio > 3) return 'Excellent';
    if (ratio > 2) return 'Very Good';
    if (ratio > 1) return 'Good';
    if (ratio > 0) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-bold text-gray-900">Risk Metrics</h2>
      </div>

      <div className="space-y-4">
        {/* Overall Risk Rating */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Risk Rating</span>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(
                riskRating
              )}`}
            >
              {riskRating}
            </span>
          </div>
        </div>

        {/* Volatility */}
        <div className="p-3 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Portfolio Volatility</span>
            </div>
            <span className="text-lg font-bold text-blue-700">{volatility.toFixed(2)}%</span>
          </div>
          <div className="w-full h-2 bg-blue-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(volatility * 2, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-600 mt-2">
            Annualized price fluctuation measure
          </p>
        </div>

        {/* Sharpe Ratio */}
        <div className="p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-100">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Sharpe Ratio</span>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-green-700">{sharpeRatio.toFixed(2)}</div>
              <div className={`text-xs font-semibold ${getSharpeRatingColor(sharpeRatio)}`}>
                {getSharpeRatingText(sharpeRatio)}
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-600">Risk-adjusted return measure</p>
        </div>

        {/* Diversification */}
        <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-700 mb-1">Diversification</div>
              <div className="text-xs text-gray-600">{holdingsCount} holdings</div>
            </div>
            <div className="text-right">
              {diversified ? (
                <div className="flex items-center gap-1 text-green-600">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-semibold">Diversified</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-orange-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm font-semibold">Add More</span>
                </div>
              )}
            </div>
          </div>
          {!diversified && (
            <p className="text-xs text-orange-600 mt-2">
              Recommended: 5+ holdings for diversification
            </p>
          )}
        </div>

        {/* Individual Stock Risks */}
        {data.individual_stocks && data.individual_stocks.length > 0 && (
          <div className="pt-3 border-t border-gray-200">
            <div className="text-xs font-semibold text-gray-700 mb-2">Top Risky Holdings</div>
            <div className="space-y-2">
              {data.individual_stocks
                .sort((a, b) => b.volatility - a.volatility)
                .slice(0, 3)
                .map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="font-medium text-gray-700">{stock.symbol}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600">
                        {(stock.volatility * 100).toFixed(1)}% vol
                      </span>
                      <span className={getRiskColor(stock.risk_rating).split(' ')[0]}>
                        •
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          Based on 1-year historical data • Updated daily
        </p>
      </div>
    </div>
  );
}

export default RiskMetricsPanel;
