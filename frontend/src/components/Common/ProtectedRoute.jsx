import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex flex-col items-center justify-center">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-brand-500/20 mb-4 animate-bounce">
          E
        </div>
        <div className="flex items-center gap-1.5 text-xs text-brand-400 font-semibold tracking-wider uppercase animate-pulse">
          Loading Workspace...
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
