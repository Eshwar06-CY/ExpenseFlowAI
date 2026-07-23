import React from 'react';
import { Sparkles, AlertCircle, HelpCircle } from 'lucide-react';

/**
 * Standardized Design System UI Primitives for ExpenseFlowAI
 */

// 1. Status Badge Component
export const StatusBadge = ({ type = 'info', children, className = '' }) => {
  const styles = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    error: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    info: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    neutral: 'bg-dark-850 text-dark-300 border-dark-800',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-extrabold uppercase tracking-wider border ${styles[type] || styles.info} ${className}`}>
      {children}
    </span>
  );
};

// 2. Metric KPI Card
export const MetricCard = ({ title, value, subtitle, icon: Icon, trend, className = '' }) => {
  return (
    <div className={`p-5 rounded-2xl bg-dark-900 border border-dark-800 hover:border-indigo-500/50 transition-all flex items-start justify-between space-x-4 shadow-md ${className}`}>
      <div className="space-y-1">
        <p className="text-xs text-dark-400 font-semibold uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-black text-white">{value}</p>
        {subtitle && <p className="text-[11px] text-dark-400">{subtitle}</p>}
      </div>

      {Icon && (
        <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex-shrink-0">
          <Icon size={20} />
        </div>
      )}
    </div>
  );
};

// 3. Shimmer Skeleton Component
export const SkeletonShimmer = ({ className = 'h-12 w-full rounded-2xl' }) => {
  return (
    <div className={`bg-dark-850/80 animate-pulse ${className}`} />
  );
};

// 4. Custom Tooltip Box
export const TooltipBox = ({ content, children }) => {
  return (
    <div className="relative group inline-block">
      {children}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-50 px-2.5 py-1 rounded-lg bg-dark-950 text-white text-[11px] font-medium border border-dark-800 whitespace-nowrap shadow-xl">
        {content}
      </div>
    </div>
  );
};
