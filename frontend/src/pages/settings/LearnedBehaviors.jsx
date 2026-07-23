import React, { useState } from 'react';
import { Brain, Sparkles, AlertCircle } from 'lucide-react';
import BehaviorCard from '../../components/Personalization/BehaviorCard';
import ConfidenceMeter from '../../components/Personalization/ConfidenceMeter';

const LearnedBehaviors = ({ behaviors = [], confidence = 0.92, onDeleteBehavior }) => {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await onDeleteBehavior(id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Overall AI Confidence */}
      <ConfidenceMeter
        confidence={confidence}
        explanation="The assistant is confident because it has observed consistent financial behavior across your transactions, bills, and goals."
      />

      {/* Learned Behavior Observations Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center">
            <Brain className="w-5 h-5 mr-2 text-indigo-600 dark:text-indigo-400" />
            Learned Financial Habits & Observations
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Application-level observations derived from your historical financial interactions. Deleting an item removes only that specific observation.
          </p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
          {behaviors.length} Learned {behaviors.length === 1 ? 'Habit' : 'Habits'}
        </span>
      </div>

      {/* Behavior Cards Grid */}
      {behaviors.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {behaviors.map((b) => (
            <BehaviorCard
              key={b.id}
              id={b.id}
              category={b.category}
              observation={b.observation}
              confidence={b.confidence}
              onDelete={handleDelete}
              isDeleting={deletingId === b.id}
            />
          ))}
        </div>
      ) : (
        <div className="p-8 text-center bg-white dark:bg-gray-800 rounded-2xl border border-dashed border-gray-200 dark:border-gray-700">
          <Sparkles className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
          <h4 className="text-sm font-bold text-gray-900 dark:text-white">No Learned Behaviors Recorded</h4>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            As you log transactions, pay bills, and track goals, ExpenseFlowAI will adapt to your financial habits.
          </p>
        </div>
      )}
    </div>
  );
};

export default LearnedBehaviors;
