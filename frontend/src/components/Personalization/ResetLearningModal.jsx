import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

const ResetLearningModal = ({ isOpen, onClose, onConfirm, isResetting = false }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-md w-full p-6 shadow-2xl border border-gray-100 dark:border-gray-700/80 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400">
              <AlertTriangle size={22} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Forget Everything</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">Reset all AI learned intelligence</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="py-4 space-y-3">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            This action will permanently delete all application-level learned AI data for your account.
          </p>

          <div className="bg-rose-50/50 dark:bg-rose-950/20 p-3.5 rounded-xl border border-rose-100 dark:border-rose-900/40 text-xs text-rose-800 dark:text-rose-300 space-y-1.5">
            <p className="font-semibold text-rose-900 dark:text-rose-200">What will be deleted:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>All learned behavior observations (Dining, Savings, Bills, Goals)</li>
              <li>Persistent AI memory entries and risk preferences</li>
              <li>Personalization confidence scores</li>
              <li>Recommendation response history</li>
              <li>Reset all AI settings to baseline default values</li>
            </ul>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button
            type="button"
            onClick={onClose}
            disabled={isResetting}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isResetting}
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 shadow-sm shadow-rose-600/30 transition-all disabled:opacity-50"
          >
            <Trash2 size={14} className="mr-1.5" />
            {isResetting ? 'Resetting Data...' : 'Confirm Reset Everything'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResetLearningModal;
