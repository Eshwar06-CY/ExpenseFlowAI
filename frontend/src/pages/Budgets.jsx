import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Trash2, Calendar, DollarSign, X, AlertCircle, CheckCircle2, Sliders } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Budgets = () => {
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Month select
  const currentMonthStr = new Date().toISOString().slice(0, 7);
  const [selectedMonth, setSelectedMonth] = useState(currentMonthStr);

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);

  // Form Fields
  const [amount, setAmount] = useState('');
  const [categoryId, setCategoryId] = useState('');

  // Confirm Dialog State
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [budRes, catRes] = await Promise.all([
        api.get(`/budgets?month=${selectedMonth}`),
        api.get('/categories')
      ]);
      setBudgets(budRes.data);
      setCategories(catRes.data.filter(c => c.type === 'expense'));
    } catch (err) {
      setError('Failed to load budget records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMonth]);

  const handleOpenCreate = () => {
    setEditingBudget(null);
    setAmount('');
    setCategoryId(categories[0]?.id || '');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (budget) => {
    setEditingBudget(budget);
    setAmount(budget.amount.toString());
    setCategoryId(budget.category_id);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a positive limit amount.');
      return;
    }

    try {
      if (editingBudget) {
        // Edit limit
        const res = await api.put(`/budgets/${editingBudget.id}`, { amount: parseFloat(amount) });
        setBudgets(budgets.map(b => b.id === editingBudget.id ? res.data : b));
        setSuccess('Budget limit updated successfully!');
      } else {
        // Create new
        const res = await api.post('/budgets/', {
          category_id: parseInt(categoryId),
          amount: parseFloat(amount),
          month: selectedMonth
        });
        setBudgets([...budgets, res.data]);
        setSuccess('Budget limit set successfully!');
      }
      setIsModalOpen(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving budget limit.');
    }
  };

  const handleDelete = (budgetId) => {
    setDeleteId(budgetId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`/budgets/${deleteId}`);
      setBudgets(budgets.filter(b => b.id !== deleteId));
      setSuccess('Budget limit deleted successfully!');
    } catch (err) {
      setError('Failed to delete budget.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Monthly Budgets</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Control your expenses by setting custom category budget limits.</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Button onClick={handleOpenCreate} size="sm" className="flex items-center gap-2">
            <Plus size={16} /> Set Budget
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
      ) : budgets.length === 0 ? (
        <Card className="text-center py-12">
          <Sliders className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
          <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-1">No Budgets Set</h3>
          <p className="text-gray-400 dark:text-gray-500 text-sm max-w-sm mx-auto mb-4">
            You haven't set any category budgets for this month. Track smarter by setting constraints.
          </p>
          <Button onClick={handleOpenCreate} variant="secondary" size="sm">
            Configure First Limit
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {budgets.map((bud) => {
            const ratio = bud.amount > 0 ? (bud.spent / bud.amount) * 100 : 0;
            const isOver = bud.spent > bud.amount;
            const isWarning = ratio >= 80 && ratio <= 100;
            
            let colorClass = "bg-indigo-600";
            let textClass = "text-indigo-600 dark:text-indigo-400";
            if (isOver) {
              colorClass = "bg-rose-500";
              textClass = "text-rose-500 dark:text-rose-400";
            } else if (isWarning) {
              colorClass = "bg-amber-500";
              textClass = "text-amber-500 dark:text-amber-400";
            }

            return (
              <Card key={bud.id} className="relative overflow-hidden group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white shadow-sm"
                      style={{ backgroundColor: bud.category?.color || '#6366F1' }}
                    >
                      {bud.category?.name?.charAt(0) || 'B'}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{bud.category?.name || 'Category'}</h4>
                      <p className="text-gray-400 text-xs">Limit Target: ${bud.amount.toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => handleOpenEdit(bud)} 
                      className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 rounded-md"
                      title="Edit Budget"
                    >
                      <Edit3 size={15} />
                    </button>
                    <button 
                      onClick={() => handleDelete(bud.id)} 
                      className="p-1 hover:bg-red-50 dark:hover:bg-red-950/30 text-red-500 rounded-md"
                      title="Delete Budget"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Spent</span>
                    <span className="font-semibold text-gray-800 dark:text-gray-200">
                      ${bud.spent.toLocaleString()} / <span className="text-gray-400">${bud.amount.toLocaleString()}</span>
                    </span>
                  </div>
                  
                  {/* Progress Line */}
                  <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
                      style={{ width: `${Math.min(ratio, 100)}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-400">{ratio.toFixed(0)}% utilized</span>
                    {isOver && <span className="text-rose-500 font-medium">Over limit!</span>}
                    {isWarning && <span className="text-amber-500 font-medium">Approaching limit!</span>}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Set/Edit Budget Modal */}
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
              {editingBudget ? 'Adjust Budget Limit' : 'Configure New Budget'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {!editingBudget && (
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Expense Category</label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  >
                    {categories.length === 0 ? (
                      <option value="">No categories. Set up custom categories first.</option>
                    ) : (
                      categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)
                    )}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Limit Target (USD)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <DollarSign size={16} />
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Budget Period</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <Calendar size={16} />
                  </div>
                  <input
                    type="month"
                    value={selectedMonth}
                    disabled={!!editingBudget}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingBudget ? 'Update Limit' : 'Set Limit'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
      
      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Budget Limit"
        message="Are you sure you want to permanently delete this category budget limit? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default Budgets;
