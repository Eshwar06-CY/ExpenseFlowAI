import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './layouts/DashboardLayout';
import ProtectedRoute from './components/Common/ProtectedRoute';
import { DashboardSkeleton } from './components/Common/SkeletonLoader';
import ErrorBoundary from './components/Common/ErrorBoundary';
import OfflineBanner from './components/Common/OfflineBanner';

// Lazy-loaded pages for route-level code splitting
const Landing = lazy(() => import('./pages/Landing'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Expenses = lazy(() => import('./pages/Expenses'));
const Income = lazy(() => import('./pages/Income'));
const Accounts = lazy(() => import('./pages/Accounts'));
const Categories = lazy(() => import('./pages/Categories'));
const Transfers = lazy(() => import('./pages/Transfers'));
const Budgets = lazy(() => import('./pages/Budgets'));
const Goals = lazy(() => import('./pages/Goals'));
const Bills = lazy(() => import('./pages/Bills'));
const Recurring = lazy(() => import('./pages/Recurring'));
const Reports = lazy(() => import('./pages/Reports'));
const Insights = lazy(() => import('./pages/Insights'));
const Settings = lazy(() => import('./pages/Settings'));
const Notifications = lazy(() => import('./pages/Notifications'));
const ImportWizard = lazy(() => import('./pages/ImportWizard'));
const ImportHistory = lazy(() => import('./pages/ImportHistory'));
const ForecastDashboard = lazy(() => import('./pages/ForecastDashboard'));
const FinancialTimeline = lazy(() => import('./pages/FinancialTimeline'));
const FinancialHealth = lazy(() => import('./pages/FinancialHealth'));
const Profile = lazy(() => import('./pages/Profile'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const NotFound = lazy(() => import('./pages/NotFound'));
const Workspaces = lazy(() => import('./pages/Workspaces'));
const Automations = lazy(() => import('./pages/Automations'));
const AIChat = lazy(() => import('./pages/AIChat'));
const DigestPage = lazy(() => import('./pages/DigestPage'));

const PageFallback = () => (
  <div className="p-6 md:p-8 max-w-7xl mx-auto">
    <DashboardSkeleton />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Router>
          <AuthProvider>
            <ToastProvider>
            <Suspense fallback={<PageFallback />}>
              <Routes>
                {/* Public Landing page */}
                <Route path="/" element={<Landing />} />

                {/* Auth pages outside layout */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />

                {/* Protected layouts core */}
                <Route path="/dashboard" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                  <Route index element={<Suspense fallback={<DashboardSkeleton />}><Dashboard /></Suspense>} />
                  <Route path="analytics" element={<Suspense fallback={<DashboardSkeleton />}><Analytics /></Suspense>} />
                  <Route path="expenses" element={<Suspense fallback={<DashboardSkeleton />}><Expenses /></Suspense>} />
                  <Route path="income" element={<Suspense fallback={<DashboardSkeleton />}><Income /></Suspense>} />
                  <Route path="accounts" element={<Suspense fallback={<DashboardSkeleton />}><Accounts /></Suspense>} />
                  <Route path="categories" element={<Suspense fallback={<DashboardSkeleton />}><Categories /></Suspense>} />
                  <Route path="transfers" element={<Suspense fallback={<DashboardSkeleton />}><Transfers /></Suspense>} />
                  <Route path="budgets" element={<Suspense fallback={<DashboardSkeleton />}><Budgets /></Suspense>} />
                  <Route path="goals" element={<Suspense fallback={<DashboardSkeleton />}><Goals /></Suspense>} />
                  <Route path="bills" element={<Suspense fallback={<DashboardSkeleton />}><Bills /></Suspense>} />
                  <Route path="recurring" element={<Suspense fallback={<DashboardSkeleton />}><Recurring /></Suspense>} />
                  <Route path="reports" element={<Suspense fallback={<DashboardSkeleton />}><Reports /></Suspense>} />
                  <Route path="insights" element={<Suspense fallback={<DashboardSkeleton />}><Insights /></Suspense>} />
                  <Route path="notifications" element={<Suspense fallback={<DashboardSkeleton />}><Notifications /></Suspense>} />
                  <Route path="import-wizard" element={<Suspense fallback={<DashboardSkeleton />}><ImportWizard /></Suspense>} />
                  <Route path="import-history" element={<Suspense fallback={<DashboardSkeleton />}><ImportHistory /></Suspense>} />
                  <Route path="forecast" element={<Suspense fallback={<DashboardSkeleton />}><ForecastDashboard /></Suspense>} />
                  <Route path="timeline" element={<Suspense fallback={<DashboardSkeleton />}><FinancialTimeline /></Suspense>} />
                  <Route path="health" element={<Suspense fallback={<DashboardSkeleton />}><FinancialHealth /></Suspense>} />
                  <Route path="settings" element={<Suspense fallback={<DashboardSkeleton />}><Settings /></Suspense>} />
                  <Route path="profile" element={<Suspense fallback={<DashboardSkeleton />}><Profile /></Suspense>} />
                  <Route path="workspaces" element={<Suspense fallback={<DashboardSkeleton />}><Workspaces /></Suspense>} />
                  <Route path="automations" element={<Suspense fallback={<DashboardSkeleton />}><Automations /></Suspense>} />
                  <Route path="chat" element={<Suspense fallback={<DashboardSkeleton />}><AIChat /></Suspense>} />
                  <Route path="digest" element={<Suspense fallback={<DashboardSkeleton />}><DigestPage /></Suspense>} />
                  {/* Fallback route inside layout */}
                  <Route path="*" element={<NotFound />} />
                </Route>

                {/* Global Fallback */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
            <OfflineBanner />
          </ToastProvider>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  </ErrorBoundary>
  );
}

export default App;
