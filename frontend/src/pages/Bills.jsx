import React, { useState, useEffect } from 'react';
import { Plus, Edit3, Trash2, Calendar, DollarSign, X, AlertCircle, CheckCircle2, FileText, Check } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';

const Bills = () => {
  const [bills, setBills] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Filtering
  const [filterPaid, setFilterPaid] = useState('unpaid'); // 'all', 'paid', 'unpaid'

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const [editingBill, setEditingBill] = useState(null);
  const [activeBill, setActiveBill] = useState(null);

  // Confirm Dialog State
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  // Form Fields
  const [name, setName] = useState('');
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState(new Date().toISOString().split('T')[0]);
  const [categoryId, setCategoryId] = useState('');

  // Pay Form Fields
  const [payAccountId, setPayAccountId] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      let url = '/bills/';
      if (filterPaid === 'paid') url += '?is_paid=true';
      if (filterPaid === 'unpaid') url += '?is_paid=false';
      
      const [billsRes, acctsRes, catsRes] = await Promise.all([
        api.get(url),
        api.get('/accounts'),
        api.get('/categories')
      ]);
      setBills(billsRes.data);
      setAccounts(acctsRes.data);
      setCategories(catsRes.data);
    } catch (err) {
      setError('Failed to fetch bills.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterPaid]);

  const handleOpenCreate = () => {
    setEditingBill(null);
    setName('');
    setAmount('');
    setDueDate(new Date().toISOString().split('T')[0]);
    setCategoryId(categories[0]?.id || '');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (bill) => {
    setEditingBill(bill);
    setName(bill.name);
    setAmount(bill.amount.toString());
    setDueDate(bill.due_date.split('T')[0]);
    setCategoryId(bill.category_id || '');
    setIsModalOpen(true);
  };

  const handleOpenPay = (bill) => {
    setActiveBill(bill);
    setPayAccountId(accounts[0]?.id || '');
    setIsPayModalOpen(true);
  };

  const handleBillSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError('Please provide a name.');
      return;
    }
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid bill amount.');
      return;
    }

    const payload = {
      name,
      amount: parseFloat(amount),
      due_date: new Date(dueDate).toISOString(),
      category_id: categoryId ? parseInt(categoryId) : null
    };

    try {
      if (editingBill) {
        await api.put(`/bills/${editingBill.id}`, payload);
        setSuccess('Bill updated successfully!');
      } else {
        await api.post('/bills/', payload);
        setSuccess('Bill registered successfully!');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving bill info.');
    }
  };

  const handlePaySubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!payAccountId) {
      setError('Please choose an account to pay from.');
      return;
    }

    try {
      await api.post(`/bills/${activeBill.id}/pay?account_id=${payAccountId}`);
      setSuccess(`Marked bill "${activeBill.name}" as paid! Ledger transaction recorded.`);
      setIsPayModalOpen(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute payment.');
    }
  };

  const handleDelete = (billId) => {
    setDeleteId(billId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`/bills/${deleteId}`);
      setBills(bills.filter(b => b.id !== deleteId));
      setSuccess('Bill record removed.');
    } catch (err) {
      setError('Failed to delete bill.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Upcoming Bills</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Track fixed expenditures, subscriptions, and dues to avoid late fees.</p>
        </div>
        <Button onClick={handleOpenCreate} size="sm" className="flex items-center gap-2">
          <Plus size={16} /> New Bill
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-800 pb-px">
        {['unpaid', 'paid', 'all'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterPaid(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 capitalize transition-colors ${
              filterPaid === tab 
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400' 
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {tab === 'unpaid' ? 'Pending Dues' : tab === 'paid' ? 'Settled Bills' : 'All Statements'}
          </button>
        ))}
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
      ) : bills.length === 0 ? (
        <Card className="text-center py-12">
          <FileText className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
          <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-1">No Bills Found</h3>
          <p className="text-gray-400 dark:text-gray-500 text-sm max-w-sm mx-auto mb-4">
            You don't have any bills matching this filter. Keep your recurring dues compiled in one place.
          </p>
          {filterPaid === 'unpaid' && (
            <Button onClick={handleOpenCreate} variant="secondary" size="sm">
              Schedule Bill
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bills.map((bill) => {
            const dueDateObj = new Date(bill.due_date);
            const isOverdue = !bill.is_paid && dueDateObj < new Date();
            
            return (
              <Card key={bill.id} className="relative group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-white"
                      style={{ backgroundColor: bill.category?.color || '#9CA3AF' }}
                    >
                      {bill.category?.name?.charAt(0) || 'B'}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{bill.name}</h4>
                      <p className="text-gray-400 text-xs">
                        {bill.category?.name || 'Uncategorized'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {!bill.is_paid && (
                      <button 
                        onClick={() => handleOpenEdit(bill)} 
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 rounded-md"
                      >
                        <Edit3 size={15} />
                      </button>
                    )}
                    <button 
                      onClick={() => handleDelete(bill.id)} 
                      className="p-1 hover:bg-red-50 dark:hover:bg-red-950/30 text-red-500 rounded-md"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-end border-b border-gray-100 dark:border-gray-800 pb-3">
                    <div>
                      <p className="text-xs text-gray-400">Amount Due</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">${bill.amount.toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-400 flex items-center gap-1 justify-end">
                        <Calendar size={12} /> Due Date
                      </p>
                      <p className={`text-sm font-semibold ${isOverdue ? 'text-rose-500' : 'text-gray-700 dark:text-gray-300'}`}>
                        {dueDateObj.toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div>
                      {bill.is_paid ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300">
                          <Check size={12} /> Settle Paid
                        </span>
                      ) : isOverdue ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300">
                          Overdue
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
                          Pending
                        </span>
                      )}
                    </div>
                    {!bill.is_paid && (
                      <Button onClick={() => handleOpenPay(bill)} size="xs" className="flex items-center gap-1">
                        Quick Pay
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Set/Edit Bill Modal */}
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
              {editingBill ? 'Modify Bill Record' : 'Register New Bill'}
            </h2>
            <form onSubmit={handleBillSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Bill Name / Biller</label>
                <input
                  type="text"
                  placeholder="e.g. Electric utility, Rent, Netflix"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Due Amount</label>
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
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Due Date</label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Expense Category (Optional)</label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- No Category --</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingBill ? 'Save Changes' : 'Schedule Bill'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Pay Bill Modal */}
      {isPayModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in">
          <Card className="w-full max-w-md shadow-2xl relative">
            <button 
              onClick={() => setIsPayModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <X size={18} />
            </button>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
              Confirm Bill Payment
            </h2>
            <p className="text-gray-500 text-xs mb-4">
              Pay **${activeBill?.amount.toLocaleString()}** to **{activeBill?.name}**. Choose a funding account.
            </p>
            <form onSubmit={handlePaySubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Pay From Account</label>
                <select
                  value={payAccountId}
                  onChange={(e) => setPayAccountId(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                >
                  <option value="">-- Choose Account --</option>
                  {accounts.map(a => (
                    <option key={a.id} value={a.id}>{a.name} (Bal: ${a.balance.toLocaleString()})</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setIsPayModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  Approve Payment
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
        title="Delete Bill Dues"
        message="Are you sure you want to permanently delete this bill record? This action cannot be undone."
        confirmText="Delete Bill"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default Bills;
