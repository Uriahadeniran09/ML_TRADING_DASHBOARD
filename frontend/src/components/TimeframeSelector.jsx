import React from 'react';

const TIMEFRAMES = [
  { value: '1w', label: '1W' },
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1Y' },
  { value: '2y', label: '2Y' },
];

const TimeframeSelector = ({ selected, onChange }) => {
  return (
    <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
      {TIMEFRAMES.map((timeframe) => (
        <button
          key={timeframe.value}
          onClick={() => onChange(timeframe.value)}
          className={`
            px-4 py-2 rounded-md font-medium text-sm transition-all duration-200
            ${
              selected === timeframe.value
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          {timeframe.label}
        </button>
      ))}
    </div>
  );
};

export default TimeframeSelector;
