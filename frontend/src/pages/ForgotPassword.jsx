import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, CheckCircle2, ArrowLeft, AlertCircle } from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import api from '../services/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await api.post('/auth/forgot-password', { email });
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
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
          <h2 className="text-2xl font-bold text-dark-50 tracking-tight">Reset password</h2>
          <p className="text-dark-400 text-sm mt-1.5">Recover access to your fintech ledger workspace</p>
        </div>

        <Card isGlass={true} className="p-8">
          {!submitted ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <span className="text-xs text-red-400">{error}</span>
                </div>
              )}
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                  />
                </div>
              </div>

              <Button
                type="submit"
                isLoading={isLoading}
                className="w-full py-2.5 font-semibold mt-2"
              >
                Send Reset Link
              </Button>
            </form>
          ) : (
            <div className="text-center py-4 space-y-4">
              <div className="inline-flex w-12 h-12 rounded-full bg-green-500/10 border border-green-500/20 items-center justify-center text-green-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-dark-50">Check your inbox</h3>
                <p className="text-xs text-dark-450 mt-1.5 leading-relaxed">
                  We sent a recovery email to <strong className="text-dark-200">{email}</strong>. Follow the instructions to reset your password.
                </p>
              </div>
            </div>
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

export default ForgotPassword;
