import React from 'react';
import { FileText, Download, Calendar, ShieldCheck, Sparkles, ChevronRight } from 'lucide-react';

const formatFmt = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

const DigestCard = ({ digest, onViewDetails, onDownloadPdf }) => {
  return (
    <div className="p-5 rounded-2xl bg-dark-900 border border-dark-800 hover:border-indigo-500/50 transition-all flex flex-col justify-between space-y-4 shadow-md group">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText size={16} />
            </span>
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              {digest.digest_type} Executive Digest
            </span>
          </div>

          <div className="flex items-center space-x-1.5 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            <ShieldCheck size={12} className="text-emerald-400" />
            <span className="text-[11px] font-extrabold text-emerald-400">Score {digest.health_score}/100</span>
          </div>
        </div>

        <p className="text-xs text-dark-300 line-clamp-3 leading-relaxed">
          {digest.summary}
        </p>

        <div className="flex items-center space-x-3 text-[11px] text-dark-400 pt-1">
          <span className="flex items-center space-x-1">
            <Calendar size={12} />
            <span>{digest.generated_at ? new Date(digest.generated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recent'}</span>
          </span>
          <span>•</span>
          <span className="text-indigo-400 font-semibold">Bank-Grade PDF</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-dark-800">
        <button
          type="button"
          onClick={() => onViewDetails(digest.id)}
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
        >
          <span>Interactive View</span>
          <ChevronRight size={14} />
        </button>

        {digest.has_pdf && (
          <button
            type="button"
            onClick={() => onDownloadPdf(digest.id)}
            className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <Download size={13} />
            <span>Download PDF</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default DigestCard;
