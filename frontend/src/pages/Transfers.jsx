import React, { useState, useEffect } from 'react';
import { ArrowRight, Plus, Trash2, Calendar, DollarSign, RefreshCw, X, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Transfers = () => {
  const [transfers, setTransfers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [sourceAccountId, setSourceAccountId] = useState('');
  const [destAccountId, setDestAccountId] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Fetch accounts and transfers
      const [acctRes, txRes] = await Promise.all([
        api.get('/accounts'),
        api.get('/transactions?type=transfer'),
      ]);
      setAccounts(acctRes.data);
      setTransfers(txRes.data);
    } catch (err) {
      setError('Failed to load accounts and transfer ledger.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openModal = () => {
    setSourceAccountId(accounts[0]?.id || '');
    setDestAccountId(accounts[1]?.id || '');
    setAmount('');
    setDescription('');
    setDate(new Date().toISOString().split('T')[0]);
    setError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!sourceAccountId || !destAccountId) {
      setError('Please select both source and destination accounts.');
      return;
    }

    if (sourceAccountId === destAccountId) {
      setError('Source and destination accounts must be different.');
      return;
    }

    const payload = {
      type: 'transfer',
      amount: parseFloat(amount),
      description: description || 'Account Transfer',
      date: new Date(date).toISOString(),
      account_id: parseInt(sourceAccountId),
      to_account_id: parseInt(destAccountId),
    };

    try {
      await api.post('/transactions/', payload);
      setSuccess('Fund transfer executed successfully.');
      setIsModalOpen(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute transfer.');
    }
  };

  const handleDelete = async (txId) => {
    if (!window.confirm('Are you sure you want to delete this transfer? This will revert the balances in both accounts!')) return;
    setError('');
    setSuccess('');

    try {
      await api.delete(`/transactions/${txId}`);
      setSuccess('Transfer deleted and balances reverted successfully.');
      fetchData();
    } catch (err) {
      setError('Failed to revert transaction.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Top action block */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-dark-50 tracking-tight">Internal Transfers</h2>
          <p className="text-dark-400 text-sm mt-1">Transfer assets between liquidity lines and bank vaults.</p>
        </div>
        <Button onClick={openModal} className="flex items-center gap-2 py-2" disabled={accounts.length < 2}>
          <Plus className="w-4 h-4" /> New Transfer
        </Button>
      </div>

      {accounts.length < 2 && !loading && (
        <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <h4 className="font-semibold text-yellow-300">Multiple Accounts Required</h4>
            <p className="mt-1 leading-relaxed text-yellow-400/80">
              You must have at least two accounts configured to execute transfers. 
              Go to the Accounts page to set up Cash or Card accounts first.
            </p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Transfers Ledger Table */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-dark-900/50 border border-dark-850 h-16 rounded-xl"></div>
          ))}
        </div>
      ) : transfers.length === 0 ? (
        <div className="text-center py-16 rounded-xl bg-dark-900/20 border border-dark-850">
          <RefreshCw className="w-12 h-12 text-dark-500 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-dark-250">No Transfers Logged</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-md mx-auto leading-relaxed">
            Execute a new transfer to move funds between bank lines, credit systems, and cash wallets.
          </p>
        </div>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-dark-850 bg-dark-950/50 text-dark-400 font-semibold uppercase tracking-wider">
                  <th className="p-4">Date</th>
                  <th className="p-4">Transfer Route</th>
                  <th className="p-4">Description</th>
                  <th className="p-4 text-right">Amount</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-850/60">
                {transfers.map((tx) => (
                  <tr key={tx.id} className="hover:bg-dark-900/20 transition-all">
                    <td className="p-4 text-dark-300 font-medium">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-dark-500" />
                        {new Date(tx.date).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-dark-200">
                        <span className="font-bold text-dark-100">{tx.account?.name || 'Unknown'}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                        <span className="font-bold text-brand-350">{tx.to_account?.name || 'Unknown'}</span>
                      </div>
                    </td>
                    <td className="p-4 text-dark-405 italic">{tx.description}</td>
                    <td className="p-4 text-right font-semibold text-dark-50">
                      $ {tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => handleDelete(tx.id)}
                        className="p-1.5 rounded bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/20 text-red-400 transition-all"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Transfer modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-dark-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-dark-900 border border-dark-800 rounded-xl overflow-hidden shadow-2xl animate-scaleUp">
            <div className="flex justify-between items-center p-5 border-b border-dark-850">
              <h3 className="text-lg font-bold text-dark-50">Execute Internal Transfer</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-dark-400 hover:text-dark-150">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">From Account (Source)</label>
                <select
                  required
                  value={sourceAccountId}
                  onChange={(e) => setSourceAccountId(e.target.value)}
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                >
                  {accounts.map((acct) => (
                    <option key={acct.id} value={acct.id}>
                      {acct.name} (${acct.balance.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">To Account (Destination)</label>
                <select
                  required
                  value={destAccountId}
                  onChange={(e) => setDestAccountId(e.target.value)}
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                >
                  {accounts.map((acct) => (
                    <option key={acct.id} value={acct.id}>
                      {acct.name} (${acct.balance.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Amount ($)</label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="0.00"
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-9 pr-4 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Date</label>
                  <input
                    type="date"
                    required
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Description / Memo</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Checking to Savings reserve"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 transition-all"
                />
              </div>

              <div className="pt-4 border-t border-dark-850 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  Execute Transfer
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transfers;
