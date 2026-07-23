import React, { useState, useEffect } from 'react';
import { X, Sparkles, Database, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import api from '../../services/api';
import ConfidenceMeter from './ConfidenceMeter';
import DataSourceChip from './DataSourceChip';
import { ReasonCard, AssumptionCard, LimitationCard } from './ReasonCard';

const fmtVal = (val) => {
  if (typeof val === 'number') {
    if (val > 100) return `₹${val.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    return `${val}`;
  }
  return String(val);
};

const ExplanationPanel = ({ feature, targetId, isOpen, onClose }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchExplanation = async () => {
      if (!isOpen || !feature || !targetId) return;
      try {
        setLoading(true);
        const res = await api.get(`/explanations/${feature}/${targetId}`);
        setExplanation(res.data.explanation);
      } catch (err) {
        console.warn('Failed to fetch AI explanation:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchExplanation();
  }, [isOpen, feature, targetId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-dark-900 border border-dark-800 rounded-3xl p-6 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-dark-800 pb-4">
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles size={18} />
            </span>
            <div>
              <h3 className="text-base font-bold text-white uppercase tracking-wider">
                Explainable AI (XAI) Insight
              </h3>
              <p className="text-xs text-dark-400">
                Transparent breakdown for {feature} • {targetId}
              </p>
            </div>
          </div>

          <button type="button" onClick={onClose} className="p-2 rounded-xl text-dark-400 hover:text-white hover:bg-dark-850">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-dark-400 animate-pulse">
            Generating transparent XAI breakdown from FinanceEngine...
          </div>
        ) : explanation ? (
          <div className="space-y-5">
            {/* Reason */}
            <ReasonCard reason={explanation.reason} />

            {/* Confidence Meter */}
            <ConfidenceMeter confidence={explanation.confidence} />

            {/* Data Sources Used */}
            <div className="space-y-2">
              <p className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
                <Database size={13} className="text-indigo-400" />
                <span>Verified Data Sources Used</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {(explanation.data_used || []).map((ds, idx) => (
                  <DataSourceChip key={idx} label={ds} />
                ))}
              </div>
            </div>

            {/* FinanceEngine Metrics */}
            {explanation.finance_engine_metrics && (
              <div className="space-y-2">
                <p className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
                  <Activity size={13} className="text-emerald-400" />
                  <span>FinanceEngine Mathematical Output</span>
                </p>
                <div className="grid grid-cols-2 gap-2 p-3 rounded-2xl bg-dark-950 border border-dark-850 text-xs">
                  {Object.entries(explanation.finance_engine_metrics).map(([k, v]) => (
                    <div key={k} className="flex flex-col">
                      <span className="text-[10px] text-dark-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-white">{fmtVal(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Assumptions & Limitations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AssumptionCard assumptions={explanation.assumptions} />
              <LimitationCard limitations={explanation.limitations} />
            </div>

            {/* Suggested Actions */}
            {explanation.suggested_actions && explanation.suggested_actions.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-dark-800">
                <p className="text-xs font-bold text-white">Recommended Next Actions</p>
                <div className="space-y-1.5">
                  {explanation.suggested_actions.map((act, idx) => (
                    <div key={idx} className="p-2.5 rounded-xl bg-dark-950 border border-dark-850 text-xs text-indigo-300 flex items-center justify-between">
                      <span>{act}</span>
                      <ArrowRight size={12} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default ExplanationPanel;
