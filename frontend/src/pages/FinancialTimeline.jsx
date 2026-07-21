import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, CreditCard, Target, FileText, RefreshCw, Info, RotateCw } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import { useToast } from '../context/ToastContext';

const FinancialTimeline = () => {
  const { addToast } = useToast();
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTimeline();
  }, []);

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      const res = await api.get('/planning/timeline');
      setTimeline(res.data);
    } catch (err) {
      addToast('Failed to retrieve timeline events.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'transaction_income':
        return <DollarSign className="w-4 h-4 text-green-400" />;
      case 'transaction_expense':
        return <CreditCard className="w-4 h-4 text-red-400" />;
      case 'bill':
        return <FileText className="w-4 h-4 text-amber-400" />;
      case 'goal_milestone':
        return <Target className="w-4 h-4 text-indigo-400" />;
      case 'recurring_event':
        return <RefreshCw className="w-4 h-4 text-brand-450" />;
      default:
        return <Info className="w-4 h-4 text-dark-400" />;
    }
  };

  const getEventBorderColor = (type) => {
    switch (type) {
      case 'transaction_income':
        return 'border-green-500/30 bg-green-500/5';
      case 'transaction_expense':
        return 'border-red-500/30 bg-red-500/5';
      case 'bill':
        return 'border-amber-500/30 bg-amber-500/5';
      case 'goal_milestone':
        return 'border-indigo-500/30 bg-indigo-500/5';
      default:
        return 'border-dark-800 bg-dark-900/40';
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-12 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight flex items-center gap-2">
          <Calendar className="w-8 h-8 text-brand-500" /> Chronological Feed
        </h2>
        <p className="text-xs text-dark-400 mt-1">Review historical transactions merged chronologically with scheduled bills and goal targets.</p>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center text-xs text-dark-400 animate-pulse">
          <RotateCw className="w-5 h-5 animate-spin mr-2 text-brand-500" /> Building Timeline Feed...
        </div>
      ) : timeline.length === 0 ? (
        <Card className="text-center py-16">
          <Calendar className="w-12 h-12 text-dark-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-dark-200">Timeline Feed Empty</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-sm mx-auto leading-relaxed">
            Record checking account balances, transactions, and goals to populate timeline charts.
          </p>
        </Card>
      ) : (
        <div className="relative border-l border-dark-850 ml-4 pl-6 space-y-6">
          {timeline.map((item, idx) => (
            <div key={idx} className="relative group">
              {/* Circle Marker */}
              <span className={`absolute -left-[32px] top-1.5 p-1 rounded-full border border-dark-850 bg-dark-950 transition-transform group-hover:scale-125 z-10 ${getEventBorderColor(item.type)}`}>
                {getEventIcon(item.type)}
              </span>

              <div className="bg-dark-900 border border-dark-850/60 group-hover:border-dark-750 p-4 rounded-2xl transition-all flex justify-between gap-4 items-start hover:-translate-y-0.5">
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-dark-100">{item.title}</span>
                    <span className="text-[9px] bg-dark-950 border border-dark-800 px-2 py-0.5 rounded text-dark-400 font-mono">
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-xs text-dark-400 leading-relaxed">{item.description}</p>
                </div>
                <div className="shrink-0 text-right">
                  <span className={`text-xs font-mono font-extrabold ${
                    item.amount >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {item.amount >= 0 ? '+' : ''}${Math.abs(item.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FinancialTimeline;
