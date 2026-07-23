import React, { useState, useEffect } from 'react';
import { Sliders, Calendar, Target, TrendingDown, Sparkles, Shield, Award, Mail, Bell } from 'lucide-react';
import api from '../../services/api';
import Button from '../Common/Button';
import { useToast } from '../../context/ToastContext';

const NotificationSettings = () => {
  const { addToast } = useToast();
  const [prefs, setPrefs] = useState({
    enable_budget_alerts: true,
    enable_bill_reminders: true,
    enable_goal_updates: true,
    enable_forecast_warnings: true,
    enable_ai_recommendations: true,
    enable_security_alerts: true,
    enable_achievements: true,
    enable_email_notifications: true,
    enable_in_app: true,
    digest_frequency: 'weekly'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        setLoading(true);
        const res = await api.get('/notifications/preferences');
        setPrefs(res.data);
      } catch (err) {
        console.warn('Failed to fetch preferences:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  const handleToggle = (key) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await api.put('/notifications/preferences', prefs);
      addToast('Notification preferences updated successfully!', 'success');
    } catch (err) {
      addToast('Failed to save preferences.', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="py-8 text-center text-xs text-dark-400 animate-pulse">Loading settings...</div>;
  }

  const items = [
    { key: 'enable_budget_alerts', label: 'Budget Threshold Alerts', desc: 'Notify when budgets are exceeded or near limit', icon: Sliders },
    { key: 'enable_bill_reminders', label: 'Bill Payment Reminders', desc: 'Alerts for upcoming, due, or overdue bills', icon: Calendar },
    { key: 'enable_goal_updates', label: 'Savings Goal Milestones', desc: 'Updates on 50%+ and completion milestones', icon: Target },
    { key: 'enable_forecast_warnings', label: 'Cashflow Forecast Warnings', desc: 'Alerts for low balance runway or deficit risks', icon: TrendingDown },
    { key: 'enable_ai_recommendations', label: 'AI Personal CFO Insights', desc: 'Weekly & monthly AI coaching summaries', icon: Sparkles },
    { key: 'enable_security_alerts', label: 'Security & Account Alerts', desc: 'Login detections, password changes, export alerts', icon: Shield },
    { key: 'enable_achievements', label: 'Milestones & Achievements', desc: 'Celebratory alerts for saving streaks & goals', icon: Award },
    { key: 'enable_email_notifications', label: 'Email Digest Notifications', desc: 'Receive summaries directly to registered email', icon: Mail },
    { key: 'enable_in_app', label: 'In-App Bell & Drawer Notifications', desc: 'Enable real-time notification bell updates', icon: Bell }
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h3 className="text-base font-bold text-white">Notification Delivery Preferences</h3>
        <p className="text-xs text-dark-400">Configure which channels and financial alert categories trigger notifications.</p>
      </div>

      <div className="space-y-3">
        {items.map(({ key, label, desc, icon: IconComp }) => (
          <div key={key} className="p-4 rounded-2xl bg-dark-900 border border-dark-800 flex items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <IconComp size={18} />
              </div>
              <div>
                <p className="text-xs font-bold text-white">{label}</p>
                <p className="text-[11px] text-dark-400">{desc}</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleToggle(key)}
              className={`w-12 h-6 rounded-full transition-all relative p-0.5 flex-shrink-0 ${
                prefs[key] ? 'bg-indigo-600' : 'bg-dark-800'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white transition-all transform ${
                  prefs[key] ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        ))}
      </div>

      {/* Frequency selector */}
      <div className="p-4 rounded-2xl bg-dark-900 border border-dark-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold text-white">Email Digest Frequency</p>
          <p className="text-[11px] text-dark-400">Choose how often periodic financial summaries are delivered</p>
        </div>
        <select
          value={prefs.digest_frequency}
          onChange={(e) => setPrefs((prev) => ({ ...prev, digest_frequency: e.target.value }))}
          className="bg-dark-950 border border-dark-800 rounded-xl px-3 py-1.5 text-xs text-dark-200 outline-none focus:border-indigo-500"
        >
          <option value="daily">Daily Briefing</option>
          <option value="weekly">Weekly Summary</option>
          <option value="off">Off (Real-Time Only)</option>
        </select>
      </div>

      <div className="pt-2 flex justify-end">
        <Button variant="primary" onClick={handleSave} loading={saving}>
          Save Preferences
        </Button>
      </div>
    </div>
  );
};

export default NotificationSettings;
