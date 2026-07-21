import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Trash2, Calendar, DollarSign, X, AlertCircle, CheckCircle2, Target, PiggyBank } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Goals = () => {
  const [goals, setGoals] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isContributeOpen, setIsContributeOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [activeGoal, setActiveGoal] = useState(null);

  // Confirm Dialog State
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  // Goal Form Fields
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [currentAmount, setCurrentAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');

  // Contribution Form Fields
  const [contributeAmount, setContributeAmount] = useState('');
  const [contributeAccountId, setContributeAccountId] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [goalRes, acctRes] = await Promise.all([
        api.get('/goals/'),
        api.get('/accounts')
      ]);
      setGoals(goalRes.data);
      setAccounts(acctRes.data);
    } catch (err) {
      setError('Failed to load savings goals.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = () => {
    setEditingGoal(null);
    setName('');
    setTargetAmount('');
    setCurrentAmount('0');
    setTargetDate('');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (goal) => {
    setEditingGoal(goal);
    setName(goal.name);
    setTargetAmount(goal.target_amount.toString());
    setCurrentAmount(goal.current_amount.toString());
    setTargetDate(goal.target_date ? goal.target_date.split('T')[0] : '');
    setIsModalOpen(true);
  };

  const handleOpenContribute = (goal) => {
    setActiveGoal(goal);
    setContributeAmount('');
    setContributeAccountId(accounts[0]?.id || '');
    setIsContributeOpen(true);
  };

  const handleGoalSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError('Please enter a goal name.');
      return;
    }
    if (!targetAmount || parseFloat(targetAmount) <= 0) {
      setError('Please enter a valid target amount.');
      return;
    }

    const payload = {
      name,
      target_amount: parseFloat(targetAmount),
      current_amount: parseFloat(currentAmount || 0),
      target_date: targetDate ? new Date(targetDate).toISOString() : null
    };

    try {
      if (editingGoal) {
        const res = await api.put(`/goals/${editingGoal.id}`, payload);
        setGoals(goals.map(g => g.id === editingGoal.id ? res.data : g));
        setSuccess('Goal updated successfully!');
      } else {
        const res = await api.post('/goals/', payload);
        setGoals([...goals, res.data]);
        setSuccess('Savings goal configured successfully!');
      }
      setIsModalOpen(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving savings goal.');
    }
  };

  const handleContributeSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const amt = parseFloat(contributeAmount);
    if (!amt || amt <= 0) {
      setError('Please enter a positive contribution amount.');
      return;
    }

    try {
      let url = `/goals/${activeGoal.id}/contribute?amount=${amt}`;
      if (contributeAccountId) {
        url += `&account_id=${contributeAccountId}`;
      }
      const res = await api.post(url);
      setGoals(goals.map(g => g.id === activeGoal.id ? res.data : g));
      setSuccess(`Funded $${amt.toLocaleString()} successfully to ${activeGoal.name}!`);
      setIsContributeOpen(false);
      loadData(); // Reload to refresh account balances
    } catch (err) {
      setError(err.response?.data?.detail || 'Error applying goal contribution.');
    }
  };

  const handleDelete = (goalId) => {
    setDeleteId(goalId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`/goals/${deleteId}`);
      setGoals(goals.filter(g => g.id !== deleteId));
      setSuccess('Savings goal deleted successfully!');
    } catch (err) {
      setError('Failed to delete savings goal.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Savings Goals</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Plan for long-term targets by tracking milestones and deposits.</p>
        </div>
        <Button onClick={handleOpenCreate} size="sm" className="flex items-center gap-2">
          <Plus size={16} /> New Goal
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
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : goals.length === 0 ? (
        <Card className="text-center py-12">
          <Target className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
          <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-1">No Active Goals</h3>
          <p className="text-gray-400 dark:text-gray-500 text-sm max-w-sm mx-auto mb-4">
            Create target buckets to track down payments, emergency funds, or leisure plans.
          </p>
          <Button onClick={handleOpenCreate} variant="secondary" size="sm">
            Launch First Goal
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {goals.map((goal) => {
            const pct = goal.target_amount > 0 ? (goal.current_amount / goal.target_amount) * 100 : 0;
            const isCompleted = goal.current_amount >= goal.target_amount;
            
            return (
              <Card key={goal.id} className="relative overflow-hidden group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                      <Target size={20} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        {goal.name}
                        {isCompleted && (
                          <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 rounded-full">
                            Target Hit!
                          </span>
                        )}
                      </h4>
                      {goal.target_date && (
                        <p className="text-gray-400 text-xs flex items-center gap-1 mt-0.5">
                          <Calendar size={12} /> Target Date: {new Date(goal.target_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => handleOpenEdit(goal)} 
                      className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 rounded-md"
                    >
                      <Edit3 size={15} />
                    </button>
                    <button 
                      onClick={() => handleDelete(goal.id)} 
                      className="p-1 hover:bg-red-50 dark:hover:bg-red-950/30 text-red-500 rounded-md"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-gray-500 dark:text-gray-400">Progress</span>
                      <span className="font-semibold text-gray-800 dark:text-gray-200">
                        ${goal.current_amount.toLocaleString()} / <span className="text-gray-400">${goal.target_amount.toLocaleString()}</span>
                      </span>
                    </div>
                    <div className="w-full h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${isCompleted ? 'bg-emerald-500' : 'bg-indigo-600'}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>{pct.toFixed(0)}% completed</span>
                      {goal.target_amount > goal.current_amount && (
                        <span>Need: ${(goal.target_amount - goal.current_amount).toLocaleString()} more</span>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-gray-100 dark:border-gray-800 flex justify-end">
                    <Button 
                      onClick={() => handleOpenContribute(goal)} 
                      size="sm" 
                      variant={isCompleted ? "secondary" : "primary"}
                      className="flex items-center gap-1.5"
                    >
                      <PiggyBank size={14} /> Contribute
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Set/Edit Goal Modal */}
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
              {editingGoal ? 'Edit Savings Goal' : 'Configure New Goal'}
            </h2>
            <form onSubmit={handleGoalSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Goal Name</label>
                <input
                  type="text"
                  placeholder="e.g. New Laptop, Emergency Fund"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Target Target (USD)</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                      <DollarSign size={15} />
                    </div>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={targetAmount}
                      onChange={(e) => setTargetAmount(e.target.value)}
                      className="w-full pl-8 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Starting Savings</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                      <DollarSign size={15} />
                    </div>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={currentAmount}
                      onChange={(e) => setCurrentAmount(e.target.value)}
                      className="w-full pl-8 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Target Date (Optional)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <Calendar size={16} />
                  </div>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingGoal ? 'Save Changes' : 'Initialize Goal'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Contribute Modal */}
      {isContributeOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in">
          <Card className="w-full max-w-md shadow-2xl relative">
            <button 
              onClick={() => setIsContributeOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X size={18} />
            </button>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
              <PiggyBank className="text-indigo-600" /> Contribute to Goal
            </h2>
            <p className="text-gray-500 text-xs mb-4">
              Allocate savings to **{activeGoal?.name}**. Choose an account to debit, or record a contribution.
            </p>
            <form onSubmit={handleContributeSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Contribution Amount (USD)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                    <DollarSign size={16} />
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={contributeAmount}
                    onChange={(e) => setContributeAmount(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Debit From Account (Optional)</label>
                <select
                  value={contributeAccountId}
                  onChange={(e) => setContributeAccountId(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- No Account Debit (Adjust Goal Balance Only) --</option>
                  {accounts.map(a => (
                    <option key={a.id} value={a.id}>{a.name} (Bal: ${a.balance.toLocaleString()})</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsContributeOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  Record Deposit
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
        title="Delete Savings Goal"
        message="Are you sure you want to permanently delete this savings goal? This action cannot be undone."
        confirmText="Delete Goal"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default Goals;
