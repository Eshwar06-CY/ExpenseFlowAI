import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import Button from '../components/Common/Button';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 p-6 relative">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl"></div>
      
      <div className="text-center z-10 space-y-6">
        <div className="inline-flex p-4 bg-brand-600/10 border border-brand-500/20 text-brand-400 rounded-2xl mb-2 animate-bounce">
          <AlertCircle className="w-12 h-12" />
        </div>
        
        <h1 className="text-6xl font-extrabold text-dark-50 font-sans tracking-tight">404</h1>
        <div>
          <h2 className="text-xl font-bold text-dark-100">Page not found</h2>
          <p className="text-dark-400 text-sm mt-2 max-w-sm mx-auto leading-relaxed">
            The page you are looking for doesn't exist or has been moved to another path.
          </p>
        </div>
        
        <Button
          variant="primary"
          onClick={() => navigate('/')}
          className="px-6 font-semibold"
        >
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};

export default NotFound;
