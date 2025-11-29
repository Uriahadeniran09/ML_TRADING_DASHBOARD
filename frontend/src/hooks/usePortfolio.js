import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { portfolioApi, riskApi } from '../services/api';

// Hook to get or create portfolio for a user
export const usePortfolio = (userId = 'default_user') => {
  const queryClient = useQueryClient();

  // Try to get existing portfolio
  const { data, isLoading, error } = useQuery({
    queryKey: ['portfolio', userId],
    queryFn: async () => {
      try {
        const result = await portfolioApi.getPortfolioByUser(userId);
        return result;
      } catch (err) {
        // If portfolio doesn't exist, create one
        if (err.message.includes('not found') || err.message.includes('No portfolio found')) {
          const newPortfolio = await portfolioApi.createPortfolio(userId, 'My Portfolio');
          return newPortfolio;
        }
        throw err;
      }
    },
    staleTime: 1000 * 60, // 1 minute
    retry: false, // Don't retry on 404
  });

  // Manual create portfolio mutation
  const createMutation = useMutation({
    mutationFn: ({ userId, name }) => portfolioApi.createPortfolio(userId, name),
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolio']);
    },
  });

  return {
    portfolio: data?.portfolio,
    holdings: data?.holdings || [],
    isLoading,
    error,
    createPortfolio: createMutation.mutate,
  };
};

// Hook to get portfolio by ID
export const usePortfolioById = (portfolioId) => {
  return useQuery({
    queryKey: ['portfolio', portfolioId],
    queryFn: () => portfolioApi.getPortfolio(portfolioId),
    enabled: !!portfolioId,
    staleTime: 1000 * 60, // 1 minute
  });
};

// Hook to buy stock
export const useBuyStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ portfolioId, symbol, shares, amount }) =>
      portfolioApi.buyStock(portfolioId, symbol, shares, amount),
    onSuccess: (data, variables) => {
      // Invalidate portfolio queries to refresh data
      queryClient.invalidateQueries(['portfolio', variables.portfolioId]);
      queryClient.invalidateQueries(['portfolio']);
      queryClient.invalidateQueries(['transactions']);
      queryClient.invalidateQueries(['portfolio-risk']);
    },
  });
};

// Hook to sell stock
export const useSellStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ portfolioId, symbol, shares, amount }) =>
      portfolioApi.sellStock(portfolioId, symbol, shares, amount),
    onSuccess: (data, variables) => {
      // Invalidate portfolio queries to refresh data
      queryClient.invalidateQueries(['portfolio', variables.portfolioId]);
      queryClient.invalidateQueries(['portfolio']);
      queryClient.invalidateQueries(['transactions']);
      queryClient.invalidateQueries(['portfolio-risk']);
    },
  });
};

// Hook to get transaction history
export const useTransactions = (portfolioId, limit = 50) => {
  return useQuery({
    queryKey: ['transactions', portfolioId, limit],
    queryFn: () => portfolioApi.getTransactions(portfolioId, limit),
    enabled: !!portfolioId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

// Hook to get portfolio risk metrics
export const usePortfolioRisk = (portfolioId) => {
  return useQuery({
    queryKey: ['portfolio-risk', portfolioId],
    queryFn: () => riskApi.getPortfolioRisk(portfolioId),
    enabled: !!portfolioId,
    staleTime: 1000 * 60 * 15, // 15 minutes - risk doesn't change that fast
  });
};

// Hook to get stock risk metrics
export const useStockRisk = (symbol, period = '1y') => {
  return useQuery({
    queryKey: ['stock-risk', symbol, period],
    queryFn: () => riskApi.getStockRisk(symbol, period),
    enabled: !!symbol,
    staleTime: 1000 * 60 * 15, // 15 minutes
  });
};
