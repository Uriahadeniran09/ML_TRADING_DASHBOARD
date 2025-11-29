import { useQuery } from '@tanstack/react-query';
import { stocksApi } from '../services/api';

export const useStocks = (sector = null) => {
  return useQuery({
    queryKey: ['stocks', sector],
    queryFn: () => stocksApi.getAllStocks(sector),
  });
};

export const useSectors = () => {
  return useQuery({
    queryKey: ['sectors'],
    queryFn: () => stocksApi.getSectors(),
  });
};

export const useCurrentPrice = (symbol) => {
  return useQuery({
    queryKey: ['price', symbol],
    queryFn: () => stocksApi.getCurrentPrice(symbol),
    enabled: !!symbol,
    refetchInterval: 60000, // Refetch every minute for current price
  });
};

export const useStockHistory = (symbol, period = '6mo') => {
  return useQuery({
    queryKey: ['history', symbol, period],
    queryFn: () => stocksApi.getHistory(symbol, period),
    enabled: !!symbol,
  });
};

export const useStockAnalysis = (symbol) => {
  return useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => stocksApi.getAnalysisSummary(symbol),
    enabled: !!symbol,
  });
};
