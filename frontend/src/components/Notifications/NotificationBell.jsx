import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck, ChevronRight, X } from 'lucide-react';
import api from '../../services/api';

const NotificationBell = ({ onOpenDrawer }) => {
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentItems, setRecentItems] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const fetchUnreadNotifications = async () => {
    try {
      const res = await api.get('/notifications', { params: { limit: 5, unread_only: true } });
      setUnreadCount(res.data.unread_count || 0);
      setRecentItems(res.data.items || []);
    } catch (err) {
      console.warn('Failed to fetch notification badge count:', err);
    }
  };

  useEffect(() => {
    fetchUnreadNotifications();
    const interval = setInterval(fetchUnreadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await api.patch('/notifications/read-all');
      setUnreadCount(0);
      setRecentItems([]);
      fetchUnreadNotifications();
    } catch (err) {
      console.warn('Failed to mark all notifications read:', err);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => {
          if (onOpenDrawer) {
            onOpenDrawer();
          } else {
            setIsOpen(!isOpen);
          }
        }}
        className="relative p-2 rounded-xl text-dark-300 hover:text-white hover:bg-dark-850 transition-all focus:outline-none"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-extrabold text-white shadow-lg ring-2 ring-dark-950 animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Quick Dropdown Preview */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-dark-900 border border-dark-800 shadow-2xl p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-dark-800">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white">Notifications</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 text-[10px] font-bold border border-rose-500/20">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                >
                  <CheckCheck size={12} />
                  <span>Read All</span>
                </button>
              )}
              <button type="button" onClick={() => setIsOpen(false)} className="text-dark-400 hover:text-white p-1">
                <X size={14} />
              </button>
            </div>
          </div>

          <div className="py-2 max-h-72 overflow-y-auto space-y-2">
            {recentItems.length === 0 ? (
              <p className="text-xs text-dark-400 py-6 text-center">No unread notifications</p>
            ) : (
              recentItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    setIsOpen(false);
                    if (item.action_url) navigate(item.action_url);
                  }}
                  className="p-3 rounded-xl bg-dark-950 hover:bg-dark-850 border border-dark-850 cursor-pointer space-y-1 transition-all"
                >
                  <div className="flex items-center justify-between text-xs font-bold text-white">
                    <span>{item.title}</span>
                    <span
                      className={`text-[9px] uppercase px-1.5 py-0.5 rounded border ${
                        item.priority === 'critical'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      }`}
                    >
                      {item.priority}
                    </span>
                  </div>
                  <p className="text-[11px] text-dark-300 line-clamp-2">{item.message}</p>
                </div>
              ))
            )}
          </div>

          <div className="pt-3 border-t border-dark-800 text-center">
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate('/dashboard/notifications');
              }}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 inline-flex items-center space-x-1"
            >
              <span>Go to Notification Center</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
