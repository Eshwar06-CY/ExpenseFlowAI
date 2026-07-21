import React, { useState, useEffect } from 'react';
import { Plus, Search, Trash2, Edit3, Calendar, DollarSign, X, AlertCircle, CheckCircle2, ShoppingBag, ChevronDown, Download, Upload, Filter, ArrowUpDown } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { ICON_GLYPHS } from './Categories';

const Expenses = () => {
  const [expenses, setExpenses] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Selection state
  const [selectedIds, setSelectedIds] = useState([]);

  // Filtering / Search / Sorting State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterAccount, setFilterAccount] = useState('');
  const [minAmount, setMinAmount] = useState('');
  const [maxAmount, setMaxAmount] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Pagination states
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);
  const [totalCount, setTotalCount] = useState(0);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);

  // CSV Import State
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importErrors, setImportErrors] = useState([]);
  const [importing, setImporting] = useState(false);

  // Form Fields
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [accountId, setAccountId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  // Bulk edit category selection
  const [bulkCategory, setBulkCategory] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      setSelectedIds([]);

      // Assemble query params
      const params = new URLSearchParams({
        type: 'expense',
        skip: skip.toString(),
        limit: limit.toString(),
        sort_by: sortBy,
        sort_order: sortOrder
      });

      if (searchQuery) params.append('q', searchQuery);
      if (filterCategory) params.append('category_id', filterCategory);
      if (filterAccount) params.append('account_id', filterAccount);
      if (minAmount) params.append('min_amount', minAmount);
      if (maxAmount) params.append('max_amount', maxAmount);

      const [txRes, acctRes, catRes] = await Promise.all([
        api.get(`/transactions/?${params.toString()}`),
        api.get('/accounts'),
        api.get('/categories')
      ]);

      setExpenses(txRes.data);
      setAccounts(acctRes.data);
      setCategories(catRes.data.filter(c => c.type === 'expense' || c.type === 'both'));

      // Total count from headers
      const countHeader = txRes.headers['x-total-count'];
      if (countHeader) {
        setTotalCount(parseInt(countHeader));
      } else {
        setTotalCount(txRes.data.length);
      }
    } catch (err) {
      setError('Failed to fetch data from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [skip, sortBy, sortOrder, filterCategory, filterAccount, searchQuery]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setSkip(0);
    loadData();
  };

  const handleOpenCreate = () => {
    setEditingExpense(null);
    setAmount('');
    setDescription('');
    setAccountId(accounts[0]?.id || '');
    setCategoryId(categories[0]?.id || '');
    setDate(new Date().toISOString().split('T')[0]);
    setError('');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (exp) => {
    setEditingExpense(exp);
    setAmount(exp.amount.toString());
    setDescription(exp.description || '');
    setAccountId(exp.account_id || '');
    setCategoryId(exp.category_id || '');
    setDate(new Date(exp.date).toISOString().split('T')[0]);
    setError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!accountId) {
      setError('Please configure and select an account to log this expense.');
      return;
    }

    const payload = {
      type: 'expense',
      amount: parseFloat(amount),
      description,
      date: new Date(date).toISOString(),
      account_id: parseInt(accountId),
      category_id: categoryId ? parseInt(categoryId) : null
    };

    try {
      if (editingExpense) {
        await api.put(`/transactions/${editingExpense.id}`, payload);
        setSuccess('Expense transaction updated successfully.');
      } else {
        await api.post('/transactions/', payload);
        setSuccess('Expense transaction created successfully.');
      }
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit transaction.');
    }
  };

  const handleDelete = async (txId) => {
    if (!window.confirm('Are you sure you want to delete this expense transaction? This will restore the account balance.')) return;
    setError('');
    setSuccess('');

    try {
      await api.delete(`/transactions/${txId}`);
      setSuccess('Expense transaction deleted and account balance restored.');
      loadData();
    } catch (err) {
      setError('Failed to delete transaction.');
    }
  };

  // Checkbox functions
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(expenses.map(exp => exp.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (e, expId) => {
    if (e.target.checked) {
      setSelectedIds([...selectedIds, expId]);
    } else {
      setSelectedIds(selectedIds.filter(id => id !== expId));
    }
  };

  // Bulk actions
  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} selected transactions? Balances will be reconciled.`)) return;

    try {
      setError('');
      setSuccess('');
      await api.post('/transactions/bulk-delete', selectedIds);
      setSuccess(`Successfully deleted ${selectedIds.length} transactions and reconciled balances.`);
      setSelectedIds([]);
      loadData();
    } catch (err) {
      setError('Failed to complete bulk delete.');
    }
  };

  const handleBulkCategoryUpdate = async () => {
    if (selectedIds.length === 0 || !bulkCategory) return;
    try {
      setError('');
      setSuccess('');
      const catId = bulkCategory === 'null' ? null : parseInt(bulkCategory);
      await api.post(`/transactions/bulk-update-category?category_id=${catId || ''}`, selectedIds);
      setSuccess(`Successfully updated category tag for ${selectedIds.length} transactions.`);
      setSelectedIds([]);
      setBulkCategory('');
      loadData();
    } catch (err) {
      setError('Failed to update category in bulk.');
    }
  };

  // CSV Import
  const handleImportCSV = async (e) => {
    e.preventDefault();
    if (!importFile) return;

    setImporting(true);
    setImportErrors([]);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('file', importFile);

    try {
      const res = await api.post('/import/csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setSuccess(`CSV Import successful! Loaded ${res.data.imported_count} transactions.`);
      if (res.data.errors?.length > 0) {
        setImportErrors(res.data.errors);
      } else {
        setIsImportModalOpen(false);
      }
      setImportFile(null);
      loadData();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === 'object' && detail.errors) {
        setImportErrors(detail.errors);
      } else {
        setError(detail?.message || 'CSV Import failed. Check headers and content validity.');
      }
    } finally {
      setImporting(false);
    }
  };

  // CSV/Excel Exports
  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams({ type: 'expense' });
      if (searchQuery) params.append('q', searchQuery);
      if (filterCategory) params.append('category_id', filterCategory);
      if (filterAccount) params.append('account_id', filterAccount);
      if (minAmount) params.append('min_amount', minAmount);
      if (maxAmount) params.append('max_amount', maxAmount);

      const endpoint = format === 'excel' ? '/export/excel' : '/export/csv';
      const response = await api.get(`${endpoint}?${params.toString()}`, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], {
        type: format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Expenses_Export_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-dark-50 tracking-tight">Expenses</h2>
          <p className="text-dark-400 text-sm mt-1">Track company cash outflows, bills, and subscription fees.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center gap-1.5 py-2 px-3 text-xs"
          >
            <Upload className="w-3.5 h-3.5" /> Import CSV
          </Button>

          <div className="relative group">
            <Button
              variant="secondary"
              className="flex items-center gap-1.5 py-2 px-3 text-xs"
            >
              <Download className="w-3.5 h-3.5" /> Export <ChevronDown className="w-3 h-3" />
            </Button>
            <div className="absolute right-0 mt-1 w-32 rounded-lg bg-dark-900 border border-dark-800 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="p-1 space-y-0.5">
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full text-left px-3 py-1.5 hover:bg-dark-800 text-xs text-dark-300 rounded-md transition-colors"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => handleExport('excel')}
                  className="w-full text-left px-3 py-1.5 hover:bg-dark-800 text-xs text-dark-300 rounded-md transition-colors"
                >
                  Export Excel
                </button>
              </div>
            </div>
          </div>

          <Button onClick={handleOpenCreate} className="flex items-center gap-2 py-2 text-xs">
            <Plus className="w-4 h-4" /> Log Expense
          </Button>
        </div>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 shrink-0" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-dark-900 border border-dark-850 p-4 rounded-xl space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative w-full md:flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="text"
              placeholder="Search descriptions, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-dark-950 border border-dark-800 rounded-lg pl-10 pr-4 py-2 text-xs text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 transition-all"
            />
          </div>
          
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-xs text-dark-300 outline-none focus:border-brand-500 transition-all w-full sm:w-auto"
            >
              <option value="">All Categories</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            <select
              value={filterAccount}
              onChange={(e) => setFilterAccount(e.target.value)}
              className="bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-xs text-dark-300 outline-none focus:border-brand-500 transition-all w-full sm:w-auto"
            >
              <option value="">All Accounts</option>
              {accounts.map(a => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>

            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="flex items-center gap-1 py-2 px-3 text-xs w-full sm:w-auto justify-center"
            >
              <Filter className="w-3.5 h-3.5" /> More Filters
            </Button>
          </div>
        </form>

        {/* Collapsible Advanced Filters */}
        {showAdvancedFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-dark-800 text-xs text-dark-300 animate-slide-down">
            <div>
              <label className="block font-medium mb-1.5">Min Amount ($)</label>
              <input
                type="number"
                placeholder="0.00"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-dark-250 placeholder-dark-600 outline-none focus:border-brand-500 transition-all"
              />
            </div>
            <div>
              <label className="block font-medium mb-1.5">Max Amount ($)</label>
              <input
                type="number"
                placeholder="9999.00"
                value={maxAmount}
                onChange={(e) => setMaxAmount(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-dark-250 placeholder-dark-600 outline-none focus:border-brand-500 transition-all"
              />
            </div>
            <div>
              <label className="block font-medium mb-1.5">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-dark-250 outline-none focus:border-brand-500 transition-all"
              >
                <option value="date">Transaction Date</option>
                <option value="amount">Amount</option>
                <option value="description">Description</option>
              </select>
            </div>
            <div>
              <label className="block font-medium mb-1.5">Direction</label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-lg px-3 py-2 text-dark-250 outline-none focus:border-brand-500 transition-all"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Bulk Operations Bar */}
      {selectedIds.length > 0 && (
        <div className="bg-brand-950/20 border border-brand-500/20 p-3.5 rounded-xl flex flex-col sm:flex-row justify-between items-center gap-4 text-xs animate-fade-in z-30 relative">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
            <span className="font-bold text-dark-100">{selectedIds.length} transactions selected</span>
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            <div className="flex items-center gap-1.5">
              <select
                value={bulkCategory}
                onChange={(e) => setBulkCategory(e.target.value)}
                className="bg-dark-900 border border-dark-800 rounded-lg px-2.5 py-1.5 text-xs text-dark-300 outline-none focus:border-brand-500 transition-all"
              >
                <option value="">Move to Category...</option>
                <option value="null">Uncategorized</option>
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <Button
                variant="secondary"
                size="xs"
                onClick={handleBulkCategoryUpdate}
                disabled={!bulkCategory}
                className="py-1.5"
              >
                Apply
              </Button>
            </div>

            <div className="h-5 w-[1px] bg-dark-800"></div>

            <Button
              variant="danger"
              size="xs"
              onClick={handleBulkDelete}
              className="flex items-center gap-1 py-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </Button>
          </div>
        </div>
      )}

      {/* Expenses Table */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-dark-900/50 border border-dark-850 h-16 rounded-xl"></div>
          ))}
        </div>
      ) : expenses.length === 0 ? (
        <div className="text-center py-16 rounded-xl bg-dark-900/20 border border-dark-850">
          <ShoppingBag className="w-12 h-12 text-dark-500 mx-auto mb-4 animate-bounce" />
          <h3 className="text-base font-semibold text-dark-250">No Expenses Recorded</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-md mx-auto leading-relaxed">
            Record cash outflows or import CSV tables to see expenses grouped by categories and accounts.
          </p>
        </div>
      ) : (
        <Card className="p-0 overflow-hidden border border-dark-850">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-dark-850 bg-dark-950/50 text-dark-400 font-semibold uppercase tracking-wider select-none">
                  <th className="p-4 w-10 text-center">
                    <input
                      type="checkbox"
                      onChange={handleSelectAll}
                      checked={selectedIds.length === expenses.length && expenses.length > 0}
                      className="rounded border-dark-800 bg-dark-950 text-brand-500 focus:ring-brand-500/20 w-4 h-4 cursor-pointer"
                    />
                  </th>
                  <th className="p-4">Date</th>
                  <th className="p-4">Description</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Account</th>
                  <th className="p-4 text-right">Amount</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-850/60 text-dark-200">
                {expenses.map((exp) => {
                  const isChecked = selectedIds.includes(exp.id);
                  return (
                    <tr 
                      key={exp.id} 
                      className={`hover:bg-dark-900/20 transition-all ${isChecked ? 'bg-brand-600/5 hover:bg-brand-600/10' : ''}`}
                    >
                      <td className="p-4 text-center">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => handleSelectRow(e, exp.id)}
                          className="rounded border-dark-800 bg-dark-950 text-brand-500 focus:ring-brand-500/20 w-4 h-4 cursor-pointer"
                        />
                      </td>
                      <td className="p-4 text-dark-400 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-3.5 h-3.5 text-dark-500" />
                          {new Date(exp.date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="p-4 font-medium text-dark-100 whitespace-nowrap">{exp.description}</td>
                      <td className="p-4 whitespace-nowrap">
                        {exp.category ? (
                          <span 
                            className="px-2 py-1 rounded-full text-[10px] font-semibold tracking-wide border"
                            style={{
                              backgroundColor: `${exp.category.color}15`,
                              borderColor: `${exp.category.color}30`,
                              color: exp.category.color
                            }}
                          >
                            {ICON_GLYPHS[exp.category.icon] || '🏷️'} {exp.category.name}
                          </span>
                        ) : (
                          <span className="text-dark-500 font-italic">Uncategorized</span>
                        )}
                      </td>
                      <td className="p-4 text-dark-300 whitespace-nowrap font-medium">{exp.account?.name || 'Unknown'}</td>
                      <td className="p-4 text-right font-bold text-red-400 whitespace-nowrap">
                        - $ {exp.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="p-4 text-center whitespace-nowrap">
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => handleOpenEdit(exp)}
                            className="p-1.5 rounded hover:bg-dark-800 text-dark-400 hover:text-dark-150 transition-all"
                            title="Edit"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(exp.id)}
                            className="p-1.5 rounded hover:bg-dark-800 text-red-500 hover:text-red-400 transition-all"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          <div className="px-4 py-3.5 bg-dark-950/50 border-t border-dark-850 flex justify-between items-center text-xs select-none">
            <span className="text-dark-400 font-medium">
              Showing {expenses.length} of {totalCount} records
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="xs"
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - limit))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="xs"
                disabled={skip + limit >= totalCount}
                onClick={() => setSkip(skip + limit)}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* CSV Import Modal */}
      {isImportModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-dark-900 border border-dark-800 rounded-3xl w-full max-w-md shadow-2xl p-6 relative">
            <button 
              onClick={() => { setIsImportModalOpen(false); setImportErrors([]); }}
              className="absolute right-4 top-4 p-2 text-dark-500 hover:text-dark-300 rounded-lg hover:bg-dark-800 transition-all"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="text-lg font-bold text-dark-50 mb-2">Import Transactions from CSV</h3>
            <p className="text-xs text-dark-400 mb-4 leading-relaxed">
              CSV file must contain columns: <strong className="text-dark-200">Date</strong>, <strong className="text-dark-200">Type</strong>, <strong className="text-dark-200">Amount</strong>, and <strong className="text-dark-200">Account</strong>. Optional headers: Description, Category.
            </p>

            <form onSubmit={handleImportCSV} className="space-y-4">
              <div className="border border-dashed border-dark-800 rounded-xl p-6 text-center bg-dark-950/50 relative cursor-pointer group hover:border-brand-500/50 transition-all">
                <input
                  type="file"
                  accept=".csv"
                  required
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                />
                <Upload className="w-8 h-8 text-dark-500 mx-auto mb-2 group-hover:text-brand-500 transition-colors" />
                <span className="text-xs font-semibold text-dark-300 block">
                  {importFile ? importFile.name : 'Select or drag & drop CSV file'}
                </span>
                {importFile && (
                  <span className="text-[10px] text-dark-500 mt-1 block">
                    {(importFile.size / 1024).toFixed(1)} KB
                  </span>
                )}
              </div>

              {importErrors.length > 0 && (
                <div className="bg-red-500/5 border border-red-500/10 rounded-xl p-3 max-h-40 overflow-y-auto space-y-1">
                  <span className="text-[10px] font-bold text-red-400 block uppercase tracking-wider">Validation Errors</span>
                  {importErrors.map((err, i) => (
                    <span key={i} className="text-[10px] text-red-300/80 block">• {err}</span>
                  ))}
                </div>
              )}

              <div className="pt-2 border-t border-dark-850 flex justify-end gap-3">
                <Button 
                  type="button" 
                  variant="secondary" 
                  onClick={() => { setIsImportModalOpen(false); setImportErrors([]); }}
                  className="text-xs py-2"
                >
                  Close
                </Button>
                <Button 
                  type="submit" 
                  disabled={!importFile || importing}
                  className="text-xs py-2"
                >
                  {importing ? 'Importing...' : 'Upload & Process'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Log/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-dark-900 border border-dark-800 rounded-3xl w-full max-w-lg shadow-2xl p-6 relative">
            <button 
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 p-2 text-dark-500 hover:text-dark-300 rounded-lg hover:bg-dark-800 transition-all"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="text-lg font-bold text-dark-50 mb-1">
              {editingExpense ? 'Modify Expense Record' : 'Record Company Outflow'}
            </h3>
            <p className="text-xs text-dark-400 mb-6">Reconciles cash outflows against your user account ledger balances.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Description / Vendor</label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. AWS Cloud Hosting Bill"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 transition-all"
                />
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
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Transaction Date</label>
                  <input
                    type="date"
                    required
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Debit From Account</label>
                  <select
                    required
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  >
                    {accounts.length === 0 && (
                      <option value="">No Accounts Found</option>
                    )}
                    {accounts.map((acct) => (
                      <option key={acct.id} value={acct.id}>
                        {acct.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Category Tag</label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                  >
                    <option value="">No Category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-dark-850 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={accounts.length === 0}>
                  {editingExpense ? 'Save Changes' : 'Log Expense'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Expenses;
