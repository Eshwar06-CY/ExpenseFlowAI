import React, { useState, useEffect } from 'react';
import { LineChart, Play, Sparkles, TrendingUp, DollarSign, Plus, Trash2, CheckCircle2, RotateCw } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';

const ForecastDashboard = () => {
  const { addToast } = useToast();
  const [forecast, setForecast] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Scenario Creation Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState({
    name: '',
    type: 'salary_increase',
    amount: 0.0,
    category_id: '',
    percent_change: 0.0,
    one_off_date: ''
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [forecastRes, scenariosRes, categoriesRes] = await Promise.all([
        api.get('/planning/forecast'),
        api.get('/planning/scenarios'),
        api.get('/categories')
      ]);
      setForecast(forecastRes.data);
      setScenarios(scenariosRes.data);
      setCategories(categoriesRes.data);
    } catch (err) {
      addToast('Failed to fetch forecasting data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleActive = async (id, currentStatus) => {
    try {
      setActionLoading(true);
      await api.put(`/planning/scenarios/${id}`, { is_active: !currentStatus });
      addToast('Forecast scenario updated.', 'success');
      
      // Reload forecast immediately
      const fRes = await api.get('/planning/forecast');
      setForecast(fRes.data);
      
      // Update scenarios list locally
      setScenarios(scenarios.map(s => s.id === id ? { ...s, is_active: !currentStatus } : s));
    } catch (err) {
      addToast('Failed to toggle scenario status.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteScenario = async (id) => {
    try {
      setActionLoading(true);
      await api.delete(`/planning/scenarios/${id}`);
      addToast('Scenario removed.', 'success');
      
      const fRes = await api.get('/planning/forecast');
      setForecast(fRes.data);
      setScenarios(scenarios.filter(s => s.id !== id));
    } catch (err) {
      addToast('Failed to delete scenario.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateScenario = async (e) => {
    e.preventDefault();
    if (!form.name || form.amount <= 0) {
      addToast('Please enter a scenario name and valid amount.', 'warning');
      return;
    }

    try {
      setActionLoading(true);
      const payload = {
        name: form.name,
        type: form.type,
        amount: parseFloat(form.amount),
        category_id: form.category_id ? parseInt(form.category_id) : null,
        percent_change: form.type === 'spend_reduction' ? -Math.abs(parseFloat(form.percent_change)) : null,
        one_off_date: form.type === 'one_off_purchase' && form.one_off_date ? new Date(form.one_off_date).toISOString() : null,
        is_active: true
      };

      const res = await api.post('/planning/scenarios', payload);
      setScenarios([...scenarios, res.data]);
      setShowAddForm(false);
      setForm({ name: '', type: 'salary_increase', amount: 0.0, category_id: '', percent_change: 0.0, one_off_date: '' });
      addToast('What-If scenario saved and applied to forecast.', 'success');

      // Reload forecast
      const fRes = await api.get('/planning/forecast');
      setForecast(fRes.data);
    } catch (err) {
      addToast('Failed to create scenario.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // SVG Line Chart Math
  const getSvgPath = (points) => {
    if (!points || points.length < 2) return '';
    const width = 600;
    const height = 180;
    const padding = 20;
    const xStep = (width - padding * 2) / (points.length - 1);
    
    const balances = points.map(p => p.balance);
    const maxVal = Math.max(...balances, 1000);
    const minVal = Math.min(...balances, 0);
    const range = maxVal - minVal || 1000;

    return points.map((p, index) => {
      const x = padding + index * xStep;
      const y = height - padding - ((p.balance - minVal) / range) * (height - padding * 2);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center text-dark-400 text-xs animate-pulse">
        <RotateCw className="w-6 h-6 animate-spin text-brand-500 mr-2" /> Generating Cash Flow Forecast Timeline...
      </div>
    );
  }

  const timelinePoints = forecast?.timeline || [];
  const chartPath = getSvgPath(timelinePoints);

  const balance7d = forecast?.balance_7d ?? 0;
  const balance30d = forecast?.balance_30d ?? 0;
  const balance90d = forecast?.balance_90d ?? 0;
  const surplus = forecast?.monthly_surplus ?? 0;

  return (
    <div className="space-y-8 pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight flex items-center gap-2">
            <LineChart className="w-8 h-8 text-brand-500" /> Cash Flow Simulator
          </h2>
          <p className="text-xs text-dark-400 mt-1">Project cash reserves 90 days out and evaluate What-If options.</p>
        </div>
      </div>

      {/* Projections benchmarks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card isGlass={true} className="hover-lift">
          <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Projected 7 Days Balance</p>
          <h3 className="text-2xl font-bold mt-2 font-mono text-dark-100">
            ${balance7d.toLocaleString()}
          </h3>
          <span className="text-[10px] text-dark-550 block mt-2">Expected next week reserves</span>
        </Card>

        <Card isGlass={true} className="hover-lift">
          <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Projected 30 Days Balance</p>
          <h3 className={`text-2xl font-bold mt-2 font-mono ${balance30d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            ${balance30d.toLocaleString()}
          </h3>
          <span className="text-[10px] text-dark-550 block mt-2">Expected next month reserves</span>
        </Card>

        <Card isGlass={true} className="hover-lift">
          <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Projected 90 Days Balance</p>
          <h3 className={`text-2xl font-bold mt-2 font-mono ${balance90d >= 0 ? 'text-brand-400' : 'text-red-450'}`}>
            ${balance90d.toLocaleString()}
          </h3>
          <span className="text-[10px] text-dark-550 block mt-2">Quarterly timeline forecast target</span>
        </Card>

        <Card isGlass={true} className="hover-lift">
          <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Average Monthly Surplus</p>
          <h3 className={`text-2xl font-bold mt-2 font-mono ${surplus >= 0 ? 'text-green-450' : 'text-rose-500'}`}>
            ${surplus.toLocaleString()}
          </h3>
          <span className="text-[10px] text-dark-550 block mt-2">Avg income/expense surplus margin</span>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forecast Timeline Chart */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="90-Day Projected Cash Curve" subtitle="Projections mapping upcoming recurring events and active What-If items">
            {timelinePoints.length < 2 ? (
              <div className="h-64 flex items-center justify-center text-xs text-dark-500 italic">
                Add recurring salary/bills to map forecast curves.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-60 w-full bg-dark-950/40 rounded-xl p-4 border border-dark-850 flex items-center">
                  <svg className="w-full h-full" viewBox="0 0 600 180" preserveAspectRatio="none">
                    {/* Zero line threshold */}
                    <line x1="20" y1="90" x2="580" y2="90" className="stroke-red-500/20" strokeDasharray="3" />
                    
                    {/* Path */}
                    <path
                      d={chartPath}
                      fill="none"
                      className="stroke-brand-500"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <div className="flex justify-between px-2 text-[10px] text-dark-500 font-mono font-semibold">
                  <span>Today</span>
                  <span>+30 Days</span>
                  <span>+60 Days</span>
                  <span>+90 Days</span>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* What-If Scenarios Panel */}
        <div className="space-y-6">
          <Card title="What-If Planning Scenarios" subtitle="Toggle scenario variables to project curves instantly">
            <div className="space-y-4">
              {/* Scenario items list */}
              {scenarios.length === 0 ? (
                <div className="py-6 text-center text-xs text-dark-500 italic border border-dashed border-dark-800 rounded-xl">
                  No What-If scenarios configured.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {scenarios.map((scen) => (
                    <div
                      key={scen.id}
                      className={`p-3 rounded-xl border flex items-center justify-between text-xs transition-all ${
                        scen.is_active
                          ? 'bg-brand-600/10 border-brand-500/30'
                          : 'bg-dark-900 border-dark-850 opacity-60'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <p className="font-bold text-dark-150 truncate">{scen.name}</p>
                        <p className="text-[10px] text-dark-450 mt-0.5 capitalize">
                          {scen.type.replace('_', ' ')} • ${scen.amount.toLocaleString()}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleToggleActive(scen.id, scen.is_active)}
                          disabled={actionLoading}
                          className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition-all ${
                            scen.is_active
                              ? 'bg-brand-600 text-white'
                              : 'bg-dark-950 text-dark-400 border border-dark-800 hover:text-dark-250'
                          }`}
                        >
                          {scen.is_active ? 'Active' : 'Disabled'}
                        </button>
                        <button
                          onClick={() => handleDeleteScenario(scen.id)}
                          disabled={actionLoading}
                          className="p-1.5 bg-dark-950 border border-dark-800 hover:border-red-500/30 text-dark-450 hover:text-red-400 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Add form toggle */}
              {!showAddForm ? (
                <Button
                  variant="secondary"
                  onClick={() => setShowAddForm(true)}
                  className="w-full text-xs py-2 flex items-center justify-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Scenario Rule
                </Button>
              ) : (
                <form onSubmit={handleCreateScenario} className="p-4 bg-dark-950 border border-dark-850 rounded-xl space-y-3.5">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-dark-400 uppercase">Scenario Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Rent Increase, Promo"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full bg-dark-900 border border-dark-800 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500"
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-dark-400 uppercase">Scenario Type</label>
                    <select
                      value={form.type}
                      onChange={(e) => setForm({ ...form, type: e.target.value })}
                      className="w-full bg-dark-900 border border-dark-800 rounded-lg px-2 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500"
                    >
                      <option value="salary_increase">Salary/Income Increase (Monthly)</option>
                      <option value="rent_increase">Rent/Bills Increase (Monthly)</option>
                      <option value="one_off_purchase">One-off Purchase</option>
                      <option value="spend_reduction">Spend Category Reduction (%)</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-dark-400 uppercase">
                      {form.type === 'spend_reduction' ? 'Percentage Change (%)' : 'Amount ($)'}
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={form.type === 'spend_reduction' ? form.percent_change : form.amount}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value);
                        if (form.type === 'spend_reduction') {
                          setForm({ ...form, percent_change: val });
                        } else {
                          setForm({ ...form, amount: val });
                        }
                      }}
                      className="w-full bg-dark-900 border border-dark-800 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500 font-mono"
                      required
                    />
                  </div>

                  {form.type === 'spend_reduction' && (
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-dark-400 uppercase">Target Category</label>
                      <select
                        value={form.category_id}
                        onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                        className="w-full bg-dark-900 border border-dark-800 rounded-lg px-2 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500"
                        required
                      >
                        <option value="">-- Choose Category --</option>
                        {categories.map(c => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {form.type === 'one_off_purchase' && (
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-dark-400 uppercase">Purchase Date</label>
                      <input
                        type="date"
                        value={form.one_off_date}
                        onChange={(e) => setForm({ ...form, one_off_date: e.target.value })}
                        className="w-full bg-dark-900 border border-dark-800 rounded-lg px-2.5 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500"
                        required
                      />
                    </div>
                  )}

                  <div className="flex gap-2 pt-1.5">
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={actionLoading}
                      className="flex-1 py-1.5 text-xs flex justify-center items-center gap-1.5"
                    >
                      {actionLoading ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <>Save Scenario <CheckCircle2 className="w-3.5 h-3.5" /></>}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setShowAddForm(false)}
                      className="py-1.5 text-xs"
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ForecastDashboard;
