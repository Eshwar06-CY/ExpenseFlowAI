import React, { useState, useEffect } from 'react';
import { Bell, Check, Trash2, Calendar, AlertTriangle, Info, ShieldAlert, Sparkles, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';

const Notifications = () => {
  const { addToast } = useToast();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  const [selectedCategory, setSelectedCategory] = useState('all'); // 'all', 'budget', 'bill', 'system'

  // Pagination states
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalCount, setTotalCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      // Query parameters
      const params = new URLSearchParams();
      if (filter === 'unread') params.append('is_read', 'false');
      if (filter === 'read') params.append('is_read', 'true');

      const res = await api.get(`/notifications/?${params.toString()}`);
      
      // Clientside category & pagination filter simulation for high performance
      let list = res.data;

      // Filter category by keywords
      if (selectedCategory !== 'all') {
        list = list.filter(n => {
          const title = n.title.toLowerCase();
          const msg = n.message.toLowerCase();
          if (selectedCategory === 'budget') return title.includes('budget') || msg.includes('budget') || title.includes('limit');
          if (selectedCategory === 'bill') return title.includes('bill') || msg.includes('bill') || title.includes('due');
          return !title.includes('budget') && !msg.includes('budget') && !title.includes('bill') && !msg.includes('bill');
        });
      }

      setTotalCount(list.length);
      
      // Page split
      const start = (page - 1) * limit;
      const end = start + limit;
      setNotifications(list.slice(start, end));
    } catch (err) {
      addToast('Failed to retrieve alerts.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [filter, selectedCategory, page]);

  const handleMarkRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      addToast('Alert marked as read.', 'success');
      fetchNotifications();
    } catch (err) {
      addToast('Failed to update status.', 'error');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      addToast('Alert dismissed.', 'success');
      fetchNotifications();
    } catch (err) {
      addToast('Failed to dismiss alert.', 'error');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      addToast('All alerts marked as read.', 'success');
      fetchNotifications();
    } catch (err) {
      addToast('Failed to mark all read.', 'error');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to dismiss and clear all notification logs?')) return;
    try {
      await api.delete('/notifications/');
      addToast('All notification logs cleared.', 'success');
      fetchNotifications();
    } catch (err) {
      addToast('Failed to clear logs.', 'error');
    }
  };

  const getAlertIcon = (title, message) => {
    const text = (title + ' ' + message).toLowerCase();
    if (text.includes('budget') || text.includes('limit') || text.includes('exceeded')) {
      return <ShieldAlert className="w-5 h-5 text-red-400" />;
    }
    if (text.includes('bill') || text.includes('due') || text.includes('payable')) {
      return <Calendar className="w-5 h-5 text-amber-400" />;
    }
    return <Info className="w-5 h-5 text-brand-400" />;
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-dark-50 tracking-tight flex items-center gap-2">
            <Bell className="w-8 h-8 text-brand-500" /> Notification Center
          </h2>
          <p className="text-dark-400 text-sm mt-1">Review transaction audits, budget alerts, and due bill reminders.</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={handleMarkAllRead}
            disabled={notifications.length === 0}
            className="flex items-center gap-1.5 py-2 px-3 text-xs"
          >
            <Check className="w-3.5 h-3.5" /> Mark all read
          </Button>
          <Button
            variant="secondary"
            onClick={handleClearAll}
            disabled={notifications.length === 0}
            className="flex items-center gap-1.5 py-2 px-3 text-xs !text-red-400 hover:!bg-red-500/10 border-red-500/20"
          >
            <Trash2 className="w-3.5 h-3.5" /> Dismiss all
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-dark-900 border border-dark-850 p-4 rounded-2xl flex flex-wrap gap-4 items-center justify-between text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => { setFilter('all'); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg font-semibold border transition-all ${
              filter === 'all'
                ? 'bg-brand-600/10 border-brand-500/30 text-brand-400'
                : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-dark-200'
            }`}
          >
            All Logs
          </button>
          <button
            onClick={() => { setFilter('unread'); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg font-semibold border transition-all ${
              filter === 'unread'
                ? 'bg-brand-600/10 border-brand-500/30 text-brand-400'
                : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-dark-200'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => { setFilter('read'); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg font-semibold border transition-all ${
              filter === 'read'
                ? 'bg-brand-600/10 border-brand-500/30 text-brand-400'
                : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-dark-200'
            }`}
          >
            Read Archive
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-dark-500" />
          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            className="bg-dark-950 border border-dark-800 rounded-lg px-2.5 py-1.5 text-xs text-dark-350 outline-none focus:border-brand-500"
          >
            <option value="all">All Alert Types</option>
            <option value="budget">Category Budgets</option>
            <option value="bill">Upcoming Bills</option>
            <option value="system">System & Accounts</option>
          </select>
        </div>
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map(n => (
            <div key={n} className="h-20 bg-dark-900 border border-dark-850 rounded-2xl"></div>
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <Card className="text-center py-16">
          <Bell className="w-12 h-12 text-dark-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-dark-200">Inbox Completely Clean</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-sm mx-auto leading-relaxed">
            There are no alerts matching the selected filters.
          </p>
        </Card>
      ) : (
        <div className="space-y-3.5">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-4 rounded-2xl border transition-all flex justify-between gap-4 items-start ${
                notif.is_read
                  ? 'bg-dark-900/50 border-dark-850/50 hover:border-dark-800'
                  : 'bg-brand-600/5 border-brand-500/20 hover:border-brand-500/30'
              }`}
            >
              <div className="flex gap-3 items-start min-w-0">
                <div className="p-2 bg-dark-950 border border-dark-800 rounded-xl shrink-0 mt-0.5">
                  {getAlertIcon(notif.title, notif.message)}
                </div>
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-dark-100 truncate">{notif.title}</span>
                    {!notif.is_read && (
                      <span className="px-1.5 py-0.5 rounded bg-brand-500 text-[8px] font-bold text-white shrink-0 uppercase tracking-wider">
                        New
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-dark-400 leading-relaxed break-words">{notif.message}</p>
                  <span className="text-[10px] text-dark-500 block">
                    {new Date(notif.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="flex gap-1.5 shrink-0">
                {!notif.is_read && (
                  <button
                    onClick={() => handleMarkRead(notif.id)}
                    className="p-2 hover:bg-dark-950 text-dark-400 hover:text-green-400 rounded-xl transition-colors"
                    title="Mark read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => handleDelete(notif.id)}
                  className="p-2 hover:bg-dark-950 text-dark-400 hover:text-red-400 rounded-xl transition-colors"
                  title="Dismiss alert"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {/* Pagination Controls */}
          <div className="bg-dark-900 border border-dark-850 px-4 py-3 rounded-2xl flex justify-between items-center text-xs select-none">
            <span className="text-dark-400 font-medium">
              Showing {(page - 1) * limit + 1}-{Math.min(page * limit, totalCount)} of {totalCount} alerts
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="xs"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="flex items-center gap-1 py-1 px-2.5 text-xs"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </Button>
              <Button
                variant="secondary"
                size="xs"
                disabled={page * limit >= totalCount}
                onClick={() => setPage(page + 1)}
                className="flex items-center gap-1 py-1 px-2.5 text-xs"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Notifications;
