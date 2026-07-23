import React, { useState, useEffect } from 'react';
import {
  Bell, CheckCheck, RefreshCw, Search, Sliders, Calendar, Target,
  TrendingDown, Sparkles, Shield, Award, Settings, Inbox
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import NotificationCard from '../components/Notifications/NotificationCard';
import NotificationSettings from '../components/Notifications/NotificationSettings';
import EmptyState from '../components/Notifications/EmptyState';
import { useToast } from '../context/ToastContext';

const categoryFilters = [
  { id: 'all', label: 'All', icon: Bell },
  { id: 'unread', label: 'Unread', icon: Bell },
  { id: 'critical', label: 'Critical', icon: Bell },
  { id: 'budget', label: 'Budgets', icon: Sliders },
  { id: 'bills', label: 'Bills', icon: Calendar },
  { id: 'goals', label: 'Goals', icon: Target },
  { id: 'forecast', label: 'Forecast', icon: TrendingDown },
  { id: 'ai', label: 'AI Insights', icon: Sparkles },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'achievements', label: 'Achievements', icon: Award }
];

const groupNotificationsByDate = (items) => {
  const groups = { Today: [], Yesterday: [], 'This Week': [], Older: [] };
  const now = new Date();

  items.forEach((item) => {
    if (!item.created_at) {
      groups.Older.push(item);
      return;
    }
    const d = new Date(item.created_at);
    const diffHours = (now - d) / (1000 * 60 * 60);

    if (diffHours < 24 && now.getDate() === d.getDate()) {
      groups.Today.push(item);
    } else if (diffHours < 48) {
      groups.Yesterday.push(item);
    } else if (diffHours < 168) {
      groups['This Week'].push(item);
    } else {
      groups.Older.push(item);
    }
  });

  return groups;
};

const Notifications = () => {
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState('inbox'); // 'inbox' | 'preferences'
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const [items, setItems] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [criticalCount, setCriticalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = { limit: 100 };

      if (selectedFilter === 'unread') {
        params.unread_only = true;
      } else if (selectedFilter === 'critical') {
        params.priority = 'critical';
      } else if (selectedFilter !== 'all') {
        params.category = selectedFilter;
      }

      if (searchQuery) {
        params.search = searchQuery;
      }

      const res = await api.get('/notifications', { params });
      setItems(res.data.items || []);
      setUnreadCount(res.data.unread_count || 0);
      setCriticalCount(res.data.critical_count || 0);
    } catch (err) {
      console.warn('Failed to load notifications:', err);
      addToast('Failed to load notifications.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [selectedFilter, searchQuery]);

  const handleMarkRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      addToast('Failed to mark read.', 'error');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      setItems((prev) => prev.filter((n) => n.id !== id));
      addToast('Notification deleted.', 'success');
    } catch (err) {
      addToast('Failed to delete notification.', 'error');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.patch('/notifications/read-all');
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
      addToast('All notifications marked as read.', 'success');
    } catch (err) {
      addToast('Failed to mark all read.', 'error');
    }
  };

  const grouped = groupNotificationsByDate(items);

  return (
    <div className="space-y-8 pb-16 animate-in fade-in duration-300 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Bell size={20} />
            </span>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Financial Notification Center</h1>
          </div>
          <p className="text-xs text-dark-400 mt-1">
            Prioritized financial alerts, AI recommendations, budget limits, and security notifications.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => setActiveTab('inbox')}
            className={`px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center space-x-2 ${
              activeTab === 'inbox'
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                : 'bg-dark-900 text-dark-300 border-dark-800 hover:border-dark-700'
            }`}
          >
            <Inbox size={14} />
            <span>Notification Inbox</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px]">{unreadCount}</span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('preferences')}
            className={`px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center space-x-2 ${
              activeTab === 'preferences'
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                : 'bg-dark-900 text-dark-300 border-dark-800 hover:border-dark-700'
            }`}
          >
            <Settings size={14} />
            <span>Preferences</span>
          </button>
        </div>
      </div>

      {activeTab === 'preferences' ? (
        <Card className="p-6">
          <NotificationSettings />
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Filter & Search Toolbar */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-dark-900/60 p-4 rounded-2xl border border-dark-850">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
              <input
                type="text"
                placeholder="Search notifications..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-dark-500 outline-none focus:border-indigo-500"
              />
            </div>

            {/* Batch Controls */}
            <div className="flex items-center space-x-3 justify-between lg:justify-end">
              <button
                type="button"
                onClick={handleMarkAllRead}
                disabled={unreadCount === 0}
                className="px-3 py-2 rounded-xl bg-dark-950 hover:bg-dark-850 border border-dark-800 text-xs font-semibold text-indigo-400 disabled:opacity-40 flex items-center space-x-1.5"
              >
                <CheckCheck size={14} />
                <span>Mark All Read</span>
              </button>

              <button
                type="button"
                onClick={fetchNotifications}
                className="p-2 rounded-xl bg-dark-950 hover:bg-dark-850 border border-dark-800 text-dark-300 hover:text-white"
                title="Refresh"
              >
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none">
            {categoryFilters.map((cat) => {
              const IconComp = cat.icon;
              const isSelected = selectedFilter === cat.id;
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setSelectedFilter(cat.id)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap border transition-all flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/50 shadow-sm'
                      : 'bg-dark-900 text-dark-400 border-dark-850 hover:border-dark-700 hover:text-dark-200'
                  }`}
                >
                  <IconComp size={13} />
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>

          {/* Grouped Notifications List */}
          {loading ? (
            <div className="py-16 text-center text-xs text-dark-400 animate-pulse">Loading smart notifications...</div>
          ) : items.length === 0 ? (
            <EmptyState message="No notifications found in your inbox." />
          ) : (
            <div className="space-y-6">
              {Object.entries(grouped).map(([groupName, groupItems]) => {
                if (groupItems.length === 0) return null;
                return (
                  <div key={groupName} className="space-y-3">
                    <div className="flex items-center space-x-2 text-xs font-bold text-dark-400 uppercase tracking-wider">
                      <span>{groupName}</span>
                      <span className="text-dark-600">• {groupItems.length}</span>
                    </div>

                    <div className="space-y-3">
                      {groupItems.map((item) => (
                        <NotificationCard
                          key={item.id}
                          notification={item}
                          onMarkRead={handleMarkRead}
                          onDelete={handleDelete}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Notifications;
