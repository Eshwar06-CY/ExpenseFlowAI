import React from 'react';

const PreferenceCard = ({ title, description, icon: Icon, children }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700/60 shadow-sm mb-6">
      <div className="flex items-center space-x-3 mb-4 pb-3 border-b border-gray-100 dark:border-gray-700/50">
        {Icon && (
          <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
            <Icon size={20} />
          </div>
        )}
        <div>
          <h3 className="text-base font-bold text-gray-900 dark:text-white">{title}</h3>
          {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
        </div>
      </div>
      <div>{children}</div>
    </div>
  );
};

export default PreferenceCard;
