import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, ArrowUpRight, ArrowDownLeft, Settings, Sparkles, Landmark, Tag, RefreshCw, Sliders, Target, Calendar, RotateCw, FileText, X, Bell, FileSpreadsheet, RotateCcw, LineChart, Heart, Users, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const Sidebar = ({ mobile = false, onClose }) => {
  const { isDark } = useTheme();
  const [showAdvanced, setShowAdvanced] = useState(false);

  const coreItems = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Where my money is (Accounts)', to: '/dashboard/accounts', icon: Landmark },
    { name: 'Money coming in (Income)', to: '/dashboard/income', icon: ArrowDownLeft },
    { name: 'Money going out (Expenses)', to: '/dashboard/expenses', icon: ArrowUpRight },
    { name: 'Spending limits (Budgets)', to: '/dashboard/budgets', icon: Sliders },
    { name: 'Saving targets (Goals)', to: '/dashboard/goals', icon: Target },
    { name: 'Settings', to: '/dashboard/settings', icon: Settings },
  ];

  const advancedItems = [
    { name: 'How healthy is my pocket?', to: '/dashboard/health', icon: Heart },
    { name: 'Future money estimator', to: '/dashboard/forecast', icon: LineChart },
    { name: 'Pocket Insights', to: '/dashboard/insights', icon: Sparkles },
    { name: 'Move money (Transfers)', to: '/dashboard/transfers', icon: RefreshCw },
    { name: 'Category tags', to: '/dashboard/categories', icon: Tag },
    { name: 'Bills to pay', to: '/dashboard/bills', icon: Calendar },
    { name: 'Repeating items', to: '/dashboard/recurring', icon: RotateCw },
    { name: 'Statements & Reports', to: '/dashboard/reports', icon: FileText },
    { name: 'All activity history', to: '/dashboard/timeline', icon: Calendar },
    { name: 'Import bank statement', to: '/dashboard/import-wizard', icon: FileSpreadsheet },
    { name: 'Import History', to: '/dashboard/import-history', icon: RotateCcw },
    { name: 'Automatic shortcuts', to: '/dashboard/automations', icon: Zap },
    { name: 'Shared spaces', to: '/dashboard/workspaces', icon: Users },
    { name: 'Alerts & Updates', to: '/dashboard/notifications', icon: Bell },
  ];

  return (
    <aside className={`w-64 bg-dark-950/80 dark:bg-dark-950/80 light:bg-white/95 backdrop-blur-xl border-r border-dark-900/60 dark:border-dark-900/60 light:border-slate-200 h-screen flex flex-col ${mobile ? '' : 'fixed left-0 top-0'} z-30 transition-all duration-300`}>
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-dark-900/50 dark:border-dark-900/50 light:border-slate-200 bg-dark-950/45 dark:bg-dark-950/45 light:bg-slate-50/50">
        <div className="flex items-center gap-2.5">
          <img
            src={isDark ? "/branding/logo-dark.png" : "/branding/logo-light.png"}
            alt="ExpenseFlow AI"
            className="h-8 object-contain"
          />
        </div>
        {mobile && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-dark-400 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:bg-dark-900 transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Links using custom EDL nav pills */}
      <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto custom-scrollbar">
        {coreItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.to}
              end={item.to === '/dashboard'}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 group border ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-500/8 to-transparent text-brand-400 border-brand-500/20 shadow-md shadow-brand-500/[0.02]'
                    : 'text-dark-400 hover:text-dark-200 hover:bg-dark-900/40 border-transparent hover:translate-x-1'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${isActive ? 'text-brand-400' : 'text-dark-500 group-hover:text-dark-350'}`} />
                  {item.name}
                </>
              )}
            </NavLink>
          );
        })}

        <div className="pt-2 border-t border-dark-900/30 my-2" />

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-xs font-bold text-brand-400 hover:bg-dark-900/40 transition-all border border-transparent hover:border-brand-500/10"
        >
          <span>{showAdvanced ? 'Hide advanced tools' : 'Show advanced tools'}</span>
          {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {showAdvanced && advancedItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-xs font-bold transition-all duration-200 group border ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-500/8 to-transparent text-brand-400 border-brand-500/20 shadow-md shadow-brand-500/[0.02]'
                    : 'text-dark-400 hover:text-dark-200 hover:bg-dark-900/40 border-transparent hover:translate-x-1'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${isActive ? 'text-brand-400' : 'text-dark-500 group-hover:text-dark-350'}`} />
                  {item.name}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Premium Upgrade Banner */}
      <div className="p-5 m-4 rounded-2xl bg-gradient-to-br from-dark-900 to-dark-950 border border-dark-850/80 relative overflow-hidden shadow-lg">
        <div className="absolute -right-4 -bottom-4 w-16 h-16 bg-brand-500/10 rounded-full blur-xl"></div>
        <div className="flex items-center gap-1.5 text-brand-400 mb-2">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span className="text-[9px] font-extrabold uppercase tracking-wider">Premium Access</span>
        </div>
        <h4 className="text-xs font-bold text-dark-100 mb-1 leading-tight">Dynamic Insights Scanner</h4>
        <p className="text-[10px] text-dark-400 leading-normal mb-3">Instant detection of recurring leaks and subscription cycles.</p>
        <button className="w-full py-2 rounded-xl bg-brand-600/25 border border-brand-500/30 text-brand-300 text-[11px] font-bold hover:bg-brand-600 hover:text-white transition-all active:scale-95 duration-200">
          Scan Inflows
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
