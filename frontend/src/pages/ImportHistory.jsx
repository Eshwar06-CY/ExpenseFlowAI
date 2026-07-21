import React, { useState, useEffect } from 'react';
import { RefreshCw, RotateCcw, AlertTriangle, CheckCircle, FileText, ArrowLeft } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';
import { useNavigate } from 'react-router-dom';

const ImportHistory = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.get('/import/history');
      setHistory(res.data);
    } catch (err) {
      addToast('Failed to load statement import logs.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (id, filename) => {
    if (!window.confirm(`WARNING: Are you sure you want to rollback all transactions imported from "${filename}"? This will reverse their bank account balance reconciliations permanently.`)) {
      return;
    }
    
    try {
      setLoading(true);
      await api.post(`/import/history/${id}/rollback`);
      addToast('Import batch rolled back successfully.', 'success');
      fetchHistory();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to rollback import.', 'error');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight flex items-center gap-2">
            <RotateCcw className="w-8 h-8 text-brand-500" /> Statement Import History
          </h2>
          <p className="text-xs text-dark-400 mt-1">Audit and rollback previous spreadsheet statement imports.</p>
        </div>
        <Button variant="secondary" onClick={() => navigate('/dashboard/import-wizard')} className="text-xs py-2">
          New Statement Import
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map(n => (
            <div key={n} className="h-20 bg-dark-900 border border-dark-850 rounded-2xl"></div>
          ))}
        </div>
      ) : history.length === 0 ? (
        <Card className="text-center py-16">
          <FileText className="w-12 h-12 text-dark-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-dark-200">No Statement Import History</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-sm mx-auto leading-relaxed">
            You haven't uploaded any bank statements yet. Visit the import wizard to begin.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {history.map((job) => {
            const isRolledBack = job.status === 'rolled_back';
            return (
              <div
                key={job.id}
                className={`p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  isRolledBack
                    ? 'bg-red-500/5 border-red-500/10 opacity-70'
                    : 'bg-dark-900 border-dark-850 hover:border-dark-800'
                }`}
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2.5">
                    <span className="text-sm font-bold text-dark-100 truncate">{job.filename}</span>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                      isRolledBack
                        ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                        : 'bg-green-500/10 text-green-450 border border-green-500/20'
                    }`}>
                      {isRolledBack ? 'Rolled Back' : 'Completed'}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-dark-400 font-mono">
                    <span>Uploaded: {new Date(job.date).toLocaleString()}</span>
                    <span>•</span>
                    <span className="text-green-400">Imported: {job.rows_imported} rows</span>
                    <span>•</span>
                    <span className="text-amber-500">Skipped: {job.rows_skipped} rows</span>
                    <span>•</span>
                    <span className="text-red-500">Failed: {job.rows_failed} rows</span>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  {!isRolledBack && (
                    <Button
                      variant="secondary"
                      size="xs"
                      onClick={() => handleRollback(job.id, job.filename)}
                      className="flex items-center gap-1.5 py-1.5 px-3 border-red-500/20 text-red-400 hover:text-white hover:!bg-red-600 hover:border-red-600 transition-all font-semibold"
                    >
                      <RotateCcw className="w-3.5 h-3.5" /> Rollback Import
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ImportHistory;
