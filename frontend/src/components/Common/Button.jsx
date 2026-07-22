import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

const Button = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  type = 'button',
  isLoading = false,
  disabled = false,
  ...props
}) => {
  const baseStyles = 'edl-btn inline-flex items-center justify-center font-bold text-sm tracking-wide transition-all focus:outline-none disabled:opacity-40 disabled:pointer-events-none active:scale-95 duration-250';
  
  const variants = {
    primary: 'edl-btn-primary text-white bg-gradient-to-tr from-brand-600 to-cyanFlow-500 shadow-lg shadow-brand-500/20 hover:shadow-brand-500/35 border border-brand-500/30',
    secondary: 'edl-btn-secondary bg-dark-900 border border-dark-800 text-dark-100 dark:text-dark-100 light:text-slate-800 light:bg-slate-100 light:border-slate-200 hover:border-brand-500/40 hover:bg-dark-850',
    outline: 'bg-transparent border border-dark-800 dark:border-dark-800 light:border-slate-300 text-dark-300 dark:text-dark-300 light:text-slate-700 hover:text-white light:hover:text-slate-900 hover:border-brand-500/30 hover:bg-brand-500/5',
    danger: 'bg-gradient-to-tr from-red-600 to-rose-500 text-white shadow-lg shadow-red-500/20 hover:shadow-red-500/35 border border-red-500/30',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-lg',
    md: 'px-4.5 py-2.5 text-sm rounded-xl',
    lg: 'px-6 py-3.5 text-base rounded-2xl',
  };

  return (
    <button
      type={type}
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  );
};

export default Button;
