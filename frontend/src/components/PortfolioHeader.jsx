import React from 'react';
import { TrendingUp, TrendingDown, Wallet, DollarSign, Package } from 'lucide-react';

function PortfolioHeader({ portfolio }) {
  if (!portfolio) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  const totalReturn = portfolio.total_return || 0;
  const totalReturnPercent = portfolio.total_return_percent || 0;
  const isPositive = totalReturn >= 0;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  const stats = [
    {
      label: 'Total Value',
      value: formatCurrency(portfolio.total_value),
      icon: DollarSign,
      iconBg: 'bg-primary-100',
      iconColor: 'text-primary-600',
    },
    {
      label: 'Total Return',
      value: formatCurrency(totalReturn),
      icon: isPositive ? TrendingUp : TrendingDown,
      iconBg: isPositive ? 'bg-green-100' : 'bg-red-100',
      iconColor: isPositive ? 'text-green-600' : 'text-red-600',
      subtext: `${isPositive ? '+' : ''}${totalReturnPercent.toFixed(2)}%`,
      subtextColor: isPositive ? 'text-green-600' : 'text-red-600',
    },
    {
      label: 'Cash Balance',
      value: formatCurrency(portfolio.cash_balance),
      icon: Wallet,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
    },
    {
      label: 'Invested',
      value: formatCurrency(portfolio.invested_value),
      icon: Package,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
    {
      label: 'Holdings',
      value: portfolio.number_of_holdings || 0,
      icon: Package,
      iconBg: 'bg-orange-100',
      iconColor: 'text-orange-600',
      isCount: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
      {stats.map((stat, index) => (
        <div key={index} className="card hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600 mb-1">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stat.isCount ? stat.value : stat.value}
              </p>
              {stat.subtext && (
                <p className={`text-sm font-semibold mt-1 ${stat.subtextColor}`}>
                  {stat.subtext}
                </p>
              )}
            </div>
            <div className={`${stat.iconBg} p-2 rounded-lg`}>
              <stat.icon className={`w-6 h-6 ${stat.iconColor}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default PortfolioHeader;
