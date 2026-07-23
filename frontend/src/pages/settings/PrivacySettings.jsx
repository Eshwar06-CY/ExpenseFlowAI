import React, { useState } from 'react';
import { Shield, Brain, Activity, Target, MessageSquare, Trash2, ShieldAlert } from 'lucide-react';
import PrivacyCard from '../../components/Personalization/PrivacyCard';
import ToggleSetting from '../../components/Personalization/ToggleSetting';
import ResetLearningModal from '../../components/Personalization/ResetLearningModal';

const PrivacySettings = ({ preferences, onUpdatePreference, onResetAllData, isSaving }) => {
  const p = preferences || {};
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const handleConfirmReset = async () => {
    setIsResetting(true);
    try {
      await onResetAllData();
      setResetModalOpen(false);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Privacy Center Controls */}
      <PrivacyCard
        title="Privacy & Data Governance Controls"
        description="Full control over what application data the AI assistant is permitted to track or remember."
      >
        <ToggleSetting
          label="Enable AI Learning"
          description="Allow AI to observe pattern consistency and refine personalized recommendations."
          icon={Brain}
          enabled={p.enable_ai_learning ?? true}
          onChange={(val) => onUpdatePreference('enable_ai_learning', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Persistent Memory"
          description="Allow AI to remember user preferences and financial goals across sessions."
          icon={Shield}
          enabled={p.enable_memory ?? true}
          onChange={(val) => onUpdatePreference('enable_memory', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Behavior Tracking"
          description="Track recommendation acceptance and ignored advice frequency."
          icon={Activity}
          enabled={p.enable_behavior_tracking ?? true}
          onChange={(val) => onUpdatePreference('enable_behavior_tracking', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Goal Tracking"
          description="Track goal progress velocity for personalized timeline forecasts."
          icon={Target}
          enabled={p.enable_goal_tracking ?? true}
          onChange={(val) => onUpdatePreference('enable_goal_tracking', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Communication Preference Learning"
          description="Automatically adapt tone and detail level based on interaction style."
          icon={MessageSquare}
          enabled={p.enable_communication_preference_learning ?? true}
          onChange={(val) => onUpdatePreference('enable_communication_preference_learning', val)}
          disabled={isSaving}
        />
      </PrivacyCard>

      {/* Delete All Learned Data Section */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-rose-100 dark:border-rose-900/40 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 pr-4">
            <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 mt-0.5">
              <ShieldAlert size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">Delete All Learned AI Data</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-lg">
                Permanently purge all learned behaviors, AI memories, confidence scores, and recommendation history. Resets AI settings to default baseline.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setResetModalOpen(true)}
            className="inline-flex items-center px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 shadow-sm shadow-rose-600/30 transition-all flex-shrink-0"
          >
            <Trash2 size={14} className="mr-1.5" />
            Forget Everything
          </button>
        </div>
      </div>

      {/* Reset Modal */}
      <ResetLearningModal
        isOpen={resetModalOpen}
        onClose={() => setResetModalOpen(false)}
        onConfirm={handleConfirmReset}
        isResetting={isResetting}
      />
    </div>
  );
};

export default PrivacySettings;
