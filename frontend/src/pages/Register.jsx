import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, label: 'Weak', color: 'bg-red-500' });
  
  const { register } = useAuth();
  const navigate = useNavigate();

  // Password strength calculation
  useEffect(() => {
    if (!password) {
      setPasswordStrength({ score: 0, label: 'Weak', color: 'bg-red-500' });
      return;
    }

    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[0-9\W]/.test(password)) score += 1;

    let label = 'Weak';
    let color = 'bg-red-500';

    if (score === 2 || score === 3) {
      label = 'Fair';
      color = 'bg-yellow-500';
    } else if (score === 4) {
      label = 'Strong';
      color = 'bg-green-500';
    }

    setPasswordStrength({ score, label, color });
  }, [password]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!acceptTerms) {
      setError('You must accept the terms and conditions.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await register(name, email, password);
      if (res.success) {
        navigate('/login', { state: { registered: true } });
      } else {
        setError(res.error || 'Registration failed.');
      }
    } catch (err) {
      setError('An unexpected system error occurred.');
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
          <h2 className="text-2xl font-bold text-dark-50 tracking-tight">Create your account</h2>
          <p className="text-dark-400 text-sm mt-1.5">Start tracking smarter and saving better today</p>
        </div>

        <Card isGlass={true} className="p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-1.5">Full Name</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                />
              </div>
              
              {/* Password strength UI */}
              {password && (
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-dark-450 font-medium">Password Strength:</span>
                    <span className={`font-semibold ${
                      passwordStrength.label === 'Strong' ? 'text-green-400' : 
                      passwordStrength.label === 'Fair' ? 'text-yellow-400' : 'text-red-400'
                    }`}>{passwordStrength.label}</span>
                  </div>
                  <div className="w-full bg-dark-900 h-1.5 rounded-full overflow-hidden border border-dark-850">
                    <div 
                      className={`h-full ${passwordStrength.color} transition-all duration-300`} 
                      style={{ width: `${(passwordStrength.score / 4) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
                />
              </div>
            </div>

            {/* Terms of Service check */}
            <div className="flex items-start mt-2">
              <label className="flex items-start gap-2 text-xs text-dark-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  className="rounded border-dark-850 bg-dark-950 text-brand-600 focus:ring-brand-500 focus:ring-offset-dark-950 w-4 h-4 mt-0.5"
                />
                <span>I accept the <a href="#" className="text-brand-400 hover:text-brand-350">Terms of Service</a> and <a href="#" className="text-brand-400 hover:text-brand-350">Privacy Policy</a></span>
              </label>
            </div>

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full py-2.5 font-semibold mt-4"
            >
              Sign Up
            </Button>
          </form>

          <div className="mt-6 text-center text-xs text-dark-400">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Log in
            </Link>
          </div>
        </Card>

        <div className="flex items-center justify-center gap-2 mt-8 text-xs text-dark-500">
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          <span>Includes free 14-day premium advisor trial</span>
        </div>
      </div>
    </div>
  );
};

export default Register;
