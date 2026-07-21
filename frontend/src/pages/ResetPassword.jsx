import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Lock, CheckCircle2, ArrowLeft, AlertCircle, Eye, EyeOff } from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import api from '../services/api';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setError('Missing reset token. Please use the link from your email.');
    }
  }, [token]);

  const validatePassword = (pw) => {
    if (pw.length < 8) return 'Password must be at least 8 characters long.';
    if (!/[A-Z]/.test(pw)) return 'Password must contain at least one uppercase letter.';
    if (!/[a-z]/.test(pw)) return 'Password must contain at least one lowercase letter.';
    if (!/[0-9\W]/.test(pw)) return 'Password must contain at least one number or special character.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validationError = validatePassword(password);
    if (validationError) {
      setError(validationError);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: password,
      });
      setSuccess(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Failed to reset password. The link may be expired or invalid.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 p-6 relative">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <img src="/branding/logo-dark.png" alt="ExpenseFlow AI" className="h-10 mx-auto mb-4 object-contain" />
          <h2 className="text-2xl font-bold text-dark-50 tracking-tight">Set new password</h2>
          <p className="text-dark-400 text-sm mt-1.5">Choose a strong password for your account</p>
        </div>

        <Card isGlass={true} className="p-8">
          {success ? (
            <div className="text-center py-4 space-y-4">
              <div className="inline-flex w-12 h-12 rounded-full bg-green-500/10 border border-green-500/20 items-center justify-center text-green-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-dark-50">Password updated</h3>
                <p className="text-xs text-dark-450 mt-1.5 leading-relaxed">
                  Your password has been reset successfully. You can now log in with your new password.
                </p>
              </div>
              <Button
                onClick={() => navigate('/login')}
                className="w-full py-2.5 font-semibold mt-2"
              >
                Go to Login
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <span className="text-xs text-red-400">{error}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-10 py-2.5 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-10 py-2.5 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
                  >
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                isLoading={isLoading}
                disabled={!token}
                className="w-full py-2.5 font-semibold mt-2"
              >
                Reset Password
              </Button>
            </form>
          )}

          <div className="mt-6 text-center text-xs">
            <Link to="/login" className="inline-flex items-center gap-1.5 text-brand-400 hover:text-brand-300 font-medium">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Log In
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ResetPassword;
