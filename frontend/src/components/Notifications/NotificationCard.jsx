import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle, Sliders, Calendar, Clock, Target, TrendingDown,
  Sparkles, Shield, Award, Bell, Check, Trash2, ArrowUpRight
} from 'lucide-react';
import WhyButton from '../XAI/WhyButton';
import ExplanationPanel from '../XAI/ExplanationPanel';

const categoryIcons = {
  budget: Sliders,
  bills: Calendar,
  goals: Target,
  forecast: TrendingDown,
  ai: Sparkles,
  security: Shield,
  achievements: Award,
  system: Bell
};

const formatTimeAgo = (isoStr) => {
  if (!isoStr) return '';
  const date = new Date(isoStr);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 172800) return 'Yesterday';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
};

const NotificationCard = ({ notification, onMarkRead, onDelete }) => {
  const navigate = useNavigate();
  const [showXAI, setShowXAI] = useState(false);
  const IconComp = categoryIcons[notification.category] || Bell;

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case 'critical':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'medium':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  const getActionButtonLabel = (url, cat) => {
    if (url === '/dashboard/bills' || cat === 'bills') return 'Pay Bill';
    if (url === '/dashboard/budgets' || cat === 'budget') return 'View Budget';
    if (url === '/dashboard/goals' || cat === 'goals') return 'View Goal';
    if (url === '/dashboard/forecast' || cat === 'forecast') return 'Open Forecast';
    if (url === '/dashboard/chat' || cat === 'ai') return 'Open AI Chat';
    return 'Take Action';
  };

  return (
    <div
      className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
        notification.is_read
          ? 'bg-dark-950/60 border-dark-850 opacity-80'
          : 'bg-dark-900 border-dark-800 shadow-md hover:border-indigo-500/40'
      }`}
    >
      <div className="flex items-start space-x-3.5 z-10">
        <div
          className={`p-2.5 rounded-xl flex-shrink-0 ${
            notification.priority === 'critical'
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              : notification.priority === 'high'
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
          }`}
        >
          <IconComp size={18} />
        </div>

        <div className="space-y-1">
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <span className="text-xs font-bold text-white">{notification.title}</span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getPriorityStyle(
                notification.priority
              )}`}
            >
              {notification.priority}
            </span>
            {!notification.is_read && (
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
            )}
          </div>

          <p className="text-xs text-dark-300 leading-relaxed">{notification.message}</p>

          <div className="flex items-center space-x-4 text-[11px] text-dark-400 pt-1">
            <span>{formatTimeAgo(notification.created_at)}</span>
            <span className="capitalize text-dark-500">• {notification.category}</span>
            <WhyButton onClick={() => setShowXAI(true)} label="Why?" />
          </div>

          {notification.action_url && (
            <div className="pt-2">
              <button
                type="button"
                onClick={() => navigate(notification.action_url)}
                className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all"
              >
                <span>{getActionButtonLabel(notification.action_url, notification.category)}</span>
                <ArrowUpRight size={12} />
              </button>
            </div>
          )}

          <ExplanationPanel
            feature="notification"
            targetId={String(notification.id)}
            isOpen={showXAI}
            onClose={() => setShowXAI(false)}
          />
        </div>
      </div>

      <div className="flex items-center space-x-1 flex-shrink-0">
        {!notification.is_read && (
          <button
            type="button"
            onClick={() => onMarkRead && onMarkRead(notification.id)}
            title="Mark as read"
            className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-800 transition-all"
          >
            <Check size={14} />
          </button>
        )}
        <button
          type="button"
          onClick={() => onDelete && onDelete(notification.id)}
          title="Delete notification"
          className="p-1.5 rounded-lg text-dark-400 hover:text-rose-400 hover:bg-dark-800 transition-all"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
};

export default NotificationCard;
