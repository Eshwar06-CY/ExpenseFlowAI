import React, { useState, useEffect } from 'react';
import {
  FileText, Download, Sparkles, RefreshCw, Calendar, Eye, History, Plus
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import DigestViewer from '../components/Digest/DigestViewer';
import DigestHistory from '../components/Digest/DigestHistory';
import ReportPreview from '../components/Digest/ReportPreview';
import { useToast } from '../context/ToastContext';

const DigestPage = () => {
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState('latest'); // 'latest' | 'history'
  const [selectedType, setSelectedType] = useState('monthly');
  const [latestDigest, setLatestDigest] = useState(null);
  const [activeDigest, setActiveDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // PDF Preview State
  const [previewId, setPreviewId] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const fetchLatestDigest = async () => {
    try {
      setLoading(true);
      const res = await api.get('/digests/latest');
      setLatestDigest(res.data);
      setActiveDigest(res.data);
    } catch (err) {
      console.warn('Failed to fetch latest digest:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestDigest();
  }, []);

  const handleGenerateDigest = async (typeToGen = selectedType) => {
    try {
      setGenerating(true);
      const res = await api.post('/digests/generate', { digest_type: typeToGen });
      setLatestDigest(res.data);
      setActiveDigest(res.data);
      setActiveTab('latest');
      addToast(`${typeToGen.toUpperCase()} Financial Digest generated successfully!`, 'success');
    } catch (err) {
      addToast('Failed to generate financial digest.', 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleFetchSpecificDigest = async (digestId) => {
    try {
      setLoading(true);
      const res = await api.get(`/digests/${digestId}`);
      setActiveDigest(res.data);
      setActiveTab('latest');
    } catch (err) {
      addToast('Failed to fetch digest details.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = (digestId) => {
    window.open(`/api/v1/digests/${digestId}/download`, '_blank');
  };

  return (
    <div className="space-y-8 pb-16 animate-in fade-in duration-300 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText size={20} />
            </span>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Financial Digest & Reports</h1>
          </div>
          <p className="text-xs text-dark-400 mt-1">
            Automated executive digests, interactive performance summaries, and downloadable bank-grade PDF reports.
          </p>
        </div>

        {/* Period Selector & On-Demand Generator */}
        <div className="flex items-center space-x-3 flex-wrap gap-y-2">
          <div className="flex items-center bg-dark-900 border border-dark-800 rounded-xl p-1">
            {['daily', 'weekly', 'monthly', 'yearly'].map((period) => (
              <button
                key={period}
                type="button"
                onClick={() => {
                  setSelectedType(period);
                  handleGenerateDigest(period);
                }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  selectedType === period
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-dark-400 hover:text-white'
                }`}
              >
                {period}
              </button>
            ))}
          </div>

          <Button
            variant="primary"
            onClick={() => handleGenerateDigest(selectedType)}
            loading={generating}
            icon={<Sparkles size={14} />}
          >
            Generate New Report
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-3 border-b border-dark-800 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('latest')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'latest'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-dark-900 text-dark-400 hover:text-white border border-dark-800'
          }`}
        >
          <Eye size={14} />
          <span>Interactive Digest View</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'history'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-dark-900 text-dark-400 hover:text-white border border-dark-800'
          }`}
        >
          <History size={14} />
          <span>Report Archive & History</span>
        </button>
      </div>

      {/* Content Body */}
      {activeTab === 'latest' ? (
        loading ? (
          <div className="py-16 text-center text-xs text-dark-400 animate-pulse">Loading financial digest...</div>
        ) : (
          <DigestViewer digestData={activeDigest} onDownloadPdf={handleDownloadPdf} />
        )
      ) : (
        <DigestHistory
          onViewDetails={handleFetchSpecificDigest}
          onDownloadPdf={handleDownloadPdf}
        />
      )}

      {/* PDF Report Modal Preview */}
      <ReportPreview
        digestId={previewId}
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        onDownloadPdf={handleDownloadPdf}
      />
    </div>
  );
};

export default DigestPage;
