import React, { useState, useEffect } from 'react';
import { X, CheckCheck, Filter } from 'lucide-react';
import api from '../../services/api';
import NotificationCard from './NotificationCard';
import EmptyState from './EmptyState';

const NotificationDrawer = ({ isOpen, onClose }) => {
  const [items, setItems] = useState([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [filterPriority, setFilterPriority] = useState('all');
  const [loading, setLoading] = useState(false);

  const fetchNotifications = async () => {
    if (!isOpen) return;
    try {
      setLoading(true);
      const res = await api.get('/notifications', {
        params: {
          unread_only: unreadOnly,
          priority: filterPriority !== 'all' ? filterPriority : undefined,
          limit: 30
        }
      });
      setItems(res.data.items || []);
    } catch (err) {
      console.warn('Failed to load drawer notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [isOpen, unreadOnly, filterPriority]);

  const handleMarkRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (err) {
      console.warn('Failed to mark read:', err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      setItems((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.warn('Failed to delete notification:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.patch('/notifications/read-all');
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.warn('Failed to mark all read:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-dark-900 border-l border-dark-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-dark-800 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Notification Center</h2>
              <p className="text-xs text-dark-400">Real-time financial alerts & AI recommendations</p>
            </div>
            <button type="button" onClick={onClose} className="p-2 rounded-xl text-dark-400 hover:text-white hover:bg-dark-850">
              <X size={18} />
            </button>
          </div>

          {/* Quick Filter Bar */}
          <div className="p-4 bg-dark-950/60 border-b border-dark-800 flex items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setUnreadOnly(!unreadOnly)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold border transition-all ${
                  unreadOnly
                    ? 'bg-indigo-600 text-white border-indigo-500'
                    : 'bg-dark-900 text-dark-300 border-dark-800 hover:border-dark-700'
                }`}
              >
                Unread Only
              </button>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="bg-dark-900 border border-dark-800 rounded-xl px-2 py-1 text-xs text-dark-200 outline-none focus:border-indigo-500"
              >
                <option value="all">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <button
              type="button"
              onClick={handleMarkAllRead}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
            >
              <CheckCheck size={14} />
              <span>Read All</span>
            </button>
          </div>

          {/* Items Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {loading ? (
              <div className="py-12 text-center text-xs text-dark-400 animate-pulse">Loading notifications...</div>
            ) : items.length === 0 ? (
              <EmptyState message="No notifications match the active filter criteria." />
            ) : (
              items.map((item) => (
                <NotificationCard
                  key={item.id}
                  notification={item}
                  onMarkRead={handleMarkRead}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDrawer;
