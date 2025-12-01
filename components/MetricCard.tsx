import React from 'react';

interface Props {
  label: string;
  value: string | number;
  prevValue?: string | number;
  isCurrency?: boolean;
  trend?: 'up' | 'down' | 'neutral';
  suffix?: string;
  highlight?: boolean;
}

export const MetricCard: React.FC<Props> = ({ label, value, prevValue, isCurrency, suffix, highlight }) => {
  const format = (v: string | number) => {
    if (typeof v === 'number') {
      if (isCurrency) return `$${v.toLocaleString()}`;
      return v.toLocaleString();
    }
    return v;
  };

  let delta = null;
  if (typeof value === 'number' && typeof prevValue === 'number' && prevValue !== 0) {
    const pct = ((value - prevValue) / prevValue) * 100;
    delta = pct.toFixed(1);
  }

  return (
    <div className={`flex flex-col p-6 rounded-3xl transition-all duration-300 ${highlight ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/20' : 'bg-white text-gray-900 shadow-sm hover:shadow-md'}`}>
      <span className={`text-xs font-semibold uppercase tracking-wider mb-2 ${highlight ? 'text-blue-100' : 'text-gray-400'}`}>
        {label}
      </span>
      <div className="mt-auto">
        <div className="text-3xl font-bold tracking-tight leading-none">
          {format(value)}{suffix}
        </div>
        
        {delta && !highlight && (
          <div className="mt-3 flex items-center gap-1.5">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${Number(delta) >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {Number(delta) >= 0 ? '+' : ''}{delta}%
            </span>
            <span className="text-xs text-gray-400">vs prev quarter</span>
          </div>
        )}
        
        {delta && highlight && (
           <div className="mt-3 flex items-center gap-1.5 opacity-90">
            <span className="text-xs font-medium bg-white/20 px-2 py-0.5 rounded-full">
               {Number(delta) >= 0 ? '+' : ''}{delta}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};