import React from 'react';
import { Inbox, PlusCircle } from 'lucide-react';
import Button from './Button';

const EmptyState = ({
  icon: Icon = Inbox,
  title = 'No entries recorded',
  description = 'Get started by creating your first record to begin tracking.',
  actionLabel,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in relative overflow-hidden">
      {/* Dynamic Background Light Ring */}
      <div className="absolute w-72 h-72 rounded-full bg-brand-500/5 blur-3xl -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

      {/* Tangible Animated Shield Icon Container */}
      <div className="relative mb-6">
        <div className="w-24 h-24 rounded-2xl bg-dark-900 border border-dark-800/80 flex items-center justify-center relative z-10 shadow-edl-card hover:scale-105 transition-all duration-300">
          <Icon className="w-10 h-10 text-brand-400" />
        </div>
        <div className="absolute -inset-4 rounded-3xl bg-brand-500/5 border border-brand-500/10 -z-0 animate-pulse" />
        <div className="absolute -inset-8 rounded-[2.5rem] bg-brand-500/[0.01] border border-brand-500/5 -z-10" />
      </div>

      <h3 className="text-xl font-extrabold text-dark-50 mb-2 font-sans tracking-tight">{title}</h3>
      <p className="text-sm text-dark-400 max-w-sm leading-relaxed mb-8 font-sans">{description}</p>

      {actionLabel && onAction && (
        <Button
          onClick={onAction}
          variant="primary"
          className="flex items-center gap-2 px-6 py-3 rounded-xl"
        >
          <PlusCircle className="w-4.5 h-4.5" />
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
