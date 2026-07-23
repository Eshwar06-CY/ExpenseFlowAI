import React from 'react';
import { Trash2, TrendingUp, Utensils, PiggyBank, CalendarCheck, Target, Sparkles } from 'lucide-react';

const categoryIcons = {
  Dining: Utensils,
  Savings: PiggyBank,
  Bills: CalendarCheck,
  Goals: Target,
};

const BehaviorCard = ({ id, category, observation, confidence, onDelete, isDeleting = false }) => {
  const Icon = categoryIcons[category] || Sparkles;
  const confidencePct = Math.round((confidence || 0.85) * 100);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700/60 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
              <Icon size={18} />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              {category}
            </span>
          </div>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800/50">
            Confidence {confidencePct}%
          </span>
        </div>

        <h4 className="text-sm font-semibold text-gray-900 dark:text-white leading-relaxed mb-4">
          {observation}
        </h4>
      </div>

      <div className="pt-3 border-t border-gray-100 dark:border-gray-700/50 flex justify-end">
        <button
          type="button"
          disabled={isDeleting}
          onClick={() => onDelete(id)}
          className="inline-flex items-center text-xs font-medium text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 transition-colors duration-150 disabled:opacity-50"
        >
          <Trash2 size={14} className="mr-1.5" />
          {isDeleting ? 'Deleting...' : 'Forget This Behavior'}
        </button>
      </div>
    </div>
  );
};

export default BehaviorCard;
