import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { setAccessToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize and check active sessions
  useEffect(() => {
    const initializeAuth = async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          // Attempt silent refresh on startup to restore session
          const response = await api.post('/auth/refresh', {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = response.data;
          
          setAccessToken(access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          // Get user profiles
          const userResponse = await api.get('/users/me');
          setUser(userResponse.data);
        } catch (error) {
          console.error('Session restoration failed:', error);
          localStorage.removeItem('refresh_token');
          setAccessToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();

    // Listen for global auth expiration events from Axios interceptor
    const handleAuthExpired = () => {
      setUser(null);
    };
    window.addEventListener('auth-expired', handleAuthExpired);
    
    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
    };
  }, []);

  const extractErrorMessage = (error, defaultMsg) => {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map(d => d.msg || JSON.stringify(d)).join('. ');
    }
    return defaultMsg;
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;
      
      setAccessToken(access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      const userResponse = await api.get('/users/me');
      setUser(userResponse.data);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: extractErrorMessage(error, 'Invalid email or password.') 
      };
    } finally {
      setLoading(false);
    }
  };

  const registerUser = async (fullName, email, password) => {
    setLoading(true);
    try {
      await api.post('/auth/register', {
        full_name: fullName,
        email,
        password
      });
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: extractErrorMessage(error, 'Registration failed.') 
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.warn('Logout endpoint call failed:', e);
    } finally {
      localStorage.removeItem('refresh_token');
      setAccessToken(null);
      setUser(null);
    }
  };

  const updateProfileState = (updatedUser) => {
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register: registerUser, logout, updateProfileState }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

