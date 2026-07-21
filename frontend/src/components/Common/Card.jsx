import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

const Card = ({
  children,
  className,
  title,
  subtitle,
  footer,
  isGlass = false,
  interactive = false,
  accent = null, // 'income' | 'expenses' | 'savings' | 'goals' | 'investments' | 'debt'
  ...props
}) => {
  const accentBorders = {
    income: 'border-t-2 border-t-income shadow-income/5',
    expenses: 'border-t-2 border-t-expenses shadow-expenses/5',
    savings: 'border-t-2 border-t-savings shadow-savings/5',
    goals: 'border-t-2 border-t-goals shadow-goals/5',
    investments: 'border-t-2 border-t-investments shadow-investments/5',
    debt: 'border-t-2 border-t-debt shadow-debt/5',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'edl-card p-6 border border-dark-850',
          interactive && 'edl-card-interactive',
          accent && accentBorders[accent],
          className
        )
      )}
      {...props}
    >
      {/* Decorative inner light reflection */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.01] via-transparent to-transparent pointer-events-none" />
      
      {(title || subtitle) && (
        <div className="mb-5 relative z-10">
          {title && <h3 className="text-base font-bold text-dark-50 dark:text-dark-50 light:text-slate-900 tracking-tight font-sans">{title}</h3>}
          {subtitle && <p className="text-xs text-dark-400 dark:text-dark-400 light:text-slate-500 mt-1.5 font-sans leading-normal">{subtitle}</p>}
        </div>
      )}
      <div className="text-dark-200 dark:text-dark-200 light:text-slate-800 relative z-10">{children}</div>
      {footer && <div className="mt-6 pt-4 border-t border-dark-850/50 dark:border-dark-850/50 light:border-slate-200 text-xs text-dark-400 dark:text-dark-400 light:text-slate-500 relative z-10">{footer}</div>}
    </div>
  );
};

export default Card;
