import React from 'react';
import { HelpCircle, Sparkles } from 'lucide-react';

const WhyButton = ({ onClick, label = "Why?", className = "" }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-xl bg-indigo-500/10 hover:bg-indigo-600 text-indigo-400 hover:text-white border border-indigo-500/20 text-[11px] font-bold transition-all shadow-sm ${className}`}
      title="Click to see Explainable AI reasoning"
    >
      <Sparkles size={12} />
      <span>{label}</span>
    </button>
  );
};

export default WhyButton;
