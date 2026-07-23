import React from 'react';
import { BellOff } from 'lucide-react';

const EmptyState = ({ title = "All clear!", message = "You have no unread notifications or financial alerts at this moment." }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 md:p-12 text-center border border-dashed border-dark-800 rounded-3xl bg-dark-950/40 my-4">
      <div className="p-4 rounded-2xl bg-indigo-500/10 text-indigo-400 mb-4 border border-indigo-500/20">
        <BellOff size={32} />
      </div>
      <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>
      <p className="text-xs text-dark-400 max-w-sm mt-1 leading-relaxed">{message}</p>
    </div>
  );
};

export default EmptyState;
