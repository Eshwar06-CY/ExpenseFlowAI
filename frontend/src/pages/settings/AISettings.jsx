import React from 'react';
import { Bot, Sparkles, MessageSquare, Clock, Sliders, Lightbulb, Target, TrendingUp } from 'lucide-react';
import PreferenceCard from '../../components/Personalization/PreferenceCard';
import ToggleSetting from '../../components/Personalization/ToggleSetting';

const AISettings = ({ preferences, onUpdatePreference, isSaving }) => {
  const p = preferences || {};

  return (
    <div className="space-y-6">
      {/* 1. Core AI Controls */}
      <PreferenceCard
        title="Core AI Controls"
        description="Enable or disable AI personalization features and adaptive learning."
        icon={Bot}
      >
        <ToggleSetting
          label="Enable AI Personalization"
          description="Tailor AI insights and recommendations to your specific financial profile."
          icon={Sparkles}
          enabled={p.enable_ai_personalization ?? true}
          onChange={(val) => onUpdatePreference('enable_ai_personalization', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable AI Learning"
          description="Allow the application to learn your financial habits and recommendation preferences."
          icon={Sliders}
          enabled={p.enable_ai_learning ?? true}
          onChange={(val) => onUpdatePreference('enable_ai_learning', val)}
          disabled={isSaving}
        />
      </PreferenceCard>

      {/* 2. Coaching & Tone Preferences */}
      <PreferenceCard
        title="Coaching & Response Preferences"
        description="Customize the AI assistant's persona, detail level, and frequency."
        icon={MessageSquare}
      >
        {/* Coaching Style Selector */}
        <div className="py-4 border-b border-gray-100 dark:border-gray-800">
          <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-1">
            Coaching Style
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Choose the tone and approach of your AI Personal CFO.
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'friendly', name: 'Friendly', desc: 'Warm & encouraging' },
              { id: 'professional', name: 'Professional', desc: 'Direct & analytical' },
              { id: 'motivational', name: 'Motivational', desc: 'Goal & drive focused' },
            ].map((style) => (
              <button
                key={style.id}
                type="button"
                onClick={() => onUpdatePreference('coaching_style', style.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  (p.coaching_style || 'professional') === style.id
                    ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 ring-2 ring-indigo-500/20'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="text-xs font-bold">{style.name}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{style.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Recommendation Frequency */}
        <div className="py-4 border-b border-gray-100 dark:border-gray-800">
          <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-1">
            Recommendation Frequency
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            How often the assistant should present proactive financial suggestions.
          </p>
          <select
            value={p.recommendation_frequency || 'daily'}
            onChange={(e) => onUpdatePreference('recommendation_frequency', e.target.value)}
            disabled={isSaving}
            className="w-full max-w-xs px-3 py-2 rounded-xl text-xs border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="every_login">Every Login</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="important_only">Important Only</option>
          </select>
        </div>

        {/* Response Detail */}
        <div className="py-4">
          <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-1">
            Response Detail
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Length and depth of AI generated explanations.
          </p>
          <div className="flex space-x-3">
            {[
              { id: 'brief', label: 'Brief' },
              { id: 'balanced', label: 'Balanced' },
              { id: 'detailed', label: 'Detailed' },
            ].map((detail) => (
              <button
                key={detail.id}
                type="button"
                onClick={() => onUpdatePreference('response_detail', detail.id)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                  (p.response_detail || 'balanced') === detail.id
                    ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                }`}
              >
                {detail.label}
              </button>
            ))}
          </div>
        </div>
      </PreferenceCard>

      {/* 3. Feature Modules */}
      <PreferenceCard
        title="Smart Assistance Modules"
        description="Enable specific automated insights and guidance categories."
        icon={Lightbulb}
      >
        <ToggleSetting
          label="Enable Smart Suggestions"
          description="Contextual budget caps and bill savings tips."
          icon={Lightbulb}
          enabled={p.enable_smart_suggestions ?? true}
          onChange={(val) => onUpdatePreference('enable_smart_suggestions', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Goal Recommendations"
          description="Timeline acceleration and milestone projections."
          icon={Target}
          enabled={p.enable_goal_recommendations ?? true}
          onChange={(val) => onUpdatePreference('enable_goal_recommendations', val)}
          disabled={isSaving}
        />
        <ToggleSetting
          label="Enable Spending Insights"
          description="Automated spending anomaly detection and category spikes."
          icon={TrendingUp}
          enabled={p.enable_spending_insights ?? true}
          onChange={(val) => onUpdatePreference('enable_spending_insights', val)}
          disabled={isSaving}
        />
      </PreferenceCard>
    </div>
  );
};

export default AISettings;
