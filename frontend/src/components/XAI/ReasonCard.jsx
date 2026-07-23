import React from 'react';
import { HelpCircle, CheckCircle2, AlertTriangle, Lightbulb } from 'lucide-react';

export const ReasonCard = ({ reason }) => (
  <div className="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 space-y-1.5">
    <div className="flex items-center space-x-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wider">
      <HelpCircle size={14} />
      <span>Why Was This Generated?</span>
    </div>
    <p className="text-xs text-dark-200 leading-relaxed">{reason}</p>
  </div>
);

export const AssumptionCard = ({ assumptions = [] }) => (
  <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
    <div className="flex items-center space-x-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider">
      <CheckCircle2 size={14} />
      <span>Key Assumptions</span>
    </div>
    <ul className="space-y-1 text-xs text-dark-300 list-disc list-inside">
      {assumptions.map((item, idx) => (
        <li key={idx}>{item}</li>
      ))}
    </ul>
  </div>
);

export const LimitationCard = ({ limitations = [] }) => (
  <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
    <div className="flex items-center space-x-1.5 text-xs font-bold text-rose-400 uppercase tracking-wider">
      <AlertTriangle size={14} />
      <span>Known Limitations</span>
    </div>
    <ul className="space-y-1 text-xs text-dark-300 list-disc list-inside">
      {limitations.map((item, idx) => (
        <li key={idx}>{item}</li>
      ))}
    </ul>
  </div>
);
