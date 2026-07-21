import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Load remembered email on mount
  useEffect(() => {
    const savedEmail = localStorage.getItem('remembered_email');
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const res = await login(email, password);
      if (res.success) {
        if (rememberMe) {
          localStorage.setItem('remembered_email', email);
        } else {
          localStorage.removeItem('remembered_email');
        }
        navigate('/dashboard');
      } else {
        setError(res.error || 'Login failed. Please verify credentials.');
      }
    } catch (err) {
      setError('An unexpected system error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 p-6 relative">
      {/* Background glow graphics */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <div className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-500 items-center justify-center font-bold text-xl text-white shadow-lg shadow-brand-500/20 mb-4">
            E
          </div>
          <h2 className="text-2xl font-bold text-dark-50 tracking-tight">Welcome back</h2>
          <p className="text-dark-400 text-sm mt-1.5">Enter details to manage your workspace</p>
        </div>

        <Card isGlass={true} className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                {error}
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

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider">Password</label>
                <Link to="/forgot-password" className="text-xs text-brand-400 hover:text-brand-300">Forgot?</Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-10 py-2.5 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300 focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
                </button>
              </div>
            </div>

            {/* Remember Me Toggle */}
            <div className="flex items-center">
              <label className="flex items-center gap-2 text-xs text-dark-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-dark-850 bg-dark-950 text-brand-600 focus:ring-brand-500 focus:ring-offset-dark-950 w-4 h-4"
                />
                Remember Me
              </label>
            </div>

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full py-2.5 font-semibold mt-2"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 text-center text-xs text-dark-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
              Create an account
            </Link>
          </div>
        </Card>

        <div className="flex items-center justify-center gap-2 mt-8 text-xs text-dark-500">
          <ShieldCheck className="w-4 h-4" />
          <span>Secured with standard JWT & BCrypt hashing</span>
        </div>
      </div>
    </div>
  );
};

export default Login;
