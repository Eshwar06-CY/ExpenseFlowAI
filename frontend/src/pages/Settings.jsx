import React, { useState, useEffect } from 'react';
import { User, Shield, Sliders, Database, Save, Lock, Download, Trash2, Bell, Eye, EyeOff, Sun, Moon, Laptop, Globe } from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';

const Settings = () => {
  const { user, updateProfileState, logout } = useAuth();
  const { addToast } = useToast();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');
  
  // Profile state
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);

  // Security state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

  // Preferences state
  const [currency, setCurrency] = useState(() => localStorage.getItem('ef_currency') || 'USD');
  const [timezone, setTimezone] = useState(() => localStorage.getItem('ef_timezone') || 'UTC');
  const [language, setLanguage] = useState(() => localStorage.getItem('ef_language') || 'en');

  // Expanded Notifications state
  const [budgetAlerts, setBudgetAlerts] = useState(true);
  const [billReminders, setBillReminders] = useState(true);
  const [emailDigest, setEmailDigest] = useState('weekly');
  const [smsAlerts, setSmsAlerts] = useState(false);
  const [alertThreshold, setAlertThreshold] = useState('80');

  // Data & Privacy state
  const [exporting, setExporting] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || user.name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'preferences', name: 'Preferences & Regional', icon: Sliders },
    { id: 'notifications', name: 'Notifications preferences', icon: Bell },
    { id: 'data', name: 'Data & Privacy', icon: Database },
  ];

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    try {
      const res = await api.put('/users/profile', { full_name: fullName, email });
      updateProfileState(res.data);
      addToast('Profile updated successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to update profile.', 'error');
    } finally {
      setProfileSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      addToast('Passwords do not match.', 'error');
      return;
    }
    if (newPassword.length < 8) {
      addToast('Password must be at least 8 characters.', 'error');
      return;
    }
    setPasswordSaving(true);
    try {
      await api.put('/settings/password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      addToast('Password changed successfully!', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to change password.', 'error');
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleSavePreferences = () => {
    localStorage.setItem('ef_currency', currency);
    localStorage.setItem('ef_timezone', timezone);
    localStorage.setItem('ef_language', language);
    setTheme(theme);
    addToast('Regional preferences saved successfully!', 'success');
  };

  const handleSaveNotificationPreferences = () => {
    localStorage.setItem('ef_notif_budget', budgetAlerts.toString());
    localStorage.setItem('ef_notif_bill', billReminders.toString());
    localStorage.setItem('ef_notif_digest', emailDigest);
    localStorage.setItem('ef_notif_sms', smsAlerts.toString());
    localStorage.setItem('ef_notif_threshold', alertThreshold);
    addToast('Notification preferences saved successfully!', 'success');
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const response = await api.post('/settings/export-data', {}, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `expenseflow_data_export_${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      window.URL.revokeObjectURL(url);
      addToast('Data exported successfully!', 'success');
    } catch (err) {
      addToast('Failed to export data.', 'error');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await api.delete('/settings/account', {
        data: { password: deletePassword, confirmation: deleteConfirmation },
      });
      addToast('Account deactivated. You will be logged out.', 'warning', 5000);
      setTimeout(() => logout(), 2000);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete account.', 'error');
    } finally {
      setDeleting(false);
      setDeleteConfirmOpen(false);
    }
  };

  const inputClass = "w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30 transition-all";
  const labelClass = "block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2";

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-dark-50 font-sans tracking-tight">Settings</h2>
        <p className="text-dark-400 text-sm mt-1">Configure and manage your workspace properties.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors text-left border ${
                  activeTab === tab.id
                    ? 'bg-brand-600/10 text-brand-400 border-brand-500/20'
                    : 'text-dark-400 hover:text-dark-200 bg-transparent border-transparent hover:bg-dark-900/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <Card title="Profile Settings" subtitle="Update your personal information">
              <form onSubmit={handleSaveProfile} className="space-y-6 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className={labelClass}>Full Name</label>
                    <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputClass} required />
                  </div>
                  <div>
                    <label className={labelClass}>Email Address</label>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} required />
                  </div>
                </div>
                <div className="pt-4 border-t border-dark-850 flex justify-end">
                  <Button type="submit" variant="primary" disabled={profileSaving} className="flex items-center gap-2">
                    <Save className="w-4 h-4" /> {profileSaving ? 'Saving...' : 'Save Profile'}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <Card title="Security Settings" subtitle="Manage your password and account security">
              <form onSubmit={handleChangePassword} className="space-y-6 mt-4">
                <div>
                  <label className={labelClass}>Current Password</label>
                  <div className="relative">
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className={inputClass}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className={labelClass}>New Password</label>
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className={inputClass}
                      minLength={8}
                      required
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Confirm New Password</label>
                    <input
                      type={showPasswords ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className={inputClass}
                      minLength={8}
                      required
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm text-dark-400 cursor-pointer select-none">
                  <button type="button" onClick={() => setShowPasswords(!showPasswords)} className="text-dark-500 hover:text-dark-300">
                    {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                  {showPasswords ? 'Hide passwords' : 'Show passwords'}
                </label>
                <div className="pt-4 border-t border-dark-850 flex justify-end">
                  <Button type="submit" variant="primary" disabled={passwordSaving} className="flex items-center gap-2">
                    <Lock className="w-4 h-4" /> {passwordSaving ? 'Changing...' : 'Change Password'}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <Card title="Preferences & Regional" subtitle="Customize the interface look, currency, language, and timezone">
              <div className="space-y-6 mt-4">
                {/* Theme Selection */}
                <div>
                  <label className={labelClass}>Application UI Theme</label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => setTheme('dark')}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-sm font-semibold transition-all ${
                        theme === 'dark'
                          ? 'bg-brand-600/10 text-brand-400 border-brand-500'
                          : 'bg-dark-950 border-dark-850 text-dark-400 hover:text-dark-200'
                      }`}
                    >
                      <Moon className="w-4 h-4" /> Dark Mode
                    </button>
                    <button
                      type="button"
                      onClick={() => setTheme('light')}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-sm font-semibold transition-all ${
                        theme === 'light'
                          ? 'bg-brand-600/10 text-brand-400 border-brand-500'
                          : 'bg-dark-950 border-dark-850 text-dark-400 hover:text-dark-200'
                      }`}
                    >
                      <Sun className="w-4 h-4" /> Light Mode
                    </button>
                    <button
                      type="button"
                      onClick={() => setTheme('system')}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-sm font-semibold transition-all ${
                        theme === 'system'
                          ? 'bg-brand-600/10 text-brand-400 border-brand-500'
                          : 'bg-dark-950 border-dark-850 text-dark-400 hover:text-dark-200'
                      }`}
                    >
                      <Laptop className="w-4 h-4" /> System
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Currency Selection */}
                  <div>
                    <label className={labelClass}>Base Currency</label>
                    <select value={currency} onChange={(e) => setCurrency(e.target.value)} className={inputClass}>
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                      <option value="INR">INR (₹)</option>
                      <option value="JPY">JPY (¥)</option>
                      <option value="CAD">CAD (C$)</option>
                      <option value="AUD">AUD (A$)</option>
                    </select>
                  </div>

                  {/* Timezone Selection */}
                  <div>
                    <label className={labelClass}>Local Timezone</label>
                    <select value={timezone} onChange={(e) => setTimezone(e.target.value)} className={inputClass}>
                      <option value="UTC">UTC (GMT+0)</option>
                      <option value="America/New_York">US Eastern (EST)</option>
                      <option value="America/Los_Angeles">US Pacific (PST)</option>
                      <option value="Europe/London">London (GMT/BST)</option>
                      <option value="Europe/Paris">Central European (CET)</option>
                      <option value="Asia/Kolkata">India (IST)</option>
                      <option value="Asia/Tokyo">Japan (JST)</option>
                    </select>
                  </div>

                  {/* Language Selection */}
                  <div>
                    <label className={labelClass}>Display Language</label>
                    <select value={language} onChange={(e) => setLanguage(e.target.value)} className={inputClass}>
                      <option value="en">English (US)</option>
                      <option value="es">Español (ES)</option>
                      <option value="fr">Français (FR)</option>
                      <option value="de">Deutsch (DE)</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t border-dark-850 flex justify-end">
                  <Button variant="primary" onClick={handleSavePreferences} className="flex items-center gap-2">
                    <Save className="w-4 h-4" /> Save Preferences
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <Card title="Notification Preferences" subtitle="Control alert limits, digests, and multi-channel reports">
              <div className="space-y-4 mt-4">
                <label className="flex items-center justify-between p-4 rounded-lg bg-dark-950 border border-dark-850 cursor-pointer group hover:border-dark-750 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-dark-200">Budget Limit Alerts</p>
                    <p className="text-xs text-dark-500 mt-0.5">Get notified when spending exceeds category budgets</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={budgetAlerts}
                    onChange={(e) => setBudgetAlerts(e.target.checked)}
                    className="rounded border-dark-700 bg-dark-900 text-brand-600 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                  />
                </label>

                {budgetAlerts && (
                  <div className="p-4 rounded-lg bg-dark-950/40 border border-dark-850 ml-4 space-y-2 animate-slide-down">
                    <label className="block text-xs font-semibold text-dark-400 mb-1.5">Alert Threshold Percentage (%)</label>
                    <input
                      type="number"
                      value={alertThreshold}
                      min="50"
                      max="100"
                      onChange={(e) => setAlertThreshold(e.target.value)}
                      className="w-32 bg-dark-950 border border-dark-800 rounded-lg px-3 py-1.5 text-xs text-dark-200 outline-none focus:border-brand-500"
                    />
                    <span className="text-[10px] text-dark-500 block">Trigger warnings when monthly category spent reaches this threshold (e.g. 80%).</span>
                  </div>
                )}

                <label className="flex items-center justify-between p-4 rounded-lg bg-dark-950 border border-dark-850 cursor-pointer group hover:border-dark-750 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-dark-200">Bill Reminders</p>
                    <p className="text-xs text-dark-500 mt-0.5">Receive alerts before bills are due</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={billReminders}
                    onChange={(e) => setBillReminders(e.target.checked)}
                    className="rounded border-dark-700 bg-dark-900 text-brand-600 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                  />
                </label>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Email Digests Option */}
                  <div className="p-4 rounded-lg bg-dark-950 border border-dark-850 space-y-2">
                    <p className="text-sm font-medium text-dark-200">Email Digests</p>
                    <p className="text-xs text-dark-500">Summary reports delivered to your inbox</p>
                    <select
                      value={emailDigest}
                      onChange={(e) => setEmailDigest(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-800 rounded-lg px-3 py-2 text-xs text-dark-350 outline-none focus:border-brand-500"
                    >
                      <option value="daily">Daily Digest Briefs</option>
                      <option value="weekly">Weekly Summary</option>
                      <option value="monthly">Monthly Financial Report</option>
                      <option value="off">Off (Disable)</option>
                    </select>
                  </div>

                  {/* SMS Warnings Toggles */}
                  <div className="p-4 rounded-lg bg-dark-950 border border-dark-850 flex flex-col justify-between">
                    <div>
                      <p className="text-sm font-medium text-dark-200">SMS Outflow Alert Warnings</p>
                      <p className="text-xs text-dark-500 mt-0.5">Instant phone alerts for suspicious outflows</p>
                    </div>
                    <label className="flex items-center gap-2 text-xs text-dark-300 mt-3 select-none cursor-pointer">
                      <input
                        type="checkbox"
                        checked={smsAlerts}
                        onChange={(e) => setSmsAlerts(e.target.checked)}
                        className="rounded border-dark-700 bg-dark-900 text-brand-600 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                      />
                      Enable SMS Alerts (Standard charges apply)
                    </label>
                  </div>
                </div>

                <div className="pt-4 border-t border-dark-850 flex justify-end">
                  <Button variant="primary" onClick={handleSaveNotificationPreferences} className="flex items-center gap-2">
                    <Save className="w-4 h-4" /> Save Preferences
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Data & Privacy Tab */}
          {activeTab === 'data' && (
            <div className="space-y-6">
              <Card title="Export Your Data" subtitle="Download all your financial data as JSON">
                <div className="mt-4">
                  <p className="text-sm text-dark-400 mb-4">
                    Export includes: accounts, transactions, categories, budgets, goals, and bills.
                  </p>
                  <Button variant="primary" onClick={handleExportData} disabled={exporting} className="flex items-center gap-2">
                    <Download className="w-4 h-4" /> {exporting ? 'Exporting...' : 'Download Data Export'}
                  </Button>
                </div>
              </Card>

              <Card title="System & Database" subtitle="Core system information">
                <div className="mt-4 space-y-6">
                  <div className="p-4 rounded-lg bg-dark-950 border border-dark-850 space-y-4">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-dark-400">Database Engine</span>
                      <span className="font-mono text-xs text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">MySQL 8.0</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-dark-400">Connection Handler</span>
                      <span className="font-mono text-xs text-dark-200">SQLAlchemy ORM (pymysql)</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-dark-400">Active Connection Status</span>
                      <span className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                        Connection Pool Ready
                      </span>
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-2">
                  <h3 className="text-lg font-bold text-red-400 mb-2">Danger Zone</h3>
                  <p className="text-sm text-dark-400 mb-4">
                    Permanently deactivate your account. This action cannot be easily reversed.
                  </p>
                  <Button
                    variant="danger"
                    onClick={() => setDeleteConfirmOpen(true)}
                    className="flex items-center gap-2 !bg-red-600/10 !text-red-400 !border-red-500/20 hover:!bg-red-600 hover:!text-white"
                  >
                    <Trash2 className="w-4 h-4" /> Delete Account
                  </Button>
                </div>
              </Card>

              {/* Delete Account Confirmation */}
              {deleteConfirmOpen && (
                <div className="fixed inset-0 z-[9998] flex items-center justify-center">
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm confirm-backdrop-enter" onClick={() => setDeleteConfirmOpen(false)} />
                  <div className="relative z-10 bg-dark-900 border border-dark-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 confirm-dialog-enter">
                    <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
                      <Trash2 className="w-6 h-6 text-red-400" />
                    </div>
                    <h3 className="text-lg font-bold text-dark-50 mb-2">Delete Your Account</h3>
                    <p className="text-sm text-dark-400 mb-4">This will permanently deactivate your account. Enter your password and type <strong className="text-red-400">DELETE MY ACCOUNT</strong> to confirm.</p>
                    <div className="space-y-3 mb-6">
                      <input
                        type="password"
                        placeholder="Enter your password"
                        value={deletePassword}
                        onChange={(e) => setDeletePassword(e.target.value)}
                        className={inputClass}
                      />
                      <input
                        type="text"
                        placeholder="Type DELETE MY ACCOUNT"
                        value={deleteConfirmation}
                        onChange={(e) => setDeleteConfirmation(e.target.value)}
                        className={inputClass}
                      />
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => setDeleteConfirmOpen(false)}
                        className="flex-1 px-4 py-2.5 rounded-lg border border-dark-700 text-sm font-medium text-dark-300 hover:bg-dark-800 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleDeleteAccount}
                        disabled={deleting || deleteConfirmation !== 'DELETE MY ACCOUNT' || !deletePassword}
                        className="flex-1 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deleting ? 'Deleting...' : 'Delete Account'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
