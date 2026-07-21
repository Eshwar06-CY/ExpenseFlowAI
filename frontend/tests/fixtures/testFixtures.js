import { test as baseTest } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { DashboardPage } from '../pages/DashboardPage';
import { AccountsPage } from '../pages/AccountsPage';
import { IncomePage } from '../pages/IncomePage';
import { ExpensePage } from '../pages/ExpensePage';
import { BudgetPage } from '../pages/BudgetPage';
import { GoalsPage } from '../pages/GoalsPage';
import { ReportsPage } from '../pages/ReportsPage';
import { SettingsPage } from '../pages/SettingsPage';
import { TransfersPage } from '../pages/TransfersPage';
import { BillsPage } from '../pages/BillsPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { CategoriesPage } from '../pages/CategoriesPage';

// Common test configurations and constants
export const TEST_USER = {
  email: 'playwright_sdet@example.com',
  password: 'Password123!',
  name: 'Playwright Automation User'
};

export const COMMON_CONSTANTS = {
  urls: {
    base: 'http://localhost:5173',
    login: '/login',
    register: '/register',
    dashboard: '/dashboard',
    accounts: '/dashboard/accounts',
    income: '/dashboard/income',
    expenses: '/dashboard/expenses',
    budgets: '/dashboard/budgets',
    goals: '/dashboard/goals',
    bills: '/dashboard/bills',
    reports: '/dashboard/reports',
    analytics: '/dashboard/analytics',
    settings: '/dashboard/settings'
  }
};

// Extend base test with Page Object instances as custom fixtures
export const test = baseTest.extend({
  // Standalone page fixtures
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  
  registerPage: async ({ page }, use) => {
    await use(new RegisterPage(page));
  },

  forgotPasswordPage: async ({ page }, use) => {
    await use(new ForgotPasswordPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  
  accountsPage: async ({ page }, use) => {
    await use(new AccountsPage(page));
  },
  
  incomePage: async ({ page }, use) => {
    await use(new IncomePage(page));
  },
  
  expensePage: async ({ page }, use) => {
    await use(new ExpensePage(page));
  },
  
  budgetPage: async ({ page }, use) => {
    await use(new BudgetPage(page));
  },
  
  goalsPage: async ({ page }, use) => {
    await use(new GoalsPage(page));
  },
  
  reportsPage: async ({ page }, use) => {
    await use(new ReportsPage(page));
  },
  
  settingsPage: async ({ page }, use) => {
    await use(new SettingsPage(page));
  },

  transfersPage: async ({ page }, use) => {
    await use(new TransfersPage(page));
  },

  billsPage: async ({ page }, use) => {
    await use(new BillsPage(page));
  },

  analyticsPage: async ({ page }, use) => {
    await use(new AnalyticsPage(page));
  },

  categoriesPage: async ({ page }, use) => {
    await use(new CategoriesPage(page));
  },

  // A pre-authenticated page state fixture to skip repeating login steps for dashboard tests
  authenticatedPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.skipOnboardingIfVisible();
    
    await use(page);
  }
});

export { expect } from '@playwright/test';
