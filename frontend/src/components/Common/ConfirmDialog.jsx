import React, { useEffect, useRef } from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';
import Button from './Button';

const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default', // 'default' | 'danger'
}) => {
  const dialogRef = useRef(null);
  const confirmBtnRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => confirmBtnRef.current?.focus(), 100);

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') onClose();
        if (e.key === 'Tab' && dialogRef.current) {
          const focusable = dialogRef.current.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last?.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first?.focus();
          }
        }
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isDanger = variant === 'danger';

  return (
    <div className="fixed inset-0 z-[9998] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/75 backdrop-blur-md confirm-backdrop-enter"
        onClick={onClose}
      />
      {/* Dialog box with EDL depth and shadows */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="relative z-10 w-full max-w-md bg-dark-900 border border-dark-800 rounded-3xl shadow-edl-depth confirm-dialog-enter overflow-hidden"
      >
        {/* Visual Light Spill Background */}
        <div className={`absolute -top-12 -left-12 w-32 h-32 rounded-full blur-3xl opacity-20 pointer-events-none ${
          isDanger ? 'bg-red-500' : 'bg-brand-500'
        }`} />
        
        <div className="p-7 relative z-10">
          <div className="flex justify-between items-start mb-4">
            {/* Icon Container */}
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isDanger 
                ? 'bg-red-500/10 border border-red-500/20' 
                : 'bg-amber-500/10 border border-amber-500/20'
            }`}>
              {isDanger ? (
                <Trash2 className="w-5 h-5 text-red-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              )}
            </div>
            
            <button 
              onClick={onClose} 
              className="text-dark-400 hover:text-white p-1 rounded-lg hover:bg-dark-800 transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <h3 id="confirm-title" className="text-lg font-bold text-dark-50 mb-2 font-sans tracking-tight">{title}</h3>
          <p className="text-sm text-dark-400 leading-relaxed font-sans">{message}</p>
        </div>

        {/* Action button dock */}
        <div className="flex items-center gap-3 px-6 py-4 bg-dark-950/60 border-t border-dark-850 relative z-10">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 rounded-xl border border-dark-800 text-sm font-semibold text-dark-300 hover:bg-dark-800 hover:text-white transition-all active:scale-95 duration-200"
          >
            {cancelText}
          </button>
          <button
            ref={confirmBtnRef}
            onClick={() => { onConfirm(); onClose(); }}
            className={`flex-1 px-4 py-3 rounded-xl text-sm font-bold text-white transition-all active:scale-95 duration-200 shadow-md ${
              isDanger
                ? 'bg-gradient-to-r from-red-600 to-rose-500 hover:shadow-red-500/20'
                : 'bg-gradient-to-r from-brand-600 to-indigo-500 hover:shadow-brand-500/20'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
