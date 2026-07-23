import React from 'react';
import { X, Download, Printer, FileText } from 'lucide-react';
import Button from '../Common/Button';

const ReportPreview = ({ digestId, isOpen, onClose, onDownloadPdf }) => {
  if (!isOpen || !digestId) return null;

  const pdfUrl = `/api/v1/digests/${digestId}/download`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl h-[85vh] bg-dark-900 border border-dark-800 rounded-3xl p-6 shadow-2xl flex flex-col space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-dark-800 pb-4">
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText size={18} />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">Bank-Grade PDF Report Preview</h3>
              <p className="text-xs text-dark-400">Official ExpenseFlowAI Executive Financial Digest</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Button variant="primary" onClick={() => onDownloadPdf(digestId)} icon={<Download size={14} />}>
              Download PDF
            </Button>

            <button type="button" onClick={onClose} className="p-2 rounded-xl text-dark-400 hover:text-white hover:bg-dark-850">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Embedded PDF Viewer */}
        <div className="flex-1 bg-dark-950 rounded-2xl overflow-hidden border border-dark-850 relative">
          <iframe
            src={pdfUrl}
            title="PDF Digest Report Preview"
            className="w-full h-full border-none"
          />
        </div>
      </div>
    </div>
  );
};

export default ReportPreview;
