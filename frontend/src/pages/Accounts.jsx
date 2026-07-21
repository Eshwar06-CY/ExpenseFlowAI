import React, { useState, useEffect } from 'react';
import { Landmark, Wallet, CreditCard, Plus, Trash2, Edit3, X, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Accounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);

  // Confirm Dialog State
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  // Form State
  const [name, setName] = useState('');
  const [type, setType] = useState('bank');
  const [balance, setBalance] = useState('0.00');
  const [currency, setCurrency] = useState('USD');

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const res = await api.get('/accounts');
      setAccounts(res.data);
    } catch (err) {
      setError('Failed to fetch accounts. Please check your database connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const openCreateModal = () => {
    setEditingAccount(null);
    setName('');
    setType('bank');
    setBalance('0.00');
    setCurrency('USD');
    setError('');
    setIsModalOpen(true);
  };

  const openEditModal = (account) => {
    setEditingAccount(account);
    setName(account.name);
    setType(account.type);
    setBalance(account.balance.toString());
    setCurrency(account.currency);
    setError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const payload = {
      name,
      type,
      balance: parseFloat(balance),
      currency,
    };

    try {
      if (editingAccount) {
        await api.put(`/accounts/${editingAccount.id}`, payload);
        setSuccess('Account updated successfully.');
      } else {
        await api.post('/accounts/', payload);
        setSuccess('Account created successfully.');
      }
      setIsModalOpen(false);
      fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save account details.');
    }
  };

  const handleDelete = (accountId) => {
    setDeleteId(accountId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    setError('');
    setSuccess('');

    try {
      await api.delete(`/accounts/${deleteId}`);
      setSuccess('Account and its transactions deleted successfully.');
      fetchAccounts();
    } catch (err) {
      setError('Failed to delete account.');
    }
  };

  const getAccountIcon = (acctType) => {
    switch (acctType) {
      case 'bank':
        return <Landmark className="w-5 h-5 text-blue-400" />;
      case 'credit':
        return <CreditCard className="w-5 h-5 text-pink-400" />;
      case 'cash':
      default:
        return <Wallet className="w-5 h-5 text-green-400" />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Top action block */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-dark-50 tracking-tight">Accounts Ledger</h2>
          <p className="text-dark-400 text-sm mt-1">Manage credit lines, bank accounts, and liquid cash vaults.</p>
        </div>
        <Button onClick={openCreateModal} className="flex items-center gap-2 py-2">
          <Plus className="w-4 h-4" /> Add Account
        </Button>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Grid of Accounts */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <Card key={n} className="h-44 animate-pulse flex flex-col justify-between">
              <div className="h-4 bg-dark-850 rounded w-1/3"></div>
              <div className="h-8 bg-dark-850 rounded w-1/2"></div>
              <div className="h-4 bg-dark-850 rounded w-1/4"></div>
            </Card>
          ))}
        </div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-16 rounded-xl bg-dark-900/20 border border-dark-850">
          <Landmark className="w-12 h-12 text-dark-500 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-dark-250">No Accounts Configured</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-md mx-auto leading-relaxed">
            Create a bank, cash wallet, or credit card account to start tracking transactions and ledger flows.
          </p>
          <Button onClick={openCreateModal} variant="secondary" className="mt-4 py-2">
            Create First Account
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {accounts.map((acct) => (
            <Card key={acct.id} className="relative group overflow-hidden hover:border-brand-500/30 transition-all duration-300">
              {/* Corner type tag */}
              <div className="absolute right-4 top-4 p-2.5 rounded-lg bg-dark-950 border border-dark-850">
                {getAccountIcon(acct.type)}
              </div>

              <div className="space-y-4">
                <div>
                  <span className="text-xs text-dark-400 font-semibold uppercase tracking-wider block">
                    {acct.type === 'bank' ? 'Bank Account' : acct.type === 'credit' ? 'Credit Card' : 'Cash Wallet'}
                  </span>
                  <h3 className="text-lg font-bold text-dark-50 mt-1 truncate pr-12">{acct.name}</h3>
                </div>

                <div>
                  <span className="text-xs text-dark-500">Balance</span>
                  <div className="text-2xl font-bold text-dark-100 mt-1">
                    {acct.currency} {acct.balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                </div>

                <div className="flex gap-2 pt-2 border-t border-dark-850">
                  <button
                    onClick={() => openEditModal(acct)}
                    className="flex-1 py-1.5 rounded-lg bg-dark-950 border border-dark-850 text-dark-350 hover:text-dark-150 hover:bg-dark-900 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all"
                  >
                    <Edit3 className="w-3.5 h-3.5" /> Edit
                  </button>
                  <button
                    onClick={() => handleDelete(acct.id)}
                    className="py-1.5 px-3 rounded-lg bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/20 text-red-400 hover:text-red-300 text-xs font-semibold flex items-center justify-center transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Account Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-dark-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-dark-900 border border-dark-800 rounded-xl overflow-hidden shadow-2xl animate-scaleUp">
            <div className="flex justify-between items-center p-5 border-b border-dark-850">
              <h3 className="text-lg font-bold text-dark-50">
                {editingAccount ? 'Edit Account' : 'Create Account'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-dark-400 hover:text-dark-150">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Account Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Chase checking, Wallet Cash"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Account Type</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  >
                    <option value="bank">Bank Account</option>
                    <option value="cash">Cash Wallet</option>
                    <option value="credit">Credit Card</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Currency</label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="CAD">CAD (C$)</option>
                    <option value="INR">INR (₹)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Starting Balance</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={balance}
                  onChange={(e) => setBalance(e.target.value)}
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                />
              </div>

              <div className="pt-4 border-t border-dark-850 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingAccount ? 'Save Changes' : 'Create Account'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Account"
        message="Are you sure you want to delete this account? This will cascade-delete all its associated ledger transactions permanently!"
        confirmText="Delete Account"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default Accounts;
