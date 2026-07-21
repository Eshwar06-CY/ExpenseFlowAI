import React from 'react';

const variants = {
  line: 'h-4 rounded',
  'line-sm': 'h-3 rounded',
  'line-lg': 'h-5 rounded',
  circle: 'rounded-full',
  card: 'h-28 rounded-xl',
  'card-lg': 'h-44 rounded-xl',
  'table-row': 'h-12 rounded-lg',
  avatar: 'w-10 h-10 rounded-full',
  badge: 'h-6 w-20 rounded-full',
};

const Skeleton = ({ variant = 'line', className = '', width }) => {
  const baseClass = variants[variant] || variants.line;
  return (
    <div
      className={`skeleton-shimmer bg-dark-850 ${baseClass} ${className}`}
      style={width ? { width } : undefined}
    />
  );
};

/** Pre-built skeleton layouts for common page patterns */

export const DashboardSkeleton = () => (
  <div className="space-y-8 animate-fade-in">
    {/* Briefing banner */}
    <Skeleton variant="card" className="w-full" />
    {/* Stat cards */}
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {[1, 2, 3, 4].map((n) => (
        <Skeleton key={n} variant="card" />
      ))}
    </div>
    {/* Chart + sidebar */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Skeleton variant="card-lg" className="lg:col-span-2" />
      <Skeleton variant="card-lg" />
    </div>
  </div>
);

export const TableSkeleton = ({ rows = 5 }) => (
  <div className="space-y-3 animate-fade-in">
    <div className="flex items-center justify-between">
      <Skeleton variant="line" width="200px" />
      <Skeleton variant="badge" />
    </div>
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="table-row" />
      ))}
    </div>
  </div>
);

export const CardSkeleton = ({ count = 3 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
    {Array.from({ length: count }).map((_, i) => (
      <Skeleton key={i} variant="card" />
    ))}
  </div>
);

export const FormSkeleton = () => (
  <div className="space-y-6 animate-fade-in max-w-lg">
    {[1, 2, 3].map((n) => (
      <div key={n} className="space-y-2">
        <Skeleton variant="line-sm" width="120px" />
        <Skeleton variant="table-row" />
      </div>
    ))}
    <Skeleton variant="line-lg" width="140px" className="mt-4" />
  </div>
);

export default Skeleton;
