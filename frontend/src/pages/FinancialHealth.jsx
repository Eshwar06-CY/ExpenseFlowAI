import React, { useState, useEffect } from 'react';
import { ShieldCheck, Heart, AlertTriangle, TrendingUp, DollarSign, Percent, Pocket, Award, RotateCw } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';

const FinancialHealth = () => {
  const { addToast } = useToast();
  const [health, setHealth] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const [healthRes, recRes] = await Promise.all([
        api.get('/planning/financial-health'),
        api.get('/planning/budget-recommendations')
      ]);
      setHealth(healthRes.data);
      setRecommendations(recRes.data);
    } catch (err) {
      addToast('Failed to load financial health parameters.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
  }, []);

  const handleApplyBudget = async (rec) => {
    try {
      setActionLoading(true);
      const currentMonth = new Date().toISOString().substring(0, 7); // YYYY-MM
      
      // 1. Get current budgets to see if we edit or create
      const budgetsRes = await api.get(`/budgets/?month=${currentMonth}`);
      const existing = budgetsRes.data.find(b => b.category_id === rec.category_id);

      if (existing) {
        // Edit existing
        await api.put(`/budgets/${existing.id}`, { amount: rec.recommended_budget });
        addToast(`Budget for ${rec.category_name} updated to $${rec.recommended_budget}.`, 'success');
      } else {
        // Create new
        await api.post('/budgets/', {
          category_id: rec.category_id,
          amount: rec.recommended_budget,
          month: currentMonth
        });
        addToast(`Budget for ${rec.category_name} created at $${rec.recommended_budget}.`, 'success');
      }

      // Reload recommendations
      const updatedRecs = await api.get('/planning/budget-recommendations');
      setRecommendations(updatedRecs.data);
    } catch (err) {
      addToast('Failed to apply recommended budget.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center text-xs text-dark-400 animate-pulse">
        <RotateCw className="w-5 h-5 animate-spin mr-2 text-brand-500" /> Generating Health Audit Score...
      </div>
    );
  }

  // Health Score Circular Gauge Math
  const score = health?.health_score || 0;
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  let scoreColor = "stroke-rose-500 text-rose-500";
  if (score >= 80) scoreColor = "stroke-green-400 text-green-400";
  else if (score >= 50) scoreColor = "stroke-amber-400 text-amber-400";

  // Trends Line Chart SVG Math
  const getTrendPath = (trend) => {
    if (!trend || trend.length < 2) return '';
    const width = 280;
    const height = 100;
    const padding = 10;
    const xStep = (width - padding * 2) / (trend.length - 1);
    
    return trend.map((t, idx) => {
      const x = padding + idx * xStep;
      const y = height - padding - (t.score / 100) * (height - padding * 2);
      return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const trendPath = getTrendPath(health?.historical_health_trend);

  return (
    <div className="space-y-8 pb-12 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight flex items-center gap-2">
          <Heart className="w-8 h-8 text-rose-500 animate-pulse" /> Financial Health Audit
        </h2>
        <p className="text-xs text-dark-400 mt-1">Review multi-metric coverage indices, savings margins, and automated category budget recommendations.</p>
      </div>

      {/* Health Score & Trend Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Score Radial Dial */}
        <Card isGlass={true} title="Overall Health Score" className="flex flex-col items-center justify-center text-center">
          <div className="relative w-32 h-32 flex items-center justify-center my-2">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="64" cy="64" r={radius} className="stroke-dark-800" strokeWidth="8" fill="transparent" />
              <circle
                cx="64"
                cy="64"
                r={radius}
                className={`${scoreColor} transition-all duration-1000 ease-out`}
                strokeWidth="8"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-white">{score}</span>
              <span className="text-[9px] uppercase font-bold text-dark-400">Score</span>
            </div>
          </div>
          <p className="text-xs text-dark-400 mt-2 px-2 leading-relaxed">
            {score >= 80 ? "Excellent balance sheets! Highly sustainable margins." : score >= 50 ? "Moderate health. Consider aligning dekat budget caps." : "High Risk! Emergency funds are low; reduce category outflows."}
          </p>
        </Card>

        {/* Health Trend Chart */}
        <Card isGlass={true} title="Score History Trend" subtitle="Composite rating over past months">
          {health?.historical_health_trend.length < 2 ? (
            <div className="h-28 flex items-center justify-center text-[10px] text-dark-500 italic">No history available</div>
          ) : (
            <div className="space-y-4 pt-2">
              <div className="h-24 w-full bg-dark-950/40 rounded-xl p-2 border border-dark-850 flex items-center">
                <svg className="w-full h-full" viewBox="0 0 280 100" preserveAspectRatio="none">
                  <path d={trendPath} fill="none" className="stroke-brand-500" strokeWidth="2.5" strokeLinecap="round" />
                </svg>
              </div>
              <div className="flex justify-between px-1 text-[9px] text-dark-500 font-mono">
                {health?.historical_health_trend.map((t, idx) => (
                  <span key={idx}>{t.month}</span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Quick metrics summary */}
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-2 md:grid-cols-1">
          <div className="bg-dark-900 border border-dark-850 p-3.5 rounded-2xl flex items-center gap-3">
            <div className="p-2 bg-green-500/10 border border-green-500/20 text-green-400 rounded-xl">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-dark-400">Savings Margin</p>
              <p className="text-base font-black text-dark-100">{health?.savings_rate}%</p>
            </div>
          </div>

          <div className="bg-dark-900 border border-dark-850 p-3.5 rounded-2xl flex items-center gap-3">
            <div className="p-2 bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-xl">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-dark-400">Emergency Fund</p>
              <p className="text-base font-black text-dark-100">{health?.emergency_fund_coverage_months} Months</p>
            </div>
          </div>

          <div className="bg-dark-900 border border-dark-850 p-3.5 rounded-2xl flex items-center gap-3">
            <div className="p-2 bg-cyanFlow-500/10 border border-cyanFlow-500/20 text-cyanFlow-400 rounded-xl">
              <DollarSign className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-dark-400">Projected 30d Balance</p>
              <p className="text-base font-black text-dark-100 font-mono">₹{health?.projected_30d_balance?.toLocaleString()}</p>
            </div>
          </div>

          <div className="bg-dark-900 border border-dark-850 p-3.5 rounded-2xl flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-dark-400">Bill Reliability</p>
              <p className="text-base font-black text-dark-100">{health?.bill_payment_rate}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recommendations list */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Category Budget Recommendations" subtitle="Statistical average category outflows and suggested budget limits">
            {recommendations.length === 0 ? (
              <div className="py-12 text-center text-xs text-dark-500 italic">
                Log some transactions to trigger budget recommendation suggestions.
              </div>
            ) : (
              <div className="space-y-3.5">
                {recommendations.map((rec) => (
                  <div
                    key={rec.category_id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                      rec.status === 'overspending_risk'
                        ? 'bg-rose-500/5 border-rose-500/10'
                        : rec.status === 'underspending_opportunity'
                        ? 'bg-green-500/5 border-green-500/10'
                        : 'bg-dark-900 border-dark-850'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-dark-100">{rec.category_name}</span>
                        {rec.status === 'overspending_risk' && (
                          <span className="px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-[8px] font-bold text-rose-400 uppercase tracking-wider">
                            Overspending Risk
                          </span>
                        )}
                        {rec.status === 'underspending_opportunity' && (
                          <span className="px-1.5 py-0.5 rounded bg-green-500/10 border border-green-500/20 text-[8px] font-bold text-green-450 uppercase tracking-wider">
                            Surplus Saving Opportunity
                          </span>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 text-[10px] text-dark-450 font-mono">
                        <span>90d avg: ${rec.avg_monthly_spending.toLocaleString()}/mo</span>
                        <span>•</span>
                        <span>Current Budget: {rec.current_budget ? `$${rec.current_budget.toLocaleString()}` : 'None'}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right sm:text-right">
                        <p className="text-[9px] uppercase font-bold text-dark-550">Recommended Cap</p>
                        <p className="text-xs font-extrabold text-brand-400 font-mono">${rec.recommended_budget.toLocaleString()}</p>
                      </div>
                      
                      <Button
                        variant="secondary"
                        size="xs"
                        disabled={actionLoading}
                        onClick={() => handleApplyBudget(rec)}
                        className="py-1.5 px-3 text-xs"
                      >
                        Apply Recommended
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Health Insights Panel */}
        <div className="space-y-6">
          <Card title="Financial Advice Summary" subtitle="Determined using rules engines">
            <div className="space-y-4 text-xs text-dark-350 leading-relaxed">
              <div className="p-4 bg-dark-900 border border-dark-850 rounded-2xl space-y-2">
                <h4 className="font-bold text-dark-100 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-green-400" /> Capital Protection Check
                </h4>
                <p className="text-[11px] text-dark-400">
                  Your Emergency Fund coverage is at {health?.emergency_fund_coverage_months} months. A standard stable baseline is 3.0 to 6.0 months.
                </p>
              </div>

              <div className="p-4 bg-dark-900 border border-dark-850 rounded-2xl space-y-2">
                <h4 className="font-bold text-dark-100 flex items-center gap-1.5">
                  <Percent className="w-4 h-4 text-brand-400" /> Savings Flow Efficiency
                </h4>
                <p className="text-[11px] text-dark-400">
                  Your current savings margin is {health?.savings_rate}%. Focus on maintaining savings rate above 20% to achieve your milestones.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default FinancialHealth;
