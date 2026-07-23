import React from 'react';
import {
  FileText, Download, TrendingUp, TrendingDown, Wallet, ShieldCheck,
  Sparkles, Sliders, Target, Calendar, CheckCircle2, ArrowUpRight
} from 'lucide-react';
import Card from '../Common/Card';
import Button from '../Common/Button';

const fmtFull = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
const fmt = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

const DigestViewer = ({ digestData, onDownloadPdf }) => {
  if (!digestData) return null;

  const content = digestData.content || {};
  const health = content.financial_health || {};
  const metrics = content.metrics || {};
  const catSpending = content.category_spending || [];
  const budgets = content.budget_overview || [];
  const goals = content.goal_overview || [];
  const forecast = content.forecast_snapshot || {};

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Digest Header */}
      <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-950/40 via-dark-900 to-dark-950 border border-dark-800 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-xs font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20 w-fit">
            <Sparkles size={14} />
            <span className="uppercase tracking-wider">{digestData.digest_type || 'Monthly'} Executive Digest</span>
            <span className="text-dark-500">•</span>
            <span>{digestData.generated_at ? new Date(digestData.generated_at).toLocaleDateString() : 'Current'}</span>
          </div>
          <h2 className="text-xl md:text-2xl font-extrabold text-white">Financial Activity & Performance Report</h2>
        </div>

        {digestData.has_pdf && (
          <Button variant="primary" onClick={() => onDownloadPdf(digestData.id)} icon={<Download size={14} />}>
            Download PDF Report
          </Button>
        )}
      </div>

      {/* KPI & Health Score Box */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-5 flex items-center space-x-4 border-l-4 border-l-indigo-500">
          <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-xs text-dark-400 font-semibold">Health Score</p>
            <p className="text-2xl font-black text-white">{health.score || digestData.health_score || 88} / 100</p>
            <p className="text-[11px] text-emerald-400 font-medium">{health.status || 'Excellent'}</p>
          </div>
        </Card>

        <Card className="p-5">
          <p className="text-xs text-dark-400 font-semibold">Total Balance</p>
          <p className="text-2xl font-black text-white">{fmtFull(metrics.total_balance)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Across all accounts</p>
        </Card>

        <Card className="p-5">
          <p className="text-xs text-dark-400 font-semibold">Net Surplus</p>
          <p className="text-2xl font-black text-emerald-400">{fmtFull(metrics.period_savings)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Savings Rate: {(metrics.savings_rate || 0).toFixed(1)}%</p>
        </Card>

        <Card className="p-5">
          <p className="text-xs text-dark-400 font-semibold">Estimated Net Worth</p>
          <p className="text-2xl font-black text-white">{fmtFull(metrics.net_worth)}</p>
          <p className="text-[11px] text-dark-400 mt-1">Assets & reserves</p>
        </Card>
      </div>

      {/* Executive Briefing */}
      <Card className="p-6 border-l-4 border-l-emerald-500 bg-gradient-to-r from-emerald-950/20 to-dark-900">
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-2">
            <Sparkles size={14} />
            <span>AI Executive Briefing</span>
          </h3>
          <p className="text-xs md:text-sm text-dark-200 leading-relaxed">
            {digestData.summary || content.ai_executive_summary}
          </p>
        </div>
      </Card>

      {/* Category Expenses & Budgets Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Top Spending Categories</h3>
          <div className="space-y-3">
            {catSpending.slice(0, 5).map((cat, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-dark-950 border border-dark-850 flex items-center justify-between text-xs">
                <span className="font-bold text-white">{cat.category}</span>
                <span className="font-semibold text-indigo-400">{fmt(cat.amount)}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Budget Limits & Burn Rates</h3>
          <div className="space-y-3">
            {budgets.slice(0, 5).map((b, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-dark-950 border border-dark-850 flex items-center justify-between text-xs">
                <div>
                  <p className="font-bold text-white">{b.category}</p>
                  <p className="text-[10px] text-dark-400">Limit: {fmt(b.budget_amount)}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  b.risk_level === 'critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {fmt(b.spent_amount)} ({b.burn_rate_pct}%)
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 30-Day Forecast Snapshot */}
      <Card className="p-6 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">30-Day Forecast Trajectory</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850">
            <p className="text-xs text-dark-400">Projected End Balance</p>
            <p className="text-lg font-black text-white mt-1">{fmtFull(forecast.projected_end_balance)}</p>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850">
            <p className="text-xs text-dark-400">Expected Net Surplus</p>
            <p className="text-lg font-black text-emerald-400 mt-1">{fmtFull(forecast.expected_surplus)}</p>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850">
            <p className="text-xs text-dark-400">Confidence Score</p>
            <p className="text-lg font-black text-indigo-400 mt-1">{Math.round((forecast.confidence_score || 0.88) * 100)}%</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default DigestViewer;
