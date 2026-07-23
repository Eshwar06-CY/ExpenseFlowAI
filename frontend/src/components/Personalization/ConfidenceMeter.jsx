import React from 'react';
import { Award, Info } from 'lucide-react';

const ConfidenceMeter = ({ confidence = 0.92, explanation }) => {
  const percentage = Math.round(confidence * 100);
  
  const getStatusColor = (pct) => {
    if (pct >= 85) return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800';
    if (pct >= 70) return 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800';
    return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800';
  };

  const getBarColor = (pct) => {
    if (pct >= 85) return 'bg-gradient-to-r from-emerald-500 to-teal-500';
    if (pct >= 70) return 'bg-gradient-to-r from-indigo-500 to-purple-500';
    return 'bg-gradient-to-r from-amber-500 to-orange-500';
  };

  return (
    <div className={`p-5 rounded-2xl border ${getStatusColor(percentage)} transition-all duration-300`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-white/80 dark:bg-gray-800/80 shadow-sm">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-gray-900 dark:text-white">AI Personalization Confidence</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">Based on financial habit consistency</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-black text-gray-900 dark:text-white">{percentage}%</span>
        </div>
      </div>

      {/* Meter Bar */}
      <div className="w-full bg-gray-200/80 dark:bg-gray-700/80 rounded-full h-3 overflow-hidden p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getBarColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="mt-3 flex items-start space-x-2 text-xs text-gray-600 dark:text-gray-300">
        <Info className="w-4 h-4 mt-0.5 flex-shrink-0 text-indigo-500" />
        <p>{explanation || "The assistant is confident because it has observed consistent financial behavior."}</p>
      </div>
    </div>
  );
};

export default ConfidenceMeter;
