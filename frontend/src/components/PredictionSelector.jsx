import React from 'react';
import { Brain, Sparkles } from 'lucide-react';

const PREDICTION_HORIZONS = [
  { value: '1day', label: '1D', days: 1 },
  { value: '1week', label: '1W', days: 5 },
  { value: '1month', label: '1M', days: 21 },
  { value: '6months', label: '6M', days: 126 },
];

const MODELS = [
  { value: 'lstm', label: 'LSTM', icon: Brain, enabled: true },
  { value: 'transformer', label: 'Transformer', icon: Sparkles, enabled: false },
];

const PredictionSelector = ({ 
  showPredictions, 
  onTogglePredictions,
  selectedModel,
  onSelectModel,
  selectedHorizon,
  onSelectHorizon,
}) => {
  return (
    <div className="space-y-4">
      {/* Prediction Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-600" />
          <span className="font-semibold text-gray-900">ML Predictions</span>
        </div>
        <button
          onClick={onTogglePredictions}
          className={`
            relative inline-flex h-6 w-11 items-center rounded-full transition-colors
            ${showPredictions ? 'bg-primary-600' : 'bg-gray-300'}
          `}
        >
          <span
            className={`
              inline-block h-4 w-4 transform rounded-full bg-white transition-transform
              ${showPredictions ? 'translate-x-6' : 'translate-x-1'}
            `}
          />
        </button>
      </div>

      {/* Model Selection */}
      {showPredictions && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Model
            </label>
            <div className="grid grid-cols-2 gap-2">
              {MODELS.map((model) => {
                const Icon = model.icon;
                return (
                  <button
                    key={model.value}
                    onClick={() => model.enabled && onSelectModel(model.value)}
                    disabled={!model.enabled}
                    className={`
                      relative p-3 rounded-lg border-2 transition-all duration-200
                      ${
                        selectedModel === model.value
                          ? 'border-primary-500 bg-primary-50'
                          : model.enabled
                          ? 'border-gray-300 bg-white hover:border-gray-400'
                          : 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4" />
                      <span className="font-medium text-sm">{model.label}</span>
                    </div>
                    {!model.enabled && (
                      <span className="absolute top-1 right-1 text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                        Coming Soon
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Horizon Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prediction Horizon
            </label>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
              {PREDICTION_HORIZONS.map((horizon) => (
                <button
                  key={horizon.value}
                  onClick={() => onSelectHorizon(horizon.value)}
                  className={`
                    flex-1 px-3 py-2 rounded-md font-medium text-sm transition-all duration-200
                    ${
                      selectedHorizon === horizon.value
                        ? 'bg-white text-primary-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }
                  `}
                >
                  {horizon.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default PredictionSelector;
