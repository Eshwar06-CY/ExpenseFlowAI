import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import Button from './Button';

const OfflineBanner = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="fixed bottom-20 md:bottom-6 right-6 z-[9999] bg-amber-500/10 border border-amber-500/20 backdrop-blur-xl p-4 rounded-2xl shadow-2xl shadow-black/40 flex items-center gap-3 max-w-sm animate-fade-in">
      <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl">
        <WifiOff className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="text-xs font-bold text-dark-100">You are currently offline</h4>
        <p className="text-[10px] text-dark-400 mt-0.5">Please check your network settings.</p>
      </div>
      <Button
        variant="secondary"
        size="xs"
        onClick={() => window.location.reload()}
        className="flex items-center gap-1 shrink-0 font-bold"
      >
        <RefreshCw className="w-3 h-3" /> Retry
      </Button>
    </div>
  );
};

export default OfflineBanner;
