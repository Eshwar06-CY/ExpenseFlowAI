import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Search, LogOut, User, Check, X, Menu, Wallet, CreditCard, Calendar, Target, Tag, Sparkles, RefreshCw, Users, Sun, Moon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import api from '../../services/api';

const Navbar = ({ onMenuClick }) => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const searchContainerRef = useRef(null);

  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const res = await api.get('/notifications?is_read=false');
      setNotifications(res.data);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [user]);

  // Click outside search or notifications ref
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {
        setShowSearchDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  // Debounced search query handler
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults(null);
      setSearching(false);
      return;
    }

    const delayDebounceFn = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get(`/search/?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(res.data);
      } catch (err) {
        console.error('Error performing global search:', err);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications([]);
    } catch (err) {
      console.error('Error marking all read:', err);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(notifications.filter(n => n.id !== id));
    } catch (err) {
      console.error('Error marking read:', err);
    }
  };

  const unreadCount = notifications.length;

  const handleSearchResultClick = (path) => {
    setShowSearchDropdown(false);
    setSearchQuery('');
    navigate(path);
  };

  const isSearchEmpty = (results) => {
    if (!results) return true;
    return (
      results.accounts.length === 0 &&
      results.transactions.length === 0 &&
      results.bills.length === 0 &&
      results.goals.length === 0 &&
      results.categories.length === 0 &&
      results.notifications.length === 0
    );
  };

  return (
    <header className="h-16 w-full flex items-center justify-between px-4 md:px-6 sticky top-0 z-40 bg-dark-950/40 dark:bg-dark-950/40 light:bg-white/85 backdrop-blur-xl border-b border-dark-900/40 dark:border-dark-900/40 light:border-slate-200 transition-colors duration-300">
      {/* Left: hamburger + search */}
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 text-dark-400 dark:text-dark-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:bg-dark-900/60 dark:hover:bg-dark-900/60 light:hover:bg-slate-100 rounded-xl transition-all duration-200"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Search Bar Container */}
        <div className="relative" ref={searchContainerRef}>
          <div className="hidden md:flex items-center gap-2.5 bg-dark-900/80 dark:bg-dark-900/80 light:bg-slate-100 border border-dark-850 dark:border-dark-850 light:border-slate-200 rounded-xl px-3.5 py-2 w-80 focus-within:border-brand-500/60 focus-within:ring-1 focus-within:ring-brand-500/30 transition-all duration-300">
            <Search className="w-4 h-4 text-dark-500 light:text-slate-400" />
            <input
              type="text"
              placeholder="Search workspaces & history..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowSearchDropdown(true);
              }}
              onFocus={() => setShowSearchDropdown(true)}
              className="bg-transparent text-xs text-dark-200 dark:text-dark-200 light:text-slate-800 outline-none w-full placeholder-dark-500 light:placeholder-slate-400 font-medium"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="text-dark-500 hover:text-dark-200 light:hover:text-slate-700 transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Search Result Overlay Dropdown */}
          {showSearchDropdown && searchQuery.trim().length >= 2 && (
            <div className="absolute left-0 mt-2 w-[420px] rounded-2xl bg-dark-900/95 dark:bg-dark-900/95 light:bg-white border border-dark-800 dark:border-dark-800 light:border-slate-200 shadow-edl-depth z-50 overflow-hidden animate-fade-in text-xs max-h-[440px] overflow-y-auto backdrop-blur-xl">
              {searching ? (
                <div className="p-8 text-center text-dark-450 flex flex-col items-center gap-3">
                  <RefreshCw className="w-5 h-5 animate-spin text-brand-400" />
                  <span className="font-semibold tracking-wide">Searching workspace...</span>
                </div>
              ) : isSearchEmpty(searchResults) ? (
                <div className="p-8 text-center text-dark-450 italic font-medium">
                  No matching entries found.
                </div>
              ) : (
                <div className="p-3 space-y-4">
                  {/* Accounts */}
                  {searchResults?.accounts.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Accounts</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.accounts.map(a => (
                          <button
                            key={a.id}
                            onClick={() => handleSearchResultClick('/dashboard/accounts')}
                            className="w-full text-left px-3 py-2 hover:bg-dark-800/80 rounded-xl flex items-center justify-between text-dark-200 transition-colors"
                          >
                            <span className="flex items-center gap-2.5 truncate font-semibold">
                              <Wallet className="w-4 h-4 text-savings shrink-0" />
                              <span className="truncate">{a.name}</span>
                            </span>
                            <span className="font-extrabold text-dark-50 shrink-0">${a.balance.toLocaleString()}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Transactions */}
                  {searchResults?.transactions.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Transactions</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.transactions.map(t => (
                          <button
                            key={t.id}
                            onClick={() => handleSearchResultClick(t.type === 'income' ? '/dashboard/income' : '/dashboard/expenses')}
                            className="w-full text-left px-3 py-2 hover:bg-dark-800/80 rounded-xl flex items-center justify-between text-dark-200 transition-colors"
                          >
                            <span className="flex items-center gap-2.5 truncate font-semibold">
                              <CreditCard className="w-4 h-4 text-brand-400 shrink-0" />
                              <span className="truncate">{t.description}</span>
                            </span>
                            <span className={`font-extrabold shrink-0 ${t.type === 'income' ? 'text-income' : 'text-expenses'}`}>
                              {t.type === 'income' ? '+' : '-'}${t.amount.toLocaleString()}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Bills */}
                  {searchResults?.bills.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Bills</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.bills.map(b => (
                          <button
                            key={b.id}
                            onClick={() => handleSearchResultClick('/dashboard/bills')}
                            className="w-full text-left px-3 py-2 hover:bg-dark-800/80 rounded-xl flex items-center justify-between text-dark-200 transition-colors"
                          >
                            <span className="flex items-center gap-2.5 truncate font-semibold">
                              <Calendar className="w-4 h-4 text-investments shrink-0" />
                              <span className="truncate">{b.name}</span>
                            </span>
                            <span className="font-extrabold text-dark-50 shrink-0">${b.amount.toLocaleString()}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Goals */}
                  {searchResults?.goals.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Goals</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.goals.map(g => (
                          <button
                            key={g.id}
                            onClick={() => handleSearchResultClick('/dashboard/goals')}
                            className="w-full text-left px-3 py-2 hover:bg-dark-800/80 rounded-xl flex items-center justify-between text-dark-200 transition-colors"
                          >
                            <span className="flex items-center gap-2.5 truncate font-semibold">
                              <Target className="w-4 h-4 text-income shrink-0" />
                              <span className="truncate">{g.name}</span>
                            </span>
                            <span className="text-dark-400 font-bold shrink-0">${g.current_amount.toLocaleString()} / ${g.target_amount.toLocaleString()}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Categories */}
                  {searchResults?.categories.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Categories</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.categories.map(c => (
                          <button
                            key={c.id}
                            onClick={() => handleSearchResultClick('/dashboard/categories')}
                            className="w-full text-left px-3 py-2 hover:bg-dark-800/80 rounded-xl flex items-center gap-2.5 text-dark-200 transition-colors font-semibold"
                          >
                            <Tag className="w-4 h-4 shrink-0" style={{ color: c.color }} />
                            <span>{c.name}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Workspace Members */}
                  {searchResults?.members?.length > 0 && (
                    <div>
                      <h4 className="px-2 py-1 text-[10px] font-extrabold uppercase text-dark-500 tracking-widest">Workspace Members</h4>
                      <div className="space-y-0.5 mt-1">
                        {searchResults.members.map(m => (
                          <div
                            key={m.id}
                            className="w-full px-3 py-2 rounded-xl flex items-center justify-between text-dark-250 hover:bg-dark-800/40"
                          >
                            <span className="flex items-center gap-2.5 truncate font-semibold">
                              <Users className="w-4 h-4 text-brand-400 shrink-0" />
                              <span className="truncate">{m.name}</span>
                            </span>
                            <span className="text-[10px] text-dark-400 font-mono shrink-0">{m.email}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Brand logo for mobile screens */}
      <div className="md:hidden flex items-center gap-2">
        <img src="/branding/logo-icon.png" alt="ExpenseFlow AI Logo" className="w-7 h-7 object-contain" />
        <span className="font-extrabold text-sm tracking-tight text-dark-50 dark:text-dark-50 light:text-slate-900">
          ExpenseFlow
        </span>
      </div>

      {/* Right side Profile, Theme Toggle & Dues */}
      <div className="flex items-center gap-3.5">
        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2.5 text-dark-400 dark:text-dark-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 bg-dark-900/50 dark:bg-dark-900/50 light:bg-slate-100 border border-dark-850 dark:border-dark-850 light:border-slate-200 rounded-xl transition-all active:scale-95 duration-200"
          title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
          aria-label="Toggle dark/light theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
        </button>
        {/* Notifications Bell Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="relative p-2.5 text-dark-400 hover:text-white bg-dark-900/50 hover:bg-dark-900 border border-dark-850 rounded-xl transition-all active:scale-95 duration-200"
            aria-label="Toggle notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4.5 h-4.5 rounded-full bg-expenses text-[9px] font-bold text-white flex items-center justify-center shadow-lg shadow-expenses/20 animate-pulse">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {isOpen && (
            <div className="absolute right-0 mt-3 w-80 rounded-2xl bg-dark-900 border border-dark-800 shadow-edl-depth z-50 overflow-hidden animate-fade-in backdrop-blur-xl">
              <div className="p-4 border-b border-dark-850 bg-dark-950/80 flex justify-between items-center">
                <span className="text-xs font-bold text-dark-100 tracking-wide">Workspace Alerts</span>
                {unreadCount > 0 && (
                  <button 
                    onClick={handleMarkAllRead} 
                    className="text-[10px] text-brand-400 hover:text-brand-300 font-bold flex items-center gap-1"
                  >
                    <Check className="w-3.5 h-3.5" /> Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-dark-850/50">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center text-xs text-dark-450 font-medium">
                    No pending notifications. Clear!
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div key={notif.id} className="p-3.5 hover:bg-dark-850/45 transition-colors flex justify-between gap-3 items-start">
                      <div className="space-y-1">
                        <p className="text-xs font-bold text-dark-100">{notif.title}</p>
                        <p className="text-[11px] text-dark-400 leading-relaxed">{notif.message}</p>
                        <p className="text-[9px] text-dark-500 font-medium">
                          {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <button 
                        onClick={() => handleMarkRead(notif.id)}
                        className="text-dark-500 hover:text-white p-0.5"
                        title="Dismiss"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="h-5 w-[1px] bg-dark-850/70 hidden sm:block"></div>

        {user ? (
          <div className="flex items-center gap-3">
            <div className="hidden sm:block text-right">
              <p className="text-xs font-bold text-dark-100 tracking-tight leading-none">{user.name}</p>
              <p className="text-[10px] text-dark-450 font-medium mt-1 leading-none">{user.email}</p>
            </div>
            
            <div className="group relative">
              <button 
                className="flex items-center justify-center w-9 h-9 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 hover:border-brand-500/40 hover:bg-brand-500/20 transition-all active:scale-95 duration-200"
                aria-label="User profile settings"
              >
                <User className="w-4 h-4" />
              </button>
              
              {/* Dropdown Menu */}
              <div className="absolute right-0 mt-3 w-48 rounded-xl bg-dark-900 border border-dark-800 shadow-edl-depth opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 overflow-hidden backdrop-blur-xl">
                <div className="p-2 space-y-0.5">
                  <Link
                    to="/dashboard/profile"
                    className="flex items-center gap-2 px-3.5 py-2.5 text-xs font-bold text-dark-300 hover:bg-dark-850 hover:text-white rounded-lg transition-colors"
                  >
                    <User className="w-4 h-4" />
                    Profile Details
                  </Link>
                  <div className="h-[1px] bg-dark-850/60 my-1"></div>
                  <button
                    onClick={logout}
                    className="w-full flex items-center gap-2 px-3.5 py-2.5 text-xs font-bold text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-lg transition-colors text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout Account
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-xs font-extrabold text-brand-400 hover:text-brand-300 transition-colors uppercase tracking-wider">
              Log In
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;
