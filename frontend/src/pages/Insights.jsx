import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, AlertCircle, CheckCircle2, TrendingUp, Calendar, Zap, DollarSign, HelpCircle, X } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Insights = () => {
  const [insights, setInsights] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [insRes, evtsRes] = await Promise.all([
        api.get('/insights/'),
        api.get('/insights/events')
      ]);
      setInsights(insRes.data);
      setEvents(evtsRes.data);
    } catch (err) {
      setError('Failed to fetch financial intelligence insights.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError('');
      setSuccess('');
      await api.post('/insights/generate');
      setSuccess('Financial Intelligence Engine analyzed your transactions successfully!');
      loadData();
    } catch (err) {
      setError('Failed to run intelligence analytics. Add some accounts and transaction data.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDismissEvent = async (eventId) => {
    try {
      await api.post(`/insights/events/${eventId}/dismiss`);
      setEvents(events.filter(e => e.id !== eventId));
    } catch (err) {
      setError('Failed to dismiss alert.');
    }
  };

  // Find specific insight types
  const trendInsight = insights.find(i => i.type === 'trend');
  const patternInsight = insights.find(i => i.type === 'pattern');
  const forecastInsight = insights.find(i => i.type === 'forecast');
  const healthInsight = insights.find(i => i.type === 'health');

  // SVG Line Chart coordinates for Forecast
  const forecastList = forecastInsight?.data?.forecast || [];
  const maxForecastVal = forecastList.length > 0 ? Math.max(...forecastList.map(f => f.balance), 1) : 1000;
  const minForecastVal = forecastList.length > 0 ? Math.min(...forecastList.map(f => f.balance), 0) : 0;
  const valRange = maxForecastVal - minForecastVal;

  const getForecastCoordinates = () => {
    if (forecastList.length < 2) return '';
    const width = 500;
    const height = 140;
    const padding = 15;
    const xStep = (width - padding * 2) / (forecastList.length - 1);
    
    return forecastList.map((f, index) => {
      const x = padding + index * xStep;
      const y = height - padding - ((f.balance - minForecastVal) / (valRange || 1)) * (height - padding * 2);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const forecastPath = getForecastCoordinates();

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
            <Sparkles className="text-brand-500" /> Financial Intelligence
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
            Modular intelligence engine compiling spending runs, recurring schedules, and net forecasts.
          </p>
        </div>
        <Button 
          onClick={handleGenerate} 
          disabled={generating} 
          className="flex items-center gap-2 font-semibold shadow-md shadow-brand-500/10"
        >
          <RefreshCw size={16} className={generating ? "animate-spin" : ""} />
          {generating ? 'Parsing Ledger...' : 'Run Insights Engine'}
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-xl text-sm border border-red-100 dark:border-red-900/50">
          <AlertCircle size={18} className="flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 p-4 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-xl text-sm border border-emerald-100 dark:border-emerald-900/50">
          <CheckCircle2 size={18} className="flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Forecast & Analysis Columns */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* 30-Day Liquidity Forecast */}
            <Card title="30-Day Projected Net Balance" subtitle="Projected cash flows based on active schedules">
              {forecastList.length < 2 ? (
                <div className="h-44 flex items-center justify-center text-gray-400 text-xs italic">
                  Not enough recurring schedules to calculate 30-day projection paths.
                </div>
              ) : (
                <div className="space-y-4 py-2">
                  <div className="h-36 w-full">
                    <svg className="w-full h-full" viewBox="0 0 500 140" preserveAspectRatio="none">
                      {/* Grid Lines */}
                      {[0, 0.25, 0.5, 0.75, 1].map((r, i) => (
                        <line 
                          key={i} 
                          x1="15" y1={15 + r * 110} 
                          x2="485" y2={15 + r * 110} 
                          className="stroke-gray-100 dark:stroke-gray-800" 
                          strokeWidth="0.5" 
                          strokeDasharray="4"
                        />
                      ))}
                      
                      {/* Forecast Line */}
                      <path 
                        d={forecastPath} 
                        fill="none" 
                        className="stroke-indigo-600 dark:stroke-indigo-500" 
                        strokeWidth="2.5" 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                      />
                    </svg>
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-400">
                    <span>Today (${forecastList[0]?.balance.toLocaleString()})</span>
                    <span>15 Days (${forecastList[14]?.balance.toLocaleString()})</span>
                    <span>30 Days (${forecastList[forecastList.length - 1]?.balance.toLocaleString()})</span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs border-t border-gray-100 dark:border-gray-800 pt-3 text-gray-500">
                    <span>Projected Month-End Balance:</span>
                    <span className={`font-bold text-sm ${forecastList[forecastList.length - 1]?.balance >= forecastList[0]?.balance ? 'text-emerald-600' : 'text-rose-500'}`}>
                      ${forecastList[forecastList.length - 1]?.balance.toLocaleString()}
                    </span>
                  </div>
                </div>
              )}
            </Card>

            {/* Category spending trends */}
            <Card title="Outflow Category Trends" subtitle="Structured spending weights">
              {!trendInsight?.data?.category_breakdown ? (
                <p className="text-xs text-gray-400 italic">No category insights compiled yet.</p>
              ) : (
                <div className="space-y-3.5 py-1">
                  {Object.entries(trendInsight.data.category_breakdown).map(([catName, amount], i) => {
                    const total = Object.values(trendInsight.data.category_breakdown).reduce((a, b) => a + b, 0);
                    const pct = total > 0 ? (amount / total) * 100 : 0;
                    
                    return (
                      <div key={i} className="text-xs">
                        <div className="flex justify-between mb-1.5 text-gray-700 dark:text-gray-300">
                          <span className="font-semibold">{catName}</span>
                          <span>${amount.toLocaleString()} ({pct.toFixed(0)}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full" 
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>

            {/* Detected Recurring Patterns / Subscriptions */}
            <Card title="Detected Recurring Payments & Subscriptions" subtitle="Repeating ledger descriptions caught by processor">
              {!patternInsight?.data?.recurring_patterns || patternInsight.data.recurring_patterns.length === 0 ? (
                <div className="py-6 text-center text-xs text-gray-400 italic">
                  No subscription profiles or uniform repeating schedules detected in expenses.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {patternInsight.data.recurring_patterns.map((pat, idx) => (
                    <div key={idx} className="p-3.5 bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800 rounded-xl space-y-2">
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-xs text-gray-800 dark:text-gray-200">{pat.name}</h4>
                        <span className="text-[10px] uppercase font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded">
                          {pat.frequency}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-500">
                        Repeated {pat.frequency_count} times, spaced on average every {pat.average_interval_days} days.
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right Side Health & Warnings Columns */}
          <div className="space-y-6">
            
            {/* Financial Health Scores */}
            <Card title="Financial Health Metrics" subtitle="Core indicators of financial balance">
              {!healthInsight?.data ? (
                <p className="text-xs text-gray-400 italic">Health analysis pending engine run.</p>
              ) : (
                <div className="space-y-4 py-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 dark:bg-gray-800/40 p-3 rounded-xl border border-gray-100 dark:border-gray-800 text-center">
                      <p className="text-[10px] text-gray-400 font-semibold uppercase">Savings Rate</p>
                      <p className={`text-xl font-bold mt-1 ${healthInsight.data.savings_rate >= 10 ? 'text-emerald-500' : 'text-gray-300'}`}>
                        {healthInsight.data.savings_rate}%
                      </p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-800/40 p-3 rounded-xl border border-gray-100 dark:border-gray-800 text-center">
                      <p className="text-[10px] text-gray-400 font-semibold uppercase">Runway Reserve</p>
                      <p className="text-xl font-bold mt-1 text-white">
                        {healthInsight.data.burn_rate_months} <span className="text-[11px] text-gray-400 font-medium">mos</span>
                      </p>
                    </div>
                  </div>

                  <div className="text-xs space-y-2 text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-100 dark:border-gray-800">
                    <div className="flex justify-between">
                      <span>Monthly Income:</span>
                      <span className="font-bold text-gray-800 dark:text-gray-200">${healthInsight.data.monthly_income.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Monthly Expenses:</span>
                      <span className="font-bold text-gray-800 dark:text-gray-200">${healthInsight.data.monthly_expenses.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Budget Adherence Rate:</span>
                      <span className="font-bold text-gray-800 dark:text-gray-200">{healthInsight.data.budget_adherence_rate}%</span>
                    </div>
                  </div>
                </div>
              )}
            </Card>

            {/* Severity events and notifications */}
            <Card title="Active Events & Alerts" subtitle="Significant events detected in workspace">
              {events.length === 0 ? (
                <div className="py-8 text-center text-xs text-gray-400 italic">
                  No active warnings. Financial parameters stable.
                </div>
              ) : (
                <div className="space-y-3">
                  {events.map((evt) => {
                    const isHigh = evt.severity === 'high';
                    return (
                      <div 
                        key={evt.id} 
                        className={`p-3 rounded-xl border flex gap-3 items-start justify-between relative group ${
                          isHigh 
                            ? 'bg-rose-50/30 border-rose-950/20 text-rose-300' 
                            : 'bg-amber-50/30 border-amber-950/20 text-amber-300'
                        }`}
                      >
                        <div className="flex gap-2">
                          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                          <div>
                            <h5 className="font-bold text-xs text-gray-900 dark:text-white leading-snug">{evt.title}</h5>
                            <p className="text-[10px] text-gray-500 dark:text-gray-450 mt-1 leading-normal">
                              {evt.description}
                            </p>
                          </div>
                        </div>
                        <button 
                          onClick={() => handleDismissEvent(evt.id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                          title="Dismiss Alert"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Insights;
