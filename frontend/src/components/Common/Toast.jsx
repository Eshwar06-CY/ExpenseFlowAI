import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const iconMap = {
  success: CheckCircle2,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const colorMap = {
  success: {
    bg: 'bg-emerald-500/10 border-emerald-500/20',
    icon: 'text-emerald-400',
    text: 'text-emerald-100',
    progress: 'bg-emerald-400',
  },
  error: {
    bg: 'bg-red-500/10 border-red-500/20',
    icon: 'text-red-400',
    text: 'text-red-100',
    progress: 'bg-red-400',
  },
  warning: {
    bg: 'bg-amber-500/10 border-amber-500/20',
    icon: 'text-amber-400',
    text: 'text-amber-100',
    progress: 'bg-amber-400',
  },
  info: {
    bg: 'bg-blue-500/10 border-blue-500/20',
    icon: 'text-blue-400',
    text: 'text-blue-100',
    progress: 'bg-blue-400',
  },
};

const ToastItem = ({ toast, onRemove }) => {
  const [exiting, setExiting] = useState(false);
  const [progress, setProgress] = useState(100);
  const colors = colorMap[toast.type] || colorMap.info;
  const Icon = iconMap[toast.type] || Info;

  useEffect(() => {
    const startTime = Date.now();
    const duration = toast.duration || 4000;

    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) clearInterval(progressInterval);
    }, 50);

    const timer = setTimeout(() => {
      setExiting(true);
      setTimeout(() => onRemove(toast.id), 300);
    }, duration);

    return () => {
      clearTimeout(timer);
      clearInterval(progressInterval);
    };
  }, [toast, onRemove]);

  const handleClose = () => {
    setExiting(true);
    setTimeout(() => onRemove(toast.id), 300);
  };

  return (
    <div
      className={`relative flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-2xl shadow-black/20 min-w-[320px] max-w-[420px] overflow-hidden transition-all duration-300 ${colors.bg} ${
        exiting ? 'toast-exit' : 'toast-enter'
      }`}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${colors.icon}`} />
      <p className={`text-sm font-medium flex-1 ${colors.text}`}>{toast.message}</p>
      <button
        onClick={handleClose}
        className="text-dark-400 hover:text-dark-100 transition-colors flex-shrink-0 mt-0.5"
      >
        <X className="w-4 h-4" />
      </button>
      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/5">
        <div
          className={`h-full ${colors.progress} transition-all duration-100 ease-linear`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

const Toast = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2.5 pointer-events-auto">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
};

export default Toast;
