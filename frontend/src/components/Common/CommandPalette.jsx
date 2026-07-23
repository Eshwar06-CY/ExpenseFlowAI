import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, LayoutDashboard, Sparkles, FileText, Landmark,
  ArrowDownLeft, ArrowUpRight, Sliders, Target, Calendar,
  LineChart, Heart, Bell, Settings, Command, X, ArrowRight
} from 'lucide-react';

const commands = [
  { id: 'dashboard', name: 'Dashboard', path: '/dashboard', category: 'Navigation', icon: LayoutDashboard },
  { id: 'chat', name: 'AI Streaming Chat', path: '/dashboard/chat', category: 'AI Assistant', icon: Sparkles },
  { id: 'digest', name: 'AI Digest Reports', path: '/dashboard/digest', category: 'Reports', icon: FileText },
  { id: 'accounts', name: 'Accounts & Balances', path: '/dashboard/accounts', category: 'Finance', icon: Landmark },
  { id: 'income', name: 'Income Tracker', path: '/dashboard/income', category: 'Finance', icon: ArrowDownLeft },
  { id: 'expenses', name: 'Expense Ledger', path: '/dashboard/expenses', category: 'Finance', icon: ArrowUpRight },
  { id: 'budgets', name: 'Budget Limits', path: '/dashboard/budgets', category: 'Planning', icon: Sliders },
  { id: 'goals', name: 'Savings Goals', path: '/dashboard/goals', category: 'Planning', icon: Target },
  { id: 'bills', name: 'Bills & Subscriptions', path: '/dashboard/bills', category: 'Planning', icon: Calendar },
  { id: 'forecast', name: '30-Day Forecast', path: '/dashboard/forecast', category: 'Intelligence', icon: LineChart },
  { id: 'health', name: 'Financial Health Score', path: '/dashboard/health', category: 'Intelligence', icon: Heart },
  { id: 'notifications', name: 'Alerts & Notifications', path: '/dashboard/notifications', category: 'System', icon: Bell },
  { id: 'settings', name: 'Settings & Privacy', path: '/dashboard/settings', category: 'System', icon: Settings },
];

const CommandPalette = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const filteredCommands = commands.filter((cmd) =>
    cmd.name.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (cmd) => {
    if (cmd.path) {
      navigate(cmd.path);
    }
    onClose();
    setQuery('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredCommands.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % Math.max(1, filteredCommands.length));
    } else if (e.key === 'Enter' && filteredCommands.length > 0) {
      e.preventDefault();
      handleSelect(filteredCommands[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-150">
      <div className="relative w-full max-w-xl bg-dark-900 border border-dark-800 rounded-3xl shadow-2xl overflow-hidden space-y-0">
        {/* Search Input Bar */}
        <div className="p-4 border-b border-dark-800 flex items-center space-x-3 bg-dark-950/80">
          <Search size={18} className="text-indigo-400 flex-shrink-0" />
          <input
            type="text"
            autoFocus
            placeholder="Type a command or search pages... (e.g. 'forecast', 'budgets', 'chat')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-sm text-white placeholder-dark-500 outline-none"
          />
          <span className="hidden sm:flex items-center space-x-1 px-2 py-1 rounded-md bg-dark-850 text-[10px] font-bold text-dark-400 border border-dark-800">
            <Command size={10} />
            <span>K</span>
          </span>
          <button type="button" onClick={onClose} className="text-dark-400 hover:text-white p-1 rounded-lg">
            <X size={16} />
          </button>
        </div>

        {/* Command Options List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-dark-850/40">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-xs text-dark-400">
              No matching commands or pages found.
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const IconComp = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  onClick={() => handleSelect(cmd)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`p-3 rounded-2xl flex items-center justify-between cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-indigo-600/20 border border-indigo-500/30 text-white'
                      : 'text-dark-300 hover:bg-dark-850/50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={`p-2 rounded-xl ${isSelected ? 'bg-indigo-600 text-white' : 'bg-dark-950 text-indigo-400 border border-dark-800'}`}>
                      <IconComp size={16} />
                    </span>
                    <div>
                      <p className="text-xs font-bold text-white">{cmd.name}</p>
                      <p className="text-[10px] text-dark-400">{cmd.category}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 text-dark-500 text-xs">
                    {isSelected && <span className="text-[10px] text-indigo-400 font-semibold">Press Enter</span>}
                    <ArrowRight size={14} className={isSelected ? 'text-indigo-400' : 'text-dark-600'} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Navigation Hint */}
        <div className="p-3 bg-dark-950/90 border-t border-dark-800 text-[11px] text-dark-400 flex items-center justify-between px-4">
          <div className="flex items-center space-x-3">
            <span><b>↑↓</b> to navigate</span>
            <span>•</span>
            <span><b>↵</b> to select</span>
            <span>•</span>
            <span><b>esc</b> to exit</span>
          </div>
          <span className="text-indigo-400 font-semibold">ExpenseFlowAI Command OS</span>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
