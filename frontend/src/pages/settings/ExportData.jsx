import React, { useState } from 'react';
import { Download, FileJson, ShieldCheck, CheckCircle2 } from 'lucide-react';
import api from '../../services/api';

const ExportData = ({ addToast }) => {
  const [exporting, setExporting] = useState(false);
  const [lastExported, setLastExported] = useState(null);

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await api.get('/personalization/export');
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(res.data, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `ExpenseFlowAI_Data_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();

      setLastExported(new Date().toLocaleTimeString());
      if (addToast) addToast('AI Personalization data exported successfully!', 'success');
    } catch (err) {
      if (addToast) addToast(err.response?.data?.detail || 'Failed to export AI data.', 'error');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700/60 shadow-sm">
        <div className="flex items-start space-x-4 mb-6">
          <div className="p-3 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
            <FileJson size={24} />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white">Export Complete AI Personalization Data</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-xl leading-relaxed">
              Download a complete, structured JSON archive containing your AI preferences, learned financial behaviors, persistent memories, and interaction telemetry statistics.
            </p>
          </div>
        </div>

        {/* Data Package Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {[
            { title: 'AI Settings & Preferences', desc: 'Coaching style, response detail & privacy toggles' },
            { title: 'Learned Behavior Cards', desc: 'Category observations and confidence ratings' },
            { title: 'Persistent AI Memories', desc: 'Stored financial preferences and goals' },
            { title: 'Telemetry & Statistics', desc: 'Interaction counts & compliance metrics' }
          ].map((item, idx) => (
            <div key={idx} className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-800 flex items-start space-x-2.5">
              <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-gray-900 dark:text-white">{item.title}</h4>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
            <ShieldCheck size={16} className="text-emerald-500" />
            <span>Sanitized JSON • 100% Client-side download</span>
          </div>

          <button
            type="button"
            onClick={handleExportData}
            disabled={exporting}
            className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            <Download size={15} className="mr-2" />
            {exporting ? 'Generating JSON Package...' : 'Download AI Data (JSON)'}
          </button>
        </div>

        {lastExported && (
          <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium text-right mt-2">
            Last exported today at {lastExported}
          </p>
        )}
      </div>
    </div>
  );
};

export default ExportData;
