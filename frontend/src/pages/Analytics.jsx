import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, Tooltip, XAxis, YAxis,
  CartesianGrid, Legend, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, TrendingDown, DollarSign, ArrowUpRight,
  ArrowDownRight, Minus, RefreshCw, Download, BarChart3,
  PieChart as PieIcon, Activity, Target, ShoppingBag, Wallet
} from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';

// ─── Palette ──────────────────────────────────────────────────────────────

const CHART_COLORS = {
  income:  '#05b074',
  expense: '#fa5f70',
  net:     '#00d2fc',
  purple:  '#8b5cf6',
};

const DONUT_PALETTE = [
  '#8b5cf6', '#00d2fc', '#ec4899', '#05b074', '#ffb000',
  '#f97316', '#14b8a6', '#fa5f70', '#84cc16', '#06b6d4',
];

// ─── Helpers ──────────────────────────────────────────────────────────────

const fmt = (n) => {
  if (n === null || n === undefined) return '—';
  const abs = Math.abs(n);
  if (abs >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(1)}Cr`;
  if (abs >= 1_00_000)    return `₹${(n / 1_00_000).toFixed(1)}L`;
  if (abs >= 1_000)       return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

const fmtFull = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

const PctBadge = ({ value }) => {
  if (value === null || value === undefined) return <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>vs prev</span>;
  const up = value >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 11, fontWeight: 700, color: up ? '#05b074' : '#fa5f70' }}>
      <Icon size={11} />{Math.abs(value)}%
    </span>
  );
};

// ─── KPI Card ─────────────────────────────────────────────────────────────

function KpiCard({ label, value, pctChange, icon: Icon, color, sub }) {
  return (
    <div style={{
      background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 16,
      padding: '18px 20px',
      borderTop: `3px solid ${color}`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
        <div style={{ width: 34, height: 34, borderRadius: 9, background: `color-mix(in srgb, ${color} 15%, transparent)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={16} color={color} />
        </div>
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.02em' }}>{value}</div>
      <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
        <PctBadge value={pctChange} />
        {sub && <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{sub}</span>}
      </div>
    </div>
  );
}

// ─── Chart Card ──────────────────────────────────────────────────────────

function ChartCard({ title, subtitle, children, action }) {
  return (
    <div style={{
      background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 16, overflow: 'hidden'
    }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text)' }}>{title}</div>
          {subtitle && <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2 }}>{subtitle}</div>}
        </div>
        {action}
      </div>
      <div style={{ padding: '16px 20px' }}>{children}</div>
    </div>
  );
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--card-bg)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '10px 14px', boxShadow: '0 8px 24px rgba(0,0,0,0.3)'
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: p.color }} />
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{p.name}:</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)' }}>{fmt(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

// ─── Period Picker ────────────────────────────────────────────────────────

const PERIODS = [
  { value: '7d',  label: '7D' },
  { value: '30d', label: '30D' },
  { value: '90d', label: '90D' },
  { value: 'mtd', label: 'MTD' },
  { value: '1y',  label: '1Y' },
  { value: 'ytd', label: 'YTD' },
];

function PeriodPicker({ value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 3, background: 'var(--input-bg)', borderRadius: 8, padding: 3, border: '1px solid var(--border)' }}>
      {PERIODS.map(p => (
        <button key={p.value} onClick={() => onChange(p.value)} style={{
          padding: '4px 10px', borderRadius: 6, border: 'none', cursor: 'pointer',
          fontSize: 12, fontWeight: 600,
          background: value === p.value ? 'var(--primary)' : 'transparent',
          color: value === p.value ? '#fff' : 'var(--text-muted)',
          transition: 'all 0.15s'
        }}>
          {p.label}
        </button>
      ))}
    </div>
  );
}

// ─── Budget Adherence Bar ────────────────────────────────────────────────

function BudgetBar({ item }) {
  const pct = Math.min(item.pct_used, 100);
  const color = item.over_budget ? '#ef4444' : item.pct_used > 80 ? '#f59e0b' : '#10b981';
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{item.category}</span>
        <span style={{ fontSize: 12, color: item.over_budget ? '#ef4444' : 'var(--text-muted)' }}>
          {fmtFull(item.spent)} / {fmtFull(item.budget)}
          {item.over_budget && <span style={{ marginLeft: 6, color: '#ef4444', fontSize: 11, fontWeight: 700 }}>OVER</span>}
        </span>
      </div>
      <div style={{ height: 8, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 4, transition: 'width 0.4s ease' }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
        {item.pct_used}% used {item.over_budget ? '' : `• ${fmtFull(item.remaining)} remaining`}
      </div>
    </div>
  );
}

// ─── Main Analytics Page ──────────────────────────────────────────────────

export default function Analytics() {
  const { addToast } = useToast();
  const [period, setPeriod] = useState('30d');
  const [groupBy, setGroupBy] = useState('day');
  const [catType, setCatType] = useState('expense');
  const [loading, setLoading] = useState(true);

  const [summary, setSummary] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [categories, setCategories] = useState(null);
  const [merchants, setMerchants] = useState(null);
  const [netWorth, setNetWorth] = useState(null);
  const [budgets, setBudgets] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, cfRes, catRes, merRes, nwRes, budRes] = await Promise.all([
        api.get('/reports/analytics/summary', { params: { period } }),
        api.get('/reports/analytics/cash-flow', { params: { period, group_by: groupBy } }),
        api.get('/reports/analytics/categories', { params: { period, tx_type: catType } }),
        api.get('/reports/analytics/merchants', { params: { period, limit: 8 } }),
        api.get('/reports/analytics/net-worth', { params: { months: 12 } }),
        api.get('/reports/analytics/budget-adherence'),
      ]);
      setSummary(sumRes.data);
      setCashFlow(cfRes.data);
      setCategories(catRes.data);
      setMerchants(merRes.data);
      setNetWorth(nwRes.data);
      setBudgets(budRes.data);
    } catch {
      addToast('Failed to load analytics data.', 'error');
    } finally {
      setLoading(false);
    }
  }, [period, groupBy, catType]);

  useEffect(() => { load(); }, [load]);

  // Build chart-friendly arrays from API data
  const cashFlowData = cashFlow?.labels
    ? cashFlow.labels.map((label, i) => ({
        label,
        Income: cashFlow.income?.[i] || 0,
        Expense: cashFlow.expense?.[i] || 0,
        Net: cashFlow.net?.[i] || 0,
      }))
    : [];

  const catData = categories?.labels
    ? categories.labels.map((l, i) => ({
        name: l,
        value: categories.values?.[i] || 0,
        color: categories.colors?.[i] || DONUT_PALETTE[i % DONUT_PALETTE.length],
        pct: categories.percentages?.[i] || 0,
      }))
    : [];

  const merchantData = merchants?.merchants || [];

  const netWorthData = netWorth?.labels
    ? netWorth.labels.map((l, i) => ({ label: l, 'Net Worth': netWorth.values?.[i] || 0 }))
    : [];

  const Skeleton = () => (
    <div style={{ height: 260, background: 'rgba(255,255,255,0.03)', borderRadius: 10, animation: 'pulse 1.5s ease-in-out infinite' }} />
  );

  return (
    <div style={{ padding: '24px 28px', maxWidth: 1300, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <BarChart3 size={26} color="var(--primary)" /> Analytics
          </h1>
          <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Deep-dive into your financial patterns and trends.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <PeriodPicker value={period} onChange={p => { setPeriod(p); }} />
          <button onClick={load} style={{
            background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8,
            padding: '6px 10px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center'
          }}>
            <RefreshCw size={15} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </div>
      </div>

      {/* KPI Summary Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 24 }}>
        {summary ? (
          <>
            <KpiCard label="Total Income" value={fmt(summary.income)} pctChange={summary.income_change_pct} icon={TrendingUp} color="#10b981" sub="vs prev period" />
            <KpiCard label="Total Expenses" value={fmt(summary.expense)} pctChange={summary.expense_change_pct} icon={TrendingDown} color="#ef4444" sub="vs prev period" />
            <KpiCard label="Net Savings" value={fmt(summary.net)} pctChange={summary.net_change_pct} icon={DollarSign} color="#6366f1" sub="income - expenses" />
            <KpiCard label="Savings Rate" value={`${summary.savings_rate}%`} pctChange={null} icon={Activity} color="#8b5cf6" sub="of total income" />
            <KpiCard label="Avg Daily Spend" value={fmt(summary.avg_daily_expense)} pctChange={null} icon={ShoppingBag} color="#f59e0b" sub="per day" />
            <KpiCard label="Transactions" value={summary.transaction_count} pctChange={null} icon={Wallet} color="#3b82f6" sub={`in ${PERIODS.find(p => p.value === period)?.label || period}`} />
          </>
        ) : (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ height: 110, background: 'var(--card-bg)', borderRadius: 16, border: '1px solid var(--border)', animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))
        )}
      </div>

      {/* Main Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Cash Flow Chart */}
        <ChartCard
          title="Cash Flow"
          subtitle="Income vs Expenses over time"
          action={
            <div style={{ display: 'flex', gap: 6 }}>
              {['day', 'week', 'month'].map(g => (
                <button key={g} onClick={() => setGroupBy(g)} style={{
                  padding: '3px 8px', borderRadius: 6, border: `1px solid ${groupBy === g ? 'var(--primary)' : 'var(--border)'}`,
                  background: groupBy === g ? 'var(--primary)' : 'transparent',
                  color: groupBy === g ? '#fff' : 'var(--text-muted)',
                  fontSize: 11, fontWeight: 600, cursor: 'pointer'
                }}>
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </button>
              ))}
            </div>
          }
        >
          {loading || !cashFlow ? <Skeleton /> : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={cashFlowData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false}
                  tickFormatter={v => v.length > 7 ? v.slice(5) : v} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={fmt} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="Income" stroke="#10b981" strokeWidth={2} fill="url(#incomeGrad)" dot={false} activeDot={{ r: 4 }} />
                <Area type="monotone" dataKey="Expense" stroke="#ef4444" strokeWidth={2} fill="url(#expenseGrad)" dot={false} activeDot={{ r: 4 }} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Category Donut */}
        <ChartCard
          title="Category Breakdown"
          subtitle={`${catType === 'expense' ? 'Expense' : 'Income'} distribution`}
          action={
            <div style={{ display: 'flex', gap: 4 }}>
              {['expense', 'income'].map(t => (
                <button key={t} onClick={() => setCatType(t)} style={{
                  padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  border: `1px solid ${catType === t ? 'var(--primary)' : 'var(--border)'}`,
                  background: catType === t ? 'var(--primary)' : 'transparent',
                  color: catType === t ? '#fff' : 'var(--text-muted)'
                }}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          }
        >
          {loading || !categories ? <Skeleton /> : catData.length === 0 ? (
            <div style={{ height: 260, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <PieIcon size={40} style={{ opacity: 0.2, marginBottom: 10 }} />
              <div>No data for this period</div>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={catData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                    dataKey="value" paddingAngle={2} stroke="none">
                    {catData.map((entry, i) => (
                      <Cell key={i} fill={entry.color || DONUT_PALETTE[i % DONUT_PALETTE.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => fmtFull(v)} contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxHeight: 120, overflowY: 'auto' }}>
                {catData.slice(0, 6).map((c, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: c.color, flexShrink: 0 }} />
                      <span style={{ color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 100 }}>{c.name}</span>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{c.pct}%</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </ChartCard>
      </div>

      {/* Net Worth + Merchants Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Net Worth Trend */}
        <ChartCard title="Net Worth Trend" subtitle="Cumulative balance over 12 months">
          {loading || !netWorth ? <Skeleton /> : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={netWorthData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false}
                  tickFormatter={v => v.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={fmt} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="Net Worth" stroke="#6366f1" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Top Merchants */}
        <ChartCard title="Top Merchants" subtitle={`Highest spend in last ${PERIODS.find(p => p.value === period)?.label || period}`}>
          {loading || !merchants ? <Skeleton /> : merchantData.length === 0 ? (
            <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', flexDirection: 'column', gap: 8 }}>
              <ShoppingBag size={36} style={{ opacity: 0.2 }} />
              <div>No merchant data for this period</div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={merchantData} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={fmt} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={90}
                  tickFormatter={v => v.length > 12 ? v.slice(0, 12) + '…' : v} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="total" name="Total Spend" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Budget Adherence */}
      <ChartCard title="Budget Adherence" subtitle={`Spending vs budget limits — ${new Date().toLocaleString('en', { month: 'long', year: 'numeric' })}`}>
        {loading || !budgets ? <Skeleton /> : budgets.budgets.length === 0 ? (
          <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Target size={36} style={{ opacity: 0.2, marginBottom: 8 }} />
            <div>No budgets configured for this month.</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0 32px' }}>
            {budgets.budgets.map((b, i) => <BudgetBar key={i} item={b} />)}
          </div>
        )}
      </ChartCard>
    </div>
  );
}
