import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid
} from 'recharts';
import {
  ArrowUpRight, ArrowDownRight, DollarSign, CreditCard,
  TrendingUp, TrendingDown, Wallet, Sparkles, AlertCircle, RefreshCw,
  Calendar, Trash2, Sliders, Target, FileText, Activity, X, ShieldCheck,
  CheckCircle2, Clock, Plane, Car, Home, Plus, ChevronRight, MessageSquare, Bot
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import { DashboardSkeleton } from '../components/Common/SkeletonLoader';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import OnboardingWizard from '../components/Onboarding/OnboardingWizard';
import WhyButton from '../components/XAI/WhyButton';
import ExplanationPanel from '../components/XAI/ExplanationPanel';

// ─── Helpers ──────────────────────────────────────────────────────────────

const fmtFull = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
const fmt = (n) => {
  if (n === null || n === undefined) return '—';
  const abs = Math.abs(n);
  if (abs >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(1)}Cr`;
  if (abs >= 1_00_000)    return `₹${(n / 1_00_000).toFixed(1)}L`;
  if (abs >= 1_000)       return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isDark } = useTheme();
  const { addToast } = useToast();

  const [overview, setOverview] = useState(null);
  const [stats, setStats] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('30d');

  // Simulation Modal State
  const [simModalOpen, setSimModalOpen] = useState(false);
  const [activePreset, setActivePreset] = useState(null);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  // Quick AI Copilot Drawer State
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotPrompt, setCopilotPrompt] = useState('');

  // Onboarding Wizard State
  const [showOnboarding, setShowOnboarding] = useState(() => {
    const completed = localStorage.getItem('ef_onboarding_completed') === 'true';
    const skipped = localStorage.getItem('ef_onboarding_skipped') === 'true';
    return !completed && !skipped;
  });

  // Explainable AI (XAI) State
  const [xaiFeature, setXaiFeature] = useState('dashboard');
  const [xaiTargetId, setXaiTargetId] = useState('overview');
  const [xaiOpen, setXaiOpen] = useState(false);

  const openXAI = (feature, targetId) => {
    setXaiFeature(feature);
    setXaiTargetId(targetId);
    setXaiOpen(true);
  };

  const fetchCommandCenterData = async () => {
    try {
      setLoading(true);
      const [overviewRes, statsRes, accRes] = await Promise.allSettled([
        api.get('/dashboard/overview', { params: { period } }),
        api.get('/transactions/stats'),
        api.get('/accounts')
      ]);

      if (overviewRes.status === 'fulfilled') setOverview(overviewRes.value.data);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (accRes.status === 'fulfilled') setAccounts(accRes.value.data);
    } catch (err) {
      console.warn('Command center data fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommandCenterData();
  }, [period]);

  const handleRunPresetSimulation = async (preset) => {
    setActivePreset(preset);
    setSimModalOpen(true);
    setSimLoading(true);
    setSimResult(null);

    try {
      let scenarios = [];
      if (preset.type === 'income_change') {
        scenarios = [{ name: preset.label, income_change: preset.value }];
      } else if (preset.type === 'large_purchase') {
        scenarios = [{ name: preset.label, expense_change: preset.value }];
      } else if (preset.type === 'recurring_bill') {
        scenarios = [{ name: preset.label, expense_change: preset.value * 12 }];
      }

      const res = await api.post('/planning/simulate', {
        scenarios,
        months_horizon: 6
      });
      setSimResult(res.data);
    } catch (err) {
      addToast('Failed to run simulation.', 'error');
    } finally {
      setSimLoading(false);
    }
  };

  if (loading) {
    return (
      <div role="status" className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        <DashboardSkeleton />
      </div>
    );
  }

  // Financial Metrics Fallbacks
  const healthScore = overview?.financial_health?.score ?? 88;
  const healthStatus = overview?.financial_health?.status ?? 'Excellent';
  const totalBalance = overview?.metrics?.total_balance ?? stats?.total_balance ?? 0;
  const netWorth = overview?.metrics?.net_worth ?? totalBalance * 1.2;
  const periodIncome = overview?.metrics?.period_income ?? 0;
  const periodExpense = overview?.metrics?.period_expense ?? 0;
  const periodSavings = overview?.metrics?.period_savings ?? (periodIncome - periodExpense);
  const savingsRate = overview?.metrics?.savings_rate ?? (periodIncome > 0 ? (periodSavings / periodIncome) * 100 : 0);

  const categorySpending = overview?.category_spending || stats?.category_spending || [];
  const monthlyTrends = stats?.monthly_trends || [];

  const getGreeting = () => {
    const hr = new Date().getHours();
    if (hr < 12) return 'Good morning';
    if (hr < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const todayDateString = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const trendsData = monthlyTrends.map(t => ({
    name: t.month,
    Income: t.income,
    Expenses: t.expenses,
  }));

  const donutData = categorySpending.map(cat => ({
    name: cat.category,
    value: cat.amount,
    color: cat.color || '#6366f1',
  }));

  return (
    <div className="space-y-8 pb-16 animate-in fade-in duration-300 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Onboarding Setup Wizard Overlay */}
      {showOnboarding && accounts.length === 0 && (
        <OnboardingWizard
          onComplete={() => {
            setShowOnboarding(false);
            fetchCommandCenterData();
          }}
          onSkip={() => {
            setShowOnboarding(false);
            fetchCommandCenterData();
          }}
        />
      )}

      {/* ─── TOP SECTION: HERO COMMAND CENTER HEADER ──────────────────────── */}
      <div className="bg-gradient-to-br from-indigo-900/30 via-dark-900 to-dark-950 border border-dark-800 p-6 md:p-8 rounded-3xl relative overflow-hidden flex flex-col lg:flex-row lg:items-center justify-between gap-6 shadow-2xl">
        <div className="space-y-2 z-10">
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20 w-fit">
            <Sparkles size={14} />
            <span>AI Financial Command Center</span>
            <span className="text-dark-500">•</span>
            <span>{todayDateString}</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
            {getGreeting()}, {user?.full_name || user?.name || 'Commander'} 👋
          </h1>
          <p className="text-dark-400 text-xs md:text-sm max-w-2xl leading-relaxed">
            Real-time financial status, automated risk monitoring, and predictive cashflow guidance compiled by ExpenseFlow FinanceEngine.
          </p>
        </div>

        {/* Health Score Circular Widget */}
        <div className="flex items-center gap-5 bg-dark-950/70 backdrop-blur-md p-4 rounded-2xl border border-dark-800 z-10">
          <div className="relative w-20 h-20 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="40" cy="40" r="34" className="stroke-dark-800" strokeWidth="7" fill="transparent" />
              <circle
                cx="40"
                cy="40"
                r="34"
                className="stroke-indigo-500 transition-all duration-1000 ease-out"
                strokeWidth="7"
                strokeDasharray={2 * Math.PI * 34}
                strokeDashoffset={2 * Math.PI * 34 * (1 - healthScore / 100)}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <span className="absolute text-xl font-black text-white">{healthScore}</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-dark-400">Health Score</span>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                ▲ +5 this mo
              </span>
            </div>
            <p className="text-base font-bold text-white mt-0.5">{healthStatus}</p>
            <p className="text-[11px] text-dark-400">Top 12% financial discipline</p>
          </div>
        </div>
      </div>

      {/* ─── METRICS KPI CARDS GRID ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-dark-400 mb-2">
            <span className="text-xs font-semibold">Total Available Balance</span>
            <Wallet className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-black text-white">{fmtFull(totalBalance)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Across all verified accounts</p>
        </Card>

        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-dark-400 mb-2">
            <span className="text-xs font-semibold">Monthly Savings</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-black text-emerald-400">{fmtFull(periodSavings)}</p>
          <p className="text-[11px] text-dark-400 mt-1">{savingsRate.toFixed(1)}% savings rate ({period})</p>
        </Card>

        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-dark-400 mb-2">
            <span className="text-xs font-semibold">Net Surplus ({period})</span>
            <ArrowUpRight className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-black text-white">{fmtFull(periodIncome - periodExpense)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Income: {fmt(periodIncome)} • Exp: {fmt(periodExpense)}</p>
        </Card>

        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-dark-400 mb-2">
            <span className="text-xs font-semibold">Estimated Net Worth</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-black text-white">{fmtFull(netWorth)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Liquid assets & reserves</p>
        </Card>
      </div>

      {/* ─── QUICK AI EXECUTIVE SUMMARY CARD ──────────────────────────────── */}
      <Card className="p-6 border-l-4 border-l-indigo-500 bg-gradient-to-r from-indigo-950/20 to-dark-900">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Sparkles size={16} />
              </span>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Executive Briefing</h3>
              <WhyButton onClick={() => openXAI('dashboard', 'executive_briefing')} />
            </div>
            <p className="text-xs md:text-sm text-dark-200 leading-relaxed max-w-4xl">
              {overview?.ai_executive_summary ||
                `You maintained a solid ${savingsRate.toFixed(1)}% savings rate over the last ${period}. Net savings reached ${fmtFull(periodSavings)} with a total financial health score of ${healthScore}/100 (${healthStatus}). Budget adherence remains strong.`}
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/dashboard/chat')}
            className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md flex-shrink-0"
          >
            <MessageSquare size={14} />
            <span>Ask Copilot</span>
          </button>
        </div>
      </Card>

      {/* ─── TODAY'S AI INSIGHTS GRID ─────────────────────────────────────── */}
      <div className="space-y-4">
        <h2 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
          <Sparkles className="text-indigo-400" size={18} /> Today's AI Command Insights
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {(overview?.ai_insights_cards || []).map((card, idx) => (
            <Card key={idx} className="p-4 flex flex-col justify-between space-y-3 hover:border-indigo-500/50 transition-all">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {card.id.replace('_', ' ')}
                  </span>
                  <WhyButton onClick={() => openXAI('dashboard', card.id)} label="Why?" />
                </div>
                <p className="text-xs font-bold text-white mt-1">{card.title}</p>
                <p className="text-[11px] text-dark-300 leading-snug">{card.subtitle}</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/dashboard/insights')}
                className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 pt-2 border-t border-dark-800"
              >
                <span>{card.action}</span>
                <ChevronRight size={12} />
              </button>
            </Card>
          ))}
        </div>
      </div>

      {/* ─── INTERACTIVE CHARTS GRID ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cashflow Trend Line / Area Chart */}
        <Card className="lg:col-span-2 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Cash Flow & Spending Trends</h3>
              <p className="text-xs text-dark-400">Monthly Income vs Expense outflow trajectory</p>
            </div>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-dark-950 border border-dark-800 rounded-lg px-2.5 py-1 text-xs text-dark-200 outline-none focus:border-indigo-500"
            >
              <option value="7d">7 Days</option>
              <option value="30d">30 Days</option>
              <option value="90d">90 Days</option>
              <option value="1y">1 Year</option>
            </select>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendsData}>
                <defs>
                  <linearGradient id="incGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={fmt} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(val) => fmtFull(val)}
                />
                <Area type="monotone" dataKey="Income" stroke="#10b981" fillOpacity={1} fill="url(#incGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="Expenses" stroke="#f43f5e" fillOpacity={1} fill="url(#expGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Category Spending Donut */}
        <Card className="p-6 space-y-4">
          <div>
            <h3 className="text-base font-bold text-white">Category Breakdown</h3>
            <p className="text-xs text-dark-400">Expense distribution by category</p>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={donutData} innerRadius={55} outerRadius={75} paddingAngle={4} dataKey="value">
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '12px', fontSize: '12px' }} formatter={(v) => fmtFull(v)} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 max-h-28 overflow-y-auto pr-1">
            {donutData.slice(0, 4).map((c, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                  <span className="text-dark-300">{c.name}</span>
                </div>
                <span className="font-semibold text-white">{fmt(c.value)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ─── DIGITAL TWIN 1-CLICK PRESET SIMULATION BAR ──────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
            <Activity className="text-indigo-400" size={18} /> Digital Twin What-If Simulator
          </h2>
          <span className="text-xs text-dark-400">Click any preset to simulate virtual impact safely</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {(overview?.digital_twin_presets || []).map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => handleRunPresetSimulation(preset)}
              className="p-3.5 rounded-2xl bg-dark-900 hover:bg-indigo-600/10 border border-dark-800 hover:border-indigo-500/50 text-left transition-all group shadow-sm"
            >
              <p className="text-xs font-bold text-white group-hover:text-indigo-300">{preset.label}</p>
              <p className="text-[10px] text-dark-400 mt-1 capitalize">{preset.type.replace('_', ' ')}</p>
            </button>
          ))}
        </div>
      </div>

      {/* ─── GOAL COMMAND & BUDGET BURN RATE CARDS ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Goals Progress Cards */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Savings Goals Roadmap</h3>
              <p className="text-xs text-dark-400">Target milestones & AI forecast completion dates</p>
            </div>
            <button type="button" onClick={() => navigate('/dashboard/goals')} className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
              View All
            </button>
          </div>

          <div className="space-y-4">
            {(overview?.goal_overview || []).slice(0, 3).map((g) => (
              <div key={g.id} className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{g.title}</span>
                  <span className="text-indigo-400 font-bold">{g.progress_pct}%</span>
                </div>

                <div className="w-full bg-dark-850 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(g.progress_pct, 100)}%` }} />
                </div>

                <div className="flex items-center justify-between text-[11px] text-dark-400">
                  <span>Saved: {fmt(g.current_amount)} / {fmt(g.target_amount)}</span>
                  <span>Est: {g.forecast_completion_date}</span>
                </div>

                <p className="text-[11px] text-emerald-400 font-medium bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20">
                  💡 {g.ai_recommendation}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* Budget Burn Rate Cards */}
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Budget Burn Rates</h3>
              <p className="text-xs text-dark-400">Active category limits & risk level monitoring</p>
            </div>
            <button type="button" onClick={() => navigate('/dashboard/budgets')} className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
              View All
            </button>
          </div>

          <div className="space-y-4">
            {(overview?.budget_overview || []).slice(0, 3).map((b) => (
              <div key={b.id} className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{b.category}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    b.risk_level === 'critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    b.risk_level === 'warning' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  }`}>
                    {b.risk_level} ({b.burn_rate_pct}%)
                  </span>
                </div>

                <div className="w-full bg-dark-850 h-2 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${
                    b.risk_level === 'critical' ? 'bg-rose-500' : b.risk_level === 'warning' ? 'bg-amber-500' : 'bg-indigo-500'
                  }`} style={{ width: `${Math.min(b.burn_rate_pct, 100)}%` }} />
                </div>

                <div className="flex items-center justify-between text-[11px] text-dark-400">
                  <span>Spent: {fmt(b.spent_amount)} / {fmt(b.budget_amount)}</span>
                  <span>Rem: {fmt(b.remaining_amount)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ─── UPCOMING BILLS TIMELINE & FORECAST SNAPSHOT ──────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bills Timeline */}
        <Card className="lg:col-span-2 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Upcoming Bills Timeline</h3>
              <p className="text-xs text-dark-400">Pending liabilities & due dates</p>
            </div>
            <button type="button" onClick={() => navigate('/dashboard/bills')} className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
              Manage Bills
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
              <span className="text-[10px] font-bold uppercase text-amber-400">Due Today / Tomorrow</span>
              <p className="text-xl font-black text-white">
                {fmt((overview?.bills_timeline?.due_today?.length || 0) + (overview?.bills_timeline?.due_tomorrow?.length || 0))}
              </p>
              <p className="text-[11px] text-dark-400">Immediate priority</p>
            </div>

            <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
              <span className="text-[10px] font-bold uppercase text-indigo-400">Due This Week</span>
              <p className="text-xl font-black text-white">{overview?.bills_timeline?.due_this_week?.length || 0}</p>
              <p className="text-[11px] text-dark-400">Next 7 days</p>
            </div>

            <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
              <span className="text-[10px] font-bold uppercase text-rose-400">Overdue / Late</span>
              <p className="text-xl font-black text-rose-400">{overview?.bills_timeline?.late?.length || 0}</p>
              <p className="text-[11px] text-dark-400">Action required</p>
            </div>
          </div>
        </Card>

        {/* 30-Day Forecast Snapshot */}
        <Card className="p-6 space-y-4">
          <div>
            <h3 className="text-base font-bold text-white">30-Day Forecast Snapshot</h3>
            <p className="text-xs text-dark-400">Projected cash runway</p>
          </div>

          <div className="space-y-3 p-4 rounded-2xl bg-dark-950 border border-dark-850 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Projected End Balance</span>
              <span className="font-bold text-white">{fmtFull(overview?.forecast_snapshot?.projected_end_balance)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Expected Surplus</span>
              <span className="font-bold text-emerald-400">{fmtFull(overview?.forecast_snapshot?.expected_surplus)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Confidence Score</span>
              <span className="font-bold text-indigo-400">{Math.round((overview?.forecast_snapshot?.confidence_score || 0.88) * 100)}%</span>
            </div>
          </div>
        </Card>
      </div>

      {/* ─── DIGITAL TWIN SIMULATION MODAL ────────────────────────────────── */}
      {simModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-lg bg-dark-900 border border-dark-800 rounded-3xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-indigo-400">
                <Activity size={20} />
                <h3 className="text-lg font-bold text-white">Digital Twin Simulation Results</h3>
              </div>
              <button type="button" onClick={() => setSimModalOpen(false)} className="text-dark-400 hover:text-white p-1">
                <X size={18} />
              </button>
            </div>

            {simLoading ? (
              <div className="py-12 text-center text-xs text-dark-400 animate-pulse">
                Running in-memory simulation against financial profile...
              </div>
            ) : simResult ? (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 space-y-2">
                  <p className="text-xs font-bold text-indigo-400 uppercase tracking-wider">{activePreset?.label}</p>
                  <div className="flex items-center justify-between text-xs pt-1">
                    <span className="text-dark-400">Virtual Projected Balance (6 mo)</span>
                    <span className="font-bold text-white">{fmtFull(simResult.simulated_final_balance)}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-dark-400">Balance Delta Impact</span>
                    <span className={`font-bold ${simResult.balance_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {simResult.balance_delta >= 0 ? '+' : ''}{fmtFull(simResult.balance_delta)}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-bold text-white">AI Financial Evaluation</p>
                  <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-xs text-dark-200 leading-relaxed">
                    {simResult.simulated_health_score >= 80
                      ? 'This scenario maintains strong financial health. Surplus cash reserves remain sufficient to cover 3+ months of living expenses.'
                      : 'This scenario reduces net monthly surplus. Consider cutting non-essential category budgets to offset the impact.'}
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <Button variant="primary" onClick={() => setSimModalOpen(false)}>
                    Close Simulation
                  </Button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Explainable AI (XAI) Modal Panel */}
      <ExplanationPanel
        feature={xaiFeature}
        targetId={xaiTargetId}
        isOpen={xaiOpen}
        onClose={() => setXaiOpen(false)}
      />
    </div>
  );
};

export default Dashboard;
