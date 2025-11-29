import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

// ============================================================================
// STOCK DATA API CALLS
// ============================================================================

export const stocksApi = {
  // Get all available stocks
  getAllStocks: async (sector = null) => {
    const params = sector ? { sector } : {};
    return api.get('/api/stocks', { params });
  },

  // Get all sectors
  getSectors: async () => {
    return api.get('/api/sectors');
  },

  // Get current price for a stock
  getCurrentPrice: async (symbol) => {
    return api.get('/api/price', { params: { symbol } });
  },

  // Get historical price data
  getHistory: async (symbol, period = '6mo') => {
    return api.get('/api/history', { params: { symbol, period } });
  },

  // Get stock analysis summary
  getAnalysisSummary: async (symbol) => {
    return api.get(`/api/analysis/${symbol}/summary`);
  },

  // Compare multiple stocks
  compareStocks: async (symbols) => {
    const symbolsStr = Array.isArray(symbols) ? symbols.join(',') : symbols;
    return api.get('/api/analysis/compare', { params: { symbols: symbolsStr } });
  },
};

// ============================================================================
// PREDICTIONS API CALLS
// ============================================================================

export const predictionsApi = {
  // Get all stocks with predictions
  getStocksWithPredictions: async () => {
    return api.get('/api/predictions/stocks');
  },

  // Get all predictions for a stock (4 horizons)
  getPredictions: async (symbol, predictionDate = null) => {
    const params = predictionDate ? { prediction_date: predictionDate } : {};
    return api.get(`/api/predictions/${symbol}`, { params });
  },

  // Get detailed prediction path for graphing
  getPredictionPath: async (symbol, horizon, predictionDate = null) => {
    const params = { horizon };
    if (predictionDate) params.prediction_date = predictionDate;
    return api.get(`/api/predictions/${symbol}/path`, { params });
  },

  // Get latest predictions with price changes
  getLatestPredictions: async (symbol) => {
    return api.get(`/api/predictions/${symbol}/latest`);
  },

  // Compare predictions with actual prices
  comparePredictions: async (symbol, horizon) => {
    return api.get(`/api/predictions/${symbol}/compare`, { params: { horizon } });
  },
};

// ============================================================================
// PORTFOLIO API CALLS
// ============================================================================

export const portfolioApi = {
  // Create a new portfolio
  createPortfolio: async (userId, name = 'My Portfolio') => {
    return api.post('/api/portfolio/create', null, { params: { user_id: userId, name } });
  },

  // Get portfolio by ID
  getPortfolio: async (portfolioId) => {
    return api.get(`/api/portfolio/${portfolioId}`);
  },

  // Get portfolio by user ID
  getPortfolioByUser: async (userId) => {
    return api.get(`/api/portfolio/user/${userId}`);
  },

  // Buy stock
  buyStock: async (portfolioId, symbol, shares = null, amount = null) => {
    return api.post(`/api/portfolio/${portfolioId}/buy`, { symbol, shares, amount });
  },

  // Sell stock
  sellStock: async (portfolioId, symbol, shares = null, amount = null) => {
    return api.post(`/api/portfolio/${portfolioId}/sell`, { symbol, shares, amount });
  },

  // Get transaction history
  getTransactions: async (portfolioId, limit = 50) => {
    return api.get(`/api/portfolio/${portfolioId}/transactions`, { params: { limit } });
  },
};

// ============================================================================
// RISK API CALLS
// ============================================================================

export const riskApi = {
  // Get stock risk metrics
  getStockRisk: async (symbol, period = '1y') => {
    return api.get(`/api/risk/stock/${symbol}`, { params: { period } });
  },

  // Get portfolio risk metrics
  getPortfolioRisk: async (portfolioId) => {
    return api.get(`/api/risk/portfolio/${portfolioId}`);
  },
};

// ============================================================================
// DATABASE STATS API CALLS
// ============================================================================

export const dbApi = {
  // Get database statistics
  getStats: async () => {
    return api.get('/api/db/stats');
  },

  // Get detailed stock info from database
  getStockInfo: async (symbol) => {
    return api.get(`/api/db/stock/${symbol}`);
  },
};

export default api;
