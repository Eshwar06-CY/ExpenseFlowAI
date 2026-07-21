import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Trash2, Calendar, DollarSign, X, AlertCircle, CheckCircle2, RotateCw, RefreshCw } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Recurring = () => {
  const [schedules, setSchedules] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);

  // Form Fields
  const [type, setType] = useState('expense');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('monthly');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [accountId, setAccountId] = useState('');
  const [categoryId, setCategoryId] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [schRes, acctsRes, catsRes] = await Promise.all([
        api.get('/recurring/'),
        api.get('/accounts'),
        api.get('/categories')
      ]);
      setSchedules(schRes.data);
      setAccounts(acctsRes.data);
      setCategories(catsRes.data);
    } catch (err) {
      setError('Failed to fetch recurring rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setEditingSchedule(null);
    setType('expense');
    setAmount('');
    setDescription('');
    setFrequency('monthly');
    setStartDate(new Date().toISOString().split('T')[0]);
    setAccountId(accounts[0]?.id || '');
    setCategoryId(categories[0]?.id || '');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (sch) => {
    setEditingSchedule(sch);
    setType(sch.type);
    setAmount(sch.amount.toString());
    setDescription(sch.description);
    setFrequency(sch.frequency);
    setStartDate(sch.start_date.split('T')[0]);
    setAccountId(sch.account_id);
    setCategoryId(sch.category_id || '');
    setIsModalOpen(true);
  };

  const handleProcessRules = async () => {
    try {
      setProcessing(true);
      setError('');
      setSuccess('');
      const res = await api.post('/recurring/process');
      const count = res.data.generated_transactions_count;
      if (count > 0) {
        setSuccess(`Scheduler processing complete: Generated ${count} transactions in ledger!`);
        loadData();
      } else {
        setSuccess('Scheduler processing complete: All cycles are up to date.');
      }
    } catch (err) {
      setError('Failed to execute rule processor.');
    } finally {
      setProcessing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!description.trim()) {
      setError('Please provide a description.');
      return;
    }
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a positive amount.');
      return;
    }

    const payload = {
      type,
      amount: parseFloat(amount),
      description,
      frequency,
      start_date: new Date(startDate).toISOString(),
      account_id: parseInt(accountId),
      category_id: categoryId ? parseInt(categoryId) : null
    };

    try {
      if (editingSchedule) {
        await api.put(`/recurring/${editingSchedule.id}`, payload);
        setSuccess('Recurring schedule updated.');
      } else {
        await api.post('/recurring/', payload);
        setSuccess('Recurring schedule registered successfully.');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving recurring transaction rule.');
    }
  };

  const handleDelete = async (ruleId) => {
    if (!window.confirm('Are you sure you want to delete this recurring schedule rule?')) return;
    try {
      await api.delete(`/recurring/${ruleId}`);
      setSchedules(schedules.filter(s => s.id !== ruleId));
      setSuccess('Recurring schedule rule deleted.');
    } catch (err) {
      setError('Failed to delete schedule.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Recurring Schedules</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Configure automated recurring income or expenses matching calendar cycles.</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Button 
            onClick={handleProcessRules} 
            variant="secondary" 
            size="sm" 
            disabled={processing}
            className="flex items-center gap-2"
          >
            <RefreshCw size={16} className={processing ? "animate-spin" : ""} /> Run Processor
          </Button>
          <Button onClick={handleOpenCreate} size="sm" className="flex items-center gap-2">
            <Plus size={16} /> New Rule
          </Button>
        </div>
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
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : schedules.length === 0 ? (
        <Card className="text-center py-12">
          <RotateCw className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
          <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-1">No Recurring Transaction Rules</h3>
          <p className="text-gray-400 dark:text-gray-500 text-sm max-w-sm mx-auto mb-4">
            Set up automatic rents, dividends, salary deposits, or subscription charges.
          </p>
          <Button onClick={handleOpenCreate} variant="secondary" size="sm">
            Add First Schedule
          </Button>
        </Card>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-900/50 text-gray-400 text-xs font-semibold uppercase border-b border-gray-100 dark:border-gray-700">
                  <th className="px-6 py-4">Rule Description</th>
                  <th className="px-6 py-4">Frequency</th>
                  <th className="px-6 py-4">Amount</th>
                  <th className="px-6 py-4">Target Account</th>
                  <th className="px-6 py-4">Next Run</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-sm text-gray-700 dark:text-gray-300">
                {schedules.map((sch) => (
                  <tr key={sch.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                      <div className="flex items-center gap-3">
                        <span className={`w-2.5 h-2.5 rounded-full ${sch.type === 'income' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                        <div>
                          <p>{sch.description}</p>
                          <p className="text-xs text-gray-400 font-normal">{sch.category?.name || 'Uncategorized'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 capitalize font-semibold text-indigo-600 dark:text-indigo-400">
                      {sch.frequency}
                    </td>
                    <td className={`px-6 py-4 font-bold ${sch.type === 'income' ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {sch.type === 'income' ? '+' : '-'}${sch.amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      {sch.account?.name || 'Account'}
                    </td>
                    <td className="px-6 py-4">
                      {new Date(sch.next_run).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                      <button 
                        onClick={() => handleOpenEdit(sch)} 
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 rounded-md"
                        title="Edit Rule"
                      >
                        <Edit3 size={15} />
                      </button>
                      <button 
                        onClick={() => handleDelete(sch.id)} 
                        className="p-1.5 hover:bg-red-50 dark:hover:bg-red-950/30 text-red-500 rounded-md"
                        title="Delete Rule"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Set/Edit Schedule Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in">
          <Card className="w-full max-w-md shadow-2xl relative">
            <button 
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X size={18} />
            </button>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              {editingSchedule ? 'Modify Schedule Rule' : 'Add Recurring Schedule'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="radio"
                    name="type"
                    value="expense"
                    checked={type === 'expense'}
                    onChange={() => setType('expense')}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  Recurring Expense
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="radio"
                    name="type"
                    value="income"
                    checked={type === 'income'}
                    onChange={() => setType('income')}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  Recurring Income
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Description</label>
                <input
                  type="text"
                  placeholder="e.g. Monthly rent, Gym subscription"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Amount</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                      <DollarSign size={15} />
                    </div>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full pl-8 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Frequency</label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Target Account</label>
                  <select
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Category (Optional)</label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">-- No Category --</option>
                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Start Date</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <Calendar size={16} />
                  </div>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingSchedule ? 'Save Changes' : 'Schedule Auto-posting'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Recurring;
