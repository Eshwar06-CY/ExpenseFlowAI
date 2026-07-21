import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, PieChart, Pie, Cell, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  ArrowUpRight, ArrowDownRight, DollarSign, CreditCard,
  TrendingUp, Wallet, Sparkles, AlertCircle, RefreshCw,
  Calendar, Trash2, Sliders, Target, FileText, Activity, X
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
  
  const [stats, setStats] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [goals, setGoals] = useState([]);
  const [bills, setBills] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [briefing, setBriefing] = useState(null);
  const [periodSummary, setPeriodSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [deleteId, setDeleteId] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Onboarding Wizard State
  const [showOnboarding, setShowOnboarding] = useState(() => {
    const completed = localStorage.getItem('ef_onboarding_completed') === 'true';
    const skipped = localStorage.getItem('ef_onboarding_skipped') === 'true';
    return !completed && !skipped;
  });

  // Customize Dashboard State
  const [showCustomizeModal, setShowCustomizeModal] = useState(false);
  const [dashSettings, setDashSettings] = useState(() => {
    const saved = localStorage.getItem('ef_dashboard_settings');
    return saved ? JSON.parse(saved) : {
      widgets: {
        kpiRow: true,
        healthScore: true,
        budgetsSavings: true,
        upcomingBills: true,
        cashFlowChart: true,
        donutChart: true,
        activityTimeline: true,
        advisor: true,
      },
      dateRange: '30d',
      quickActions: {
        expense: true,
        income: true,
        transfer: true,
        bill: true,
      }
    };
  });

  const fetchStats = async () => {
    try {
      setLoading(true);
      const period = dashSettings.dateRange;
      const [statsRes, budRes, goalRes, billRes, briefRes, acctRes, summaryRes] = await Promise.all([
        api.get('/transactions/stats'),
        api.get('/budgets'),
        api.get('/goals'),
        api.get('/bills'),
        api.get('/insights/briefing/daily'),
        api.get('/accounts'),
        api.get('/reports/analytics/summary', { params: { period } })
      ]);
      setStats(statsRes.data);
      setBudgets(budRes.data);
      setGoals(goalRes.data);
      setBills(billRes.data);
      setBriefing(briefRes.data);
      setAccounts(acctRes.data);
      setPeriodSummary(summaryRes.data);
    } catch (err) {
      console.warn('Dashboard statistics failed to load or empty profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [dashSettings.dateRange]);

  const handleDeleteTransaction = async (txId) => {
    setDeleteId(txId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      await api.delete(`/transactions/${deleteId}`);
      addToast('Transaction deleted successfully', 'success');
      fetchStats();
    } catch (err) {
      addToast('Failed to delete transaction', 'error');
    }
  };

  const handleSaveSettings = (newSettings) => {
    setDashSettings(newSettings);
    localStorage.setItem('ef_dashboard_settings', JSON.stringify(newSettings));
    addToast('Dashboard settings saved!', 'success');
  };

  if (loading) {
    return (
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        <DashboardSkeleton />
      </div>
    );
  }

  // Fallbacks if data empty
  const totalBalance = stats?.total_balance || 0;
  
  // Choose between custom date range metrics or all-time stats metrics
  const activeIncome = periodSummary ? periodSummary.income : (stats?.total_income || 0);
  const activeExpenses = periodSummary ? periodSummary.expense : (stats?.total_expenses || 0);
  const totalIncome = activeIncome;
  const totalExpenses = activeExpenses;
  const savings = activeIncome - activeExpenses;
  const savingsRate = activeIncome > 0 ? (savings / activeIncome) * 100 : 0;

  const categorySpending = stats?.category_spending || [];
  const monthlyTrends = stats?.monthly_trends || [];
  const recentTransactions = stats?.recent_transactions || [];

  // Financial Health Score calculation
  let savingsScore = 0;
  if (savingsRate >= 30) {
    savingsScore = 40;
  } else if (savingsRate > 0) {
    savingsScore = (savingsRate / 30) * 40;
  }

  let budgetScore = 30;
  if (budgets.length > 0) {
    const adhered = budgets.filter(b => b.spent <= b.amount).length;
    budgetScore = (adhered / budgets.length) * 30;
  }

  let billScore = 30;
  if (bills.length > 0) {
    const paidCount = bills.filter(b => b.is_paid).length;
    billScore = (paidCount / bills.length) * 30;
  }

  const financialHealthScore = Math.round(savingsScore + budgetScore + billScore);

  // SVG Gauge Math
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (financialHealthScore / 100) * circumference;
  
  let scoreColor = "stroke-expenses text-expenses";
  if (financialHealthScore >= 80) {
    scoreColor = "stroke-income text-income";
  } else if (financialHealthScore >= 50) {
    scoreColor = "stroke-investments text-investments";
  }

  // Filter top budgets & goals
  const activeBudgets = budgets.slice(0, 3);
  const activeGoals = goals.slice(0, 3);
  const unpaidBills = bills.filter(b => !b.is_paid).slice(0, 3);

  // Personalized Greeting
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

  // Recharts line data
  const trendsData = monthlyTrends.map(t => ({
    name: t.month,
    Income: t.income,
    Expenses: t.expenses,
  }));

  // Recharts donut data
  const totalExpenseSum = categorySpending.reduce((acc, c) => acc + c.amount, 0);
  const donutData = categorySpending.map(cat => ({
    name: cat.category,
    value: cat.amount,
    color: cat.color || '#9f6ff5',
  }));

  return (
    <div className="space-y-8 pb-12 edl-animate-fade">
      {/* Onboarding Setup Wizard Overlay */}
      {showOnboarding && accounts.length === 0 && (
        <OnboardingWizard
          onComplete={() => {
            setShowOnboarding(false);
            fetchStats();
          }}
          onSkip={() => {
            setShowOnboarding(false);
            fetchStats();
          }}
        />
      )}

      {/* Welcome Banner Section */}
      <div className="bg-gradient-to-br from-brand-900/10 via-dark-900 to-dark-950 border border-dark-850 p-6.5 rounded-3xl relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-edl-card">
        <div className="absolute top-1/2 -translate-y-1/2 right-12 w-64 h-64 bg-brand-500/5 rounded-full blur-3xl select-none pointer-events-none"></div>
        <div className="space-y-1.5 z-10">
          <h2 className="text-2xl font-extrabold text-white tracking-tight font-sans">
            {getGreeting()}, {user?.full_name || user?.name || 'Workspace Manager'}! 👋
          </h2>
          <p className="text-xs text-dark-400 font-bold">
            Today is <span className="text-brand-400">{todayDateString}</span>. Here is your workspace summary.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0 z-10">
          <Button variant="secondary" onClick={() => setShowCustomizeModal(true)} className="flex items-center gap-1.5 text-xs py-2.5">
            <Sliders className="w-3.5 h-3.5" /> Customize Layout
          </Button>
          <Button variant="secondary" onClick={() => navigate('/dashboard/transfers')} className="flex items-center gap-1.5 text-xs py-2.5">
            <RefreshCw className="w-3.5 h-3.5" /> Transfers
          </Button>
          <Button variant="primary" onClick={() => navigate('/dashboard/expenses')} className="flex items-center gap-1.5 text-xs py-2.5">
            Add Expense <ArrowUpRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Account Summary Cards Panel */}
      <div className="space-y-3.5">
        <h4 className="text-xs font-bold uppercase tracking-widest text-dark-450 flex items-center gap-1.5">
          <Wallet className="w-3.5 h-3.5 text-brand-400" /> Where my money is (Accounts)
        </h4>
        {accounts.length === 0 ? (
          <p className="text-xs text-dark-500 italic">No bank accounts configured.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {accounts.map(acct => (
              <div 
                key={acct.id} 
                onClick={() => navigate('/dashboard/accounts')}
                className="bg-dark-900 border border-dark-850 p-4.5 rounded-2xl hover:border-brand-500/30 transition-all cursor-pointer flex flex-col justify-between h-28 group relative overflow-hidden shadow-sm"
              >
                <div className="absolute right-2 top-2 w-12 h-12 bg-brand-500/5 rounded-full blur-xl group-hover:bg-brand-500/10 transition-colors"></div>
                <div className="flex items-center justify-between text-xs text-dark-400 relative z-10">
                  <span className="font-bold truncate max-w-[125px]">{acct.name}</span>
                  <span className="text-[9px] bg-dark-950 px-2 py-0.5 rounded font-mono uppercase tracking-wider text-dark-500 font-extrabold border border-dark-850">
                    {acct.type}
                  </span>
                </div>
                <div className="space-y-0.5 mt-3 relative z-10">
                  <span className="text-[9px] text-dark-500 block uppercase font-bold tracking-widest">Available Balance</span>
                  <span className="text-base font-black text-dark-50 font-mono">
                    ${acct.balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {dashSettings.quickActions.expense && (
          <button
            onClick={() => navigate('/dashboard/expenses')}
            className="flex items-center gap-3.5 p-4 rounded-2xl bg-dark-900 border border-dark-850 hover:border-brand-500/30 hover:bg-dark-850/50 transition-all text-left group hover:-translate-y-0.5 shadow-sm"
          >
            <div className="p-2.5 bg-expenses/10 border border-expenses/20 text-expenses rounded-xl group-hover:scale-105 transition-transform">
              <ArrowUpRight size={16} />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-100 leading-tight">Record spending</p>
              <p className="text-[10px] text-dark-500 font-medium mt-1">Track money going out</p>
            </div>
          </button>
        )}
        {dashSettings.quickActions.income && (
          <button
            onClick={() => navigate('/dashboard/income')}
            className="flex items-center gap-3.5 p-4 rounded-2xl bg-dark-900 border border-dark-850 hover:border-brand-500/30 hover:bg-dark-850/50 transition-all text-left group hover:-translate-y-0.5 shadow-sm"
          >
            <div className="p-2.5 bg-income/10 border border-income/20 text-income rounded-xl group-hover:scale-105 transition-transform">
              <ArrowDownRight size={16} />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-100 leading-tight">Record income</p>
              <p className="text-[10px] text-dark-500 font-medium mt-1">Track money coming in</p>
            </div>
          </button>
        )}
        {dashSettings.quickActions.transfer && (
          <button
            onClick={() => navigate('/dashboard/transfers')}
            className="flex items-center gap-3.5 p-4 rounded-2xl bg-dark-900 border border-dark-850 hover:border-brand-500/30 hover:bg-dark-850/50 transition-all text-left group hover:-translate-y-0.5 shadow-sm"
          >
            <div className="p-2.5 bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-xl group-hover:scale-105 transition-transform">
              <RefreshCw size={16} />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-100 leading-tight">Move money</p>
              <p className="text-[10px] text-dark-500 font-medium mt-1">Between pockets</p>
            </div>
          </button>
        )}
        {dashSettings.quickActions.bill && (
          <button
            onClick={() => navigate('/dashboard/bills')}
            className="flex items-center gap-3.5 p-4 rounded-2xl bg-dark-900 border border-dark-850 hover:border-brand-500/30 hover:bg-dark-850/50 transition-all text-left group hover:-translate-y-0.5 shadow-sm"
          >
            <div className="p-2.5 bg-investments/10 border border-investments/20 text-investments rounded-xl group-hover:scale-105 transition-transform">
              <Calendar size={16} />
            </div>
            <div>
              <p className="text-xs font-bold text-dark-100 leading-tight">Pay Bill</p>
              <p className="text-[10px] text-dark-500 font-medium mt-1">Due payments</p>
            </div>
          </button>
        )}
      </div>

      {error && (
        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-850 flex items-start gap-3.5">
          <AlertCircle className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-dark-100">No transactions recorded yet</h4>
            <p className="text-xs text-dark-400 mt-1 leading-relaxed">
              We cannot render the charts or stats widgets because you have no active transactions. Log an expense or income to populate this dashboard!
            </p>
          </div>
        </div>
      )}

      {/* Daily Briefing Banner Widget */}
      {briefing && dashSettings.widgets.advisor && (
        <Card 
          isGlass={true} 
          accent="goals"
          className="hover:shadow-edl-card bg-gradient-to-br from-brand-500/[0.04] to-transparent"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-1.5 text-brand-400 font-extrabold text-[10px] uppercase tracking-widest">
                <Sparkles size={11} className="animate-pulse" /> Today's Workspace Financial Health
              </div>
              <h3 className="text-base font-extrabold text-white leading-snug tracking-tight">
                Your Health Score is <span className="text-brand-400">{briefing.content.health_score}/100</span>.
                You have {briefing.content.warnings_count} active alerts.
              </h3>
              <p className="text-xs text-dark-300 leading-relaxed font-medium">
                Projected 30-day balance is <strong>${briefing.content.projected_balance_30d.toLocaleString()}</strong>.
                Running cash reserve is sustainable for approximately <strong>{briefing.content.burn_rate_months} months</strong>.
              </p>
            </div>
            
            <div className="shrink-0 flex items-center gap-3">
              <Button onClick={() => navigate('/dashboard/insights')} size="sm" variant="secondary" className="flex items-center gap-1.5 py-2">
                Full Intelligence Panel <ArrowUpRight size={12} />
              </Button>
            </div>
          </div>
          
          {briefing.content.warnings.length > 0 && (
            <div className="mt-4 pt-4 border-t border-dark-850/50 grid grid-cols-1 md:grid-cols-2 gap-4">
              {briefing.content.warnings.slice(0, 2).map((w, idx) => (
                <div key={idx} className="flex gap-2.5 items-start text-xs text-dark-400">
                  <AlertCircle size={14} className="text-debt shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-white">{w.title}:</span> {w.description}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Grid statistics */}
      {dashSettings.widgets.kpiRow && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Balance */}
          <Card isGlass={true} className="hover:shadow-edl-card">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-dark-450 uppercase tracking-widest">Total money I have</p>
                <h3 className="text-xl font-extrabold text-dark-50 font-sans font-mono tracking-tight pt-1">
                  $ {totalBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </h3>
              </div>
              <div className="p-2.5 bg-dark-800 border border-dark-750 rounded-xl text-savings">
                <Wallet className="w-4 h-4" />
              </div>
            </div>
          </Card>

          {/* Total Expenses */}
          <Card isGlass={true} className="hover:shadow-edl-card" accent="expenses">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-dark-450 uppercase tracking-widest">Money spent ({dashSettings.dateRange.toUpperCase()})</p>
                <h3 className="text-xl font-extrabold text-expenses font-sans font-mono tracking-tight pt-1">
                  $ {activeExpenses.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </h3>
              </div>
              <div className="p-2.5 bg-dark-800 border border-dark-750 rounded-xl text-expenses">
                <CreditCard className="w-4 h-4" />
              </div>
            </div>
          </Card>

          {/* Total Income */}
          <Card isGlass={true} className="hover:shadow-edl-card" accent="income">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-dark-450 uppercase tracking-widest">Money earned ({dashSettings.dateRange.toUpperCase()})</p>
                <h3 className="text-xl font-extrabold text-income font-sans font-mono tracking-tight pt-1">
                  $ {activeIncome.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </h3>
              </div>
              <div className="p-2.5 bg-dark-800 border border-dark-750 rounded-xl text-income">
                <DollarSign className="w-4 h-4" />
              </div>
            </div>
          </Card>

          {/* Savings Rate */}
          <Card isGlass={true} className="hover:shadow-edl-card">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-dark-450 uppercase tracking-widest">Savings rate</p>
                <h3 className="text-xl font-extrabold text-brand-400 font-sans font-mono tracking-tight pt-1">
                  {savingsRate.toFixed(1)}%
                </h3>
              </div>
              <div className="p-2.5 bg-dark-800 border border-dark-750 rounded-xl text-brand-400">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Financial Planning Widget Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Score Gauge */}
        {dashSettings.widgets.healthScore && (
          <Card isGlass={true} title="How healthy is my pocket?" subtitle="Pocket health indicators">
            <div className="flex flex-col items-center justify-center py-4">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle 
                    cx="64" cy="64" r={radius} 
                    className="stroke-dark-800" 
                    strokeWidth="8" 
                    fill="transparent" 
                  />
                  <circle 
                    cx="64" cy="64" r={radius} 
                    className={`${scoreColor} transition-all duration-1000 ease-out`}
                    strokeWidth="8" 
                    fill="transparent" 
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-3xl font-black text-white leading-none">{financialHealthScore}</span>
                  <span className="text-[9px] uppercase font-bold text-dark-450 tracking-widest mt-1">Health</span>
                </div>
              </div>
              <p className="text-xs text-dark-400 text-center mt-5 px-1 leading-relaxed font-sans font-medium">
                {financialHealthScore >= 80 ? (
                  "Excellent cash flow! Maintain low expenses and high savings."
                ) : financialHealthScore >= 50 ? (
                  "Healthy balance, though some budgets are close to exceeding."
                ) : (
                  "Take action! Set budgets and settle pending bills to improve."
                )}
              </p>
            </div>
          </Card>
        )}

        {/* Budgets & Savings Progress */}
        {dashSettings.widgets.budgetsSavings && (
          <Card isGlass={true} title="Active Limits & Savings" subtitle="Tracking top targets">
            <div className="space-y-4 py-1">
              {/* Top Budgets */}
              <div>
                <h4 className="text-[9px] uppercase font-bold text-brand-400 tracking-wider flex items-center gap-1 mb-2">
                  <Sliders size={10} /> Active Budgets
                </h4>
                {activeBudgets.length === 0 ? (
                  <p className="text-xs text-dark-500 italic">No budgets configured.</p>
                ) : (
                  <div className="space-y-2">
                    {activeBudgets.map(b => {
                      const ratio = b.amount > 0 ? (b.spent / b.amount) * 100 : 0;
                      return (
                        <div key={b.id} className="text-xs bg-dark-950/40 p-2.5 rounded-xl border border-dark-850">
                          <div className="flex justify-between mb-1.5">
                            <span className="text-dark-200 font-bold">{b.category?.name}</span>
                            <span className="text-dark-400 font-bold font-mono">${b.spent.toLocaleString()} / ${b.amount.toLocaleString()}</span>
                          </div>
                          <div className="w-full bg-dark-800 rounded-full h-1.5 overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${ratio > 100 ? 'bg-expenses' : 'bg-brand-500'}`} 
                              style={{ width: `${Math.min(ratio, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Top Savings Goals */}
              <div>
                <h4 className="text-[9px] uppercase font-bold text-savings tracking-wider flex items-center gap-1 mb-2">
                  <Target size={10} /> Savings Goals
                </h4>
                {activeGoals.length === 0 ? (
                  <p className="text-xs text-dark-500 italic">No savings goals configured.</p>
                ) : (
                  <div className="space-y-2">
                    {activeGoals.map(g => {
                      const ratio = g.target_amount > 0 ? (g.current_amount / g.target_amount) * 100 : 0;
                      return (
                        <div key={g.id} className="text-xs bg-dark-950/40 p-2.5 rounded-xl border border-dark-850">
                          <div className="flex justify-between mb-1.5">
                            <span className="text-dark-200 font-bold">{g.name}</span>
                            <span className="text-dark-400 font-bold font-mono">${g.current_amount.toLocaleString()} / ${g.target_amount.toLocaleString()}</span>
                          </div>
                          <div className="w-full bg-dark-800 rounded-full h-1.5 overflow-hidden">
                            <div 
                              className="h-full rounded-full bg-income" 
                              style={{ width: `${Math.min(ratio, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </Card>
        )}

        {/* Due Bills Notification Panel */}
        {dashSettings.widgets.upcomingBills && (
          <Card isGlass={true} title="Upcoming Bills" subtitle="Avoid overdue notices">
            <div className="space-y-3 py-1">
              {unpaidBills.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-6 text-center text-dark-500">
                  <FileText className="w-8 h-8 text-dark-800 mb-2" />
                  <p className="text-xs font-semibold">No pending bills. Settled!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {unpaidBills.map(b => (
                    <div key={b.id} className="flex justify-between items-center p-2.5 bg-dark-950/40 border border-dark-850 rounded-xl text-xs">
                      <div>
                        <p className="font-bold text-dark-100">{b.name}</p>
                        <p className="text-[9px] text-dark-500 font-bold flex items-center gap-1 mt-1 uppercase tracking-wider">
                          <Calendar size={10} /> Due: {new Date(b.due_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-extrabold text-dark-50 font-mono">${b.amount.toLocaleString()}</p>
                        <button 
                          onClick={() => navigate('/dashboard/bills')}
                          className="text-[9px] text-brand-400 hover:text-brand-350 font-bold mt-1 block"
                        >
                          Settle Dues
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <button 
                onClick={() => navigate('/dashboard/bills')}
                className="w-full py-2.5 bg-dark-900 hover:bg-dark-850 border border-dark-850 rounded-xl text-dark-300 text-xs font-bold mt-2 transition-colors active:scale-95 duration-200"
              >
                Configure Bill Book
              </button>
            </div>
          </Card>
        )}
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Flow Line Chart */}
        {dashSettings.widgets.cashFlowChart && (
          <Card className="lg:col-span-2" title="Cash Flow Dynamics" subtitle="Interactive income vs expense trends">
            {monthlyTrends.length < 2 ? (
              <div className="h-56 flex items-center justify-center text-dark-500 text-xs italic">
                Insufficient monthly history. Build more transactions to plot.
              </div>
            ) : (
              <div className="h-56 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trendsData} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="incomeDashGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#05b074" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#05b074" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="expenseDashGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#fa5f70" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#fa5f70" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Tooltip 
                      contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 10, fontSize: 11 }}
                      itemStyle={{ fontSize: 11, fontWeight: 700 }}
                    />
                    <Area type="monotone" dataKey="Income" stroke="#05b074" strokeWidth={2} fill="url(#incomeDashGrad)" dot={false} />
                    <Area type="monotone" dataKey="Expenses" stroke="#fa5f70" strokeWidth={2} fill="url(#expenseDashGrad)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
                <div className="flex justify-between text-[10px] text-dark-500 px-4 font-mono font-bold uppercase tracking-wider mt-2">
                  {monthlyTrends.map((t, idx) => (
                    <span key={idx}>{t.month}</span>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Expenses Category Donut */}
        {dashSettings.widgets.donutChart && (
          <Card title="Expenses Tag Distribution" subtitle="Categorized outflows breakdown">
            {categorySpending.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-dark-500 text-xs italic">
                No expenses registered for category charts.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-44 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={donutData}
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={65}
                        dataKey="value"
                        paddingAngle={3}
                        stroke="none"
                      >
                        {donutData.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(val) => `$${val.toLocaleString()}`} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 11 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Legends */}
                <div className="max-h-24 overflow-y-auto space-y-1.5 px-1 custom-scrollbar">
                  {categorySpending.map((cat, idx) => {
                    const pct = totalExpenseSum > 0 ? (cat.amount / totalExpenseSum) * 100 : 0;
                    return (
                      <div key={idx} className="flex justify-between items-center text-xs text-dark-400">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cat.color || '#9CA3AF' }}></span>
                          <span className="font-bold truncate max-w-[120px]">{cat.category}</span>
                        </div>
                        <span className="font-extrabold text-dark-200 font-mono">
                          ${cat.amount.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({pct.toFixed(0)}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>
        )}
      </div>

      {/* Recent Activity Timeline & Advisor details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline activity view */}
        {dashSettings.widgets.activityTimeline && (
          <Card className="lg:col-span-2" title="Recent Activity Timeline" subtitle="Visual ledger outflow & inflow history">
            {recentTransactions.length === 0 ? (
              <div className="py-12 text-center text-xs text-dark-500 italic">
                No transactions recorded in the ledger. Log your first cash flow.
              </div>
            ) : (
              <div className="relative border-l border-dark-850 ml-4 pl-6 space-y-6 py-2">
                {recentTransactions.map((tx) => {
                  const isIncome = tx.type === 'income';
                  const isTransfer = tx.type === 'transfer';
                  return (
                    <div key={tx.id} className="relative group">
                      {/* Circle marker */}
                      <span className={`absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full border-2 bg-dark-950 transition-transform group-hover:scale-125 z-10 ${
                        isIncome ? 'border-income' : isTransfer ? 'border-brand-500' : 'border-expenses'
                      }`}></span>

                      <div className="flex items-start justify-between gap-4 text-xs">
                        <div>
                          <p className="font-bold text-dark-100 group-hover:text-brand-400 transition-colors">{tx.description}</p>
                          <div className="flex items-center gap-2 text-[10px] text-dark-500 mt-1 font-bold">
                            <span>{new Date(tx.date).toLocaleDateString()}</span>
                            <span>•</span>
                            <span className="bg-dark-900 border border-dark-850 px-1.5 py-0.5 rounded uppercase tracking-wider text-dark-400">
                              {tx.category?.name || 'Uncategorized'}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <span className={`font-mono font-black text-sm ${
                            isIncome ? 'text-income' : isTransfer ? 'text-brand-400' : 'text-expenses'
                          }`}>
                            {isIncome ? '+' : '-'}${tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                          <button 
                            onClick={() => handleDeleteTransaction(tx.id)}
                            className="p-1 hover:bg-red-500/10 text-red-500/80 hover:text-expenses rounded-md transition-all shrink-0 active:scale-90"
                            title="Delete Ledger Entry"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        )}

        {/* Quick Tips advisor card */}
        {dashSettings.widgets.advisor && (
          <Card title="Workspace Advisor" subtitle="Automated ledger parsing" isGlass={true}>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-brand-600/10 border border-brand-500/20 flex gap-3 shadow-sm">
                <Sparkles className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-brand-300">Advisor Status</h4>
                  <p className="text-[11px] text-dark-300 leading-relaxed font-semibold mt-1">
                    {totalIncome > totalExpenses ? (
                      `Great job! Your current savings margin is ${savingsRate.toFixed(0)}%. Focus on allocating this surplus to savings reserves.`
                    ) : totalIncome === 0 ? (
                      'Record a recurring salary or freelance billing in the Income page to activate automated savings advice.'
                    ) : (
                      'Your cash outflows currently exceed income streams. Scan categories to look for unused subscriptions or utility costs.'
                    )}
                  </p>
                </div>
              </div>

              <div className="border border-dark-850 rounded-xl p-3 bg-dark-950/40">
                <div className="flex items-center justify-between text-xs mb-1 font-bold">
                  <span className="text-dark-300">Monthly budget limit</span>
                  <span className="text-brand-400 font-mono">
                    $ {totalExpenses.toLocaleString(undefined, { maximumFractionDigits: 0 })} / $ 5,000
                  </span>
                </div>
                <div className="w-full bg-dark-800 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-brand-600 to-indigo-500 h-1.5 rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min((totalExpenses / 5000) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>

              <button 
                onClick={() => navigate('/dashboard/analytics')}
                className="w-full py-3 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white text-xs font-extrabold hover:shadow-lg hover:shadow-brand-500/10 active:scale-95 transition-all mt-2"
              >
                Analyze Outflow Details
              </button>
            </div>
          </Card>
        )}
      </div>

      {/* Customize Dashboard Modal */}
      {showCustomizeModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/75 backdrop-blur-md" onClick={() => setShowCustomizeModal(false)} />
          <div className="relative z-10 w-full max-w-lg bg-dark-900 border border-dark-800 rounded-3xl shadow-edl-depth overflow-hidden animate-fade-in">
            <div className="p-6 border-b border-dark-850 bg-dark-950/60 flex justify-between items-center">
              <div>
                <h3 className="text-base font-extrabold text-white">Customize Layout</h3>
                <p className="text-[10px] text-dark-400 font-semibold mt-0.5">Toggle card displays and date parameters</p>
              </div>
              <button onClick={() => setShowCustomizeModal(false)} className="text-dark-400 hover:text-white p-1 hover:bg-dark-800 rounded-lg">
                <X size={16} />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">
              {/* Date range config */}
              <div className="space-y-2">
                <label className="block text-[10px] font-extrabold uppercase text-dark-400 tracking-wider">Default Date Range</label>
                <div className="grid grid-cols-4 gap-2">
                  {['7d', '30d', '90d', 'mtd'].map(d => (
                    <button
                      key={d}
                      onClick={() => handleSaveSettings({ ...dashSettings, dateRange: d })}
                      className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                        dashSettings.dateRange === d 
                          ? 'border-brand-500 bg-brand-500/10 text-brand-400' 
                          : 'border-dark-800 text-dark-400 hover:border-dark-700'
                      }`}
                    >
                      {d === 'mtd' ? 'Month to Date' : d.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Widget visibility checks */}
              <div className="space-y-3">
                <label className="block text-[10px] font-extrabold uppercase text-dark-400 tracking-wider">Show/Hide Modules</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {Object.keys(dashSettings.widgets).map((wKey) => {
                    const titles = {
                      kpiRow: 'Aggregated KPI Ledger',
                      healthScore: 'Financial Health Gauge',
                      budgetsSavings: 'Limits & Goals Tracker',
                      upcomingBills: 'Upcoming Bills Book',
                      cashFlowChart: 'Cash Flow Dynamics Chart',
                      donutChart: 'Expenses Tag Donut Chart',
                      activityTimeline: 'Activity Timeline List',
                      advisor: 'Workspace advisor panel',
                    };
                    return (
                      <label key={wKey} className="flex items-center gap-3 bg-dark-950/40 border border-dark-850 p-3 rounded-xl cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={dashSettings.widgets[wKey]}
                          onChange={(e) => {
                            const newW = { ...dashSettings.widgets, [wKey]: e.target.checked };
                            handleSaveSettings({ ...dashSettings, widgets: newW });
                          }}
                          className="w-4 h-4 rounded text-brand-500 bg-dark-900 border-dark-800 focus:ring-brand-500"
                        />
                        <span className="text-xs font-bold text-dark-200">{titles[wKey]}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Quick Actions Config */}
              <div className="space-y-3">
                <label className="block text-[10px] font-extrabold uppercase text-dark-400 tracking-wider">Visible Quick Actions</label>
                <div className="grid grid-cols-2 gap-3">
                  {Object.keys(dashSettings.quickActions).map((actKey) => {
                    const titles = {
                      expense: 'Add Expense',
                      income: 'Add Income',
                      transfer: 'Transfer Money',
                      bill: 'Pay Due Bill',
                    };
                    return (
                      <label key={actKey} className="flex items-center gap-3 bg-dark-950/40 border border-dark-850 p-3 rounded-xl cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={dashSettings.quickActions[actKey]}
                          onChange={(e) => {
                            const newActs = { ...dashSettings.quickActions, [actKey]: e.target.checked };
                            handleSaveSettings({ ...dashSettings, quickActions: newActs });
                          }}
                          className="w-4 h-4 rounded text-brand-500 bg-dark-900 border-dark-800 focus:ring-brand-500"
                        />
                        <span className="text-xs font-bold text-dark-200">{titles[actKey]}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="p-4 bg-dark-950/60 border-t border-dark-850 flex justify-end">
              <Button onClick={() => setShowCustomizeModal(false)} variant="primary" className="px-5">
                Close & Reload
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Transaction Deletion */}
      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Transaction"
        message="Are you sure you want to permanently delete this transaction? This action will restore corresponding budget limit margins."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default Dashboard;
