import React from 'react';
import { Database } from 'lucide-react';

const DataSourceChip = ({ label }) => {
  return (
    <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 text-[11px] font-semibold border border-indigo-500/20">
      <Database size={11} className="text-indigo-400" />
      <span>{label}</span>
    </span>
  );
};

export default DataSourceChip;
