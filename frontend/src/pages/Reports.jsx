import React, { useState, useEffect } from 'react';
import { Download, Calendar, FileText, AlertCircle, CheckCircle2, FileSpreadsheet, Table2, Filter, Printer } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';

const Reports = () => {
  const { addToast } = useToast();
  const currentMonthStr = new Date().toISOString().slice(0, 7);
  const [selectedMonth, setSelectedMonth] = useState(currentMonthStr);
  const [downloading, setDownloading] = useState(false);

  // Export filters
  const [exportStartDate, setExportStartDate] = useState('');
  const [exportEndDate, setExportEndDate] = useState('');
  const [exportType, setExportType] = useState('');
  const [exportCategoryId, setExportCategoryId] = useState('');
  const [exportAccountId, setExportAccountId] = useState('');
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const [catRes, accRes] = await Promise.all([
          api.get('/categories'),
          api.get('/accounts'),
        ]);
        setCategories(catRes.data);
        setAccounts(accRes.data);
      } catch (err) {
        // Silently fail — filters are optional
      }
    };
    fetchFilters();
  }, []);

  const handleDownloadPdf = async (e) => {
    e.preventDefault();
    try {
      setDownloading(true);
      const response = await api.get(`/reports/monthly?month=${selectedMonth}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `expenseflow_statement_${selectedMonth}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      addToast('PDF statement downloaded successfully!', 'success');
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const errorObj = JSON.parse(reader.result);
            addToast(errorObj.detail || 'Failed to compile report.', 'error');
          } catch (e) {
            addToast('Failed to compile report.', 'error');
          }
        };
        reader.readAsText(err.response.data);
      } else {
        addToast(err.response?.data?.detail || 'Failed to compile report.', 'error');
      }
    } finally {
      setDownloading(false);
    }
  };

  const buildExportParams = () => {
    const params = new URLSearchParams();
    if (exportStartDate) params.append('start_date', new Date(exportStartDate).toISOString());
    if (exportEndDate) params.append('end_date', new Date(exportEndDate).toISOString());
    if (exportType) params.append('type', exportType);
    if (exportCategoryId) params.append('category_id', exportCategoryId);
    if (exportAccountId) params.append('account_id', exportAccountId);
    return params.toString();
  };

  const handleExportCsv = async () => {
    setExportingCsv(true);
    try {
      const params = buildExportParams();
      const response = await api.get(`/export/csv?${params}`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `expenseflow_export_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      addToast('CSV exported successfully!', 'success');
    } catch (err) {
      addToast('Failed to export CSV.', 'error');
    } finally {
      setExportingCsv(false);
    }
  };

  const handleExportExcel = async () => {
    setExportingExcel(true);
    try {
      const params = buildExportParams();
      const response = await api.get(`/export/excel?${params}`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `expenseflow_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      addToast('Excel exported successfully!', 'success');
    } catch (err) {
      addToast('Failed to export Excel.', 'error');
    } finally {
      setExportingExcel(false);
    }
  };

  const inputClass = "w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all";

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Financial Reports</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Compile statements and export transaction data.</p>
      </div>

      {/* PDF Statement */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
            <FileText size={20} />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white">Monthly PDF Statement</h3>
            <p className="text-gray-400 text-xs">Comprehensive financial summary with accounts, budgets, and category spending.</p>
          </div>
        </div>

        <form onSubmit={handleDownloadPdf} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Select Month</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <Calendar size={16} />
              </div>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
          </div>
          <Button type="submit" disabled={downloading} className="w-full flex items-center justify-center gap-2">
            <Download size={16} />
            {downloading ? 'Compiling PDF...' : 'Download PDF Statement'}
          </Button>
        </form>
      </Card>

      {/* Export Transactions */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <Table2 size={20} />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white">Export Transactions</h3>
            <p className="text-gray-400 text-xs">Download your transactions as CSV or Excel with optional filters.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="space-y-4 mb-6">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase text-dark-400">
            <Filter size={14} /> Filters (Optional)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-dark-500 mb-1">Start Date</label>
              <input type="date" value={exportStartDate} onChange={(e) => setExportStartDate(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="block text-xs text-dark-500 mb-1">End Date</label>
              <input type="date" value={exportEndDate} onChange={(e) => setExportEndDate(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="block text-xs text-dark-500 mb-1">Type</label>
              <select value={exportType} onChange={(e) => setExportType(e.target.value)} className={inputClass}>
                <option value="">All Types</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-dark-500 mb-1">Category</label>
              <select value={exportCategoryId} onChange={(e) => setExportCategoryId(e.target.value)} className={inputClass}>
                <option value="">All Categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-dark-500 mb-1">Account</label>
              <select value={exportAccountId} onChange={(e) => setExportAccountId(e.target.value)} className={inputClass}>
                <option value="">All Accounts</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleExportCsv}
            disabled={exportingCsv}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold hover:bg-emerald-600 hover:text-white transition-all disabled:opacity-50"
          >
            <Table2 size={16} />
            {exportingCsv ? 'Exporting...' : 'Export CSV'}
          </button>
          <button
            onClick={handleExportExcel}
            disabled={exportingExcel}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400 text-sm font-semibold hover:bg-blue-600 hover:text-white transition-all disabled:opacity-50"
          >
            <FileSpreadsheet size={16} />
            {exportingExcel ? 'Exporting...' : 'Export Excel'}
          </button>
          <button
            onClick={() => window.print()}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm font-semibold hover:bg-brand-500 hover:text-white transition-all"
          >
            <Printer size={16} />
            Print Report
          </button>
        </div>
      </Card>
    </div>
  );
};

export default Reports;
