import React, { useState, useEffect } from 'react';
import { User, Mail, Shield, Key, Globe, Sparkles, CheckCircle2 } from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Profile = () => {
  const { user, updateProfileState } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState('English (US)');
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Sync state with user data
  useEffect(() => {
    if (user) {
      setName(user.full_name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSuccess('');
    setError('');
    setIsLoading(true);

    try {
      const payload = {
        full_name: name,
        email: email,
      };
      
      if (password) {
        payload.password = password;
      }
      
      const response = await api.put('/users/profile', payload);
      
      updateProfileState(response.data);
      setSuccess('Profile updated successfully.');
      setPassword(''); // clear password field
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setIsLoading(false);
    }
  };

  const initial = name ? name.charAt(0).toUpperCase() : 'U';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-dark-50 font-sans tracking-tight">User Profile</h2>
        <p className="text-dark-400 text-sm mt-1">Manage your developer identity and credential variables.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card & Stats */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="text-center py-8">
            <div className="flex flex-col items-center">
              {/* User Avatar Circle */}
              <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center font-bold text-white text-3xl shadow-lg shadow-brand-500/20 mb-4 border border-brand-400/20">
                {initial}
              </div>
              <h3 className="text-lg font-bold text-dark-50">{name}</h3>
              <p className="text-xs text-dark-400 mt-1">{email}</p>
              
              <div className="mt-4 px-3 py-1 bg-brand-500/10 border border-brand-500/20 rounded-full text-brand-400 text-[11px] font-semibold tracking-wider uppercase">
                SaaS Administrator
              </div>
            </div>

            <div className="border-t border-dark-850 mt-8 pt-6 space-y-4 text-left px-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-dark-400">Subscription status</span>
                <span className="text-green-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Active Pro
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-dark-400">Renewal Cycle</span>
                <span className="text-dark-200">Monthly ($49.00)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-dark-400">Workspace ID</span>
                <span className="font-mono text-dark-300">ef_ws_89a0f41</span>
              </div>
            </div>
          </Card>

          {/* Premium Tier Advisory */}
          <div className="p-5 rounded-xl bg-gradient-to-br from-brand-900/10 to-violet-950/10 border border-brand-500/20 relative overflow-hidden">
            <div className="absolute -right-6 -bottom-6 w-20 h-20 bg-brand-500/10 rounded-full blur-2xl"></div>
            <div className="flex items-center gap-2 text-brand-400 mb-2">
              <Sparkles className="w-4.5 h-4.5 animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wider">AI Optimizer Enabled</span>
            </div>
            <p className="text-[11px] text-dark-300 leading-relaxed mb-1">
              Your profile is optimized for automated tracking. Any added transactions are dynamically classified.
            </p>
          </div>
        </div>

        {/* Identity Form & Details */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Account Identity" subtitle="Update username and interface language">
            {success && (
              <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-400" /> {success}
              </div>
            )}
            
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2">
                <Shield className="w-4 h-4 text-red-400" /> {error}
              </div>
            )}
            
            <form onSubmit={handleSave} className="space-y-6 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">System Language</label>
                  <div className="relative">
                    <Globe className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all appearance-none"
                    >
                      <option>English (US)</option>
                      <option>Spanish (ES)</option>
                      <option>German (DE)</option>
                      <option>French (FR)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Update Password (Optional)</label>
                  <div className="relative">
                    <Shield className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Leave blank to keep same"
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-dark-850 flex justify-end">
                <Button type="submit" variant="primary" isLoading={isLoading}>
                  Save Changes
                </Button>
              </div>
            </form>
          </Card>

          <Card title="Developer API Credentials" subtitle="Access tokens for automated command ingestion">
            <div className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Workspace API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Key className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                    <input
                      type="password"
                      readOnly
                      value="ef_pk_live_d1a2938e2193b04c8f58"
                      className="w-full bg-dark-950 border border-dark-850 rounded-lg pl-10 pr-4 py-2.5 text-xs text-dark-300 font-mono outline-none"
                    />
                  </div>
                  <Button variant="secondary" onClick={() => navigator.clipboard.writeText("ef_pk_live_d1a2938e2193b04c8f58")}>
                    Copy Key
                  </Button>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-dark-950 border border-dark-850 flex items-start gap-3">
                <Shield className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-dark-200">Standard API Security</h4>
                  <p className="text-[11px] text-dark-400 leading-relaxed mt-1">
                    Keep your API keys private. Avoid placing credentials inside standard repository branches. 
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
