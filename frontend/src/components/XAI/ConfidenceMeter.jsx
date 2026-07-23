import React from 'react';
import { ShieldCheck, HelpCircle } from 'lucide-react';

const ConfidenceMeter = ({ confidence = 0.90 }) => {
  const pct = Math.round(confidence * 100);

  let colorClass = 'bg-emerald-500 text-emerald-400 border-emerald-500/20';
  let label = 'High Confidence';

  if (pct < 70) {
    colorClass = 'bg-rose-500 text-rose-400 border-rose-500/20';
    label = 'Low Confidence';
  } else if (pct < 85) {
    colorClass = 'bg-amber-500 text-amber-400 border-amber-500/20';
    label = 'Moderate Confidence';
  }

  return (
    <div className="flex items-center space-x-3 bg-dark-950 p-3 rounded-xl border border-dark-850">
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="text-white flex items-center space-x-1">
            <ShieldCheck size={14} className="text-indigo-400" />
            <span>AI Model Confidence</span>
          </span>
          <span className={`font-black ${colorClass.split(' ')[1]}`}>{pct}%</span>
        </div>

        <div className="w-full bg-dark-850 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${colorClass.split(' ')[0]}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default ConfidenceMeter;
