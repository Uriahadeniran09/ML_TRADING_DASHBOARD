import { useQuery } from '@tanstack/react-query';
import { predictionsApi } from '../services/api';

export const useStocksWithPredictions = () => {
  return useQuery({
    queryKey: ['predictions-stocks'],
    queryFn: () => predictionsApi.getStocksWithPredictions(),
  });
};

export const usePredictions = (symbol, predictionDate = null) => {
  return useQuery({
    queryKey: ['predictions', symbol, predictionDate],
    queryFn: () => predictionsApi.getPredictions(symbol, predictionDate),
    enabled: !!symbol,
  });
};

export const usePredictionPath = (symbol, horizon, predictionDate = null) => {
  return useQuery({
    queryKey: ['prediction-path', symbol, horizon, predictionDate],
    queryFn: () => predictionsApi.getPredictionPath(symbol, horizon, predictionDate),
    enabled: !!symbol && !!horizon,
  });
};

export const useLatestPredictions = (symbol) => {
  return useQuery({
    queryKey: ['latest-predictions', symbol],
    queryFn: () => predictionsApi.getLatestPredictions(symbol),
    enabled: !!symbol,
  });
};
