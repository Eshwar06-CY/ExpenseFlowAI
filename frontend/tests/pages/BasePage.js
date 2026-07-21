/**
 * BasePage Class providing common helper elements and methods for all Page Objects.
 */
export class BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    
    // Core Layout Selectors
    this.toastNotification = page.locator('.toast, [role="alert"]');
    this.loadingIndicator = page.locator('.loading-spinner, .animate-spin, [role="status"]');
    
    // Navigation Sidebar Links (using descriptive text selectors matching App.jsx routes)
    this.sidebarToggle = page.locator('#sidebar-toggle, [aria-label="Toggle Sidebar"]');
    this.navDashboard = page.locator('a[href="/dashboard"]');
    this.navAccounts = page.locator('a[href="/dashboard/accounts"]');
    this.navIncome = page.locator('a[href="/dashboard/income"]');
    this.navExpenses = page.locator('a[href="/dashboard/expenses"]');
    this.navTransfers = page.locator('a[href="/dashboard/transfers"]');
    this.navBudgets = page.locator('a[href="/dashboard/budgets"]');
    this.navGoals = page.locator('a[href="/dashboard/goals"]');
    this.navBills = page.locator('a[href="/dashboard/bills"]');
    this.navReports = page.locator('a[href="/dashboard/reports"]');
    this.navAnalytics = page.locator('a[href="/dashboard/analytics"]');
    this.navSettings = page.locator('a[href="/dashboard/settings"]');
    this.navProfile = page.locator('a[href="/dashboard/profile"]');
  }

  async goto(path = '/') {
    await this.page.goto(path);
  }

  async waitForLoadingState() {
    // Wait until the loading indicator is hidden if it is present
    if (await this.loadingIndicator.isVisible()) {
      await this.loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
    }
  }

  async getToastMessage() {
    await this.toastNotification.first().waitFor({ state: 'visible', timeout: 5000 });
    return await this.toastNotification.first().textContent();
  }

  async navigateTo(linkLocator) {
    await linkLocator.click();
    await this.waitForLoadingState();
    await this.page.waitForLoadState('networkidle');
  }

  async logout() {
    const profileTrigger = this.page.locator('[aria-label="User profile settings"]');
    await profileTrigger.hover();
    
    const logoutBtn = this.page.locator('button:has-text("Logout"), button:has-text("Sign Out"), button:has-text("Logout Account")');
    await logoutBtn.waitFor({ state: 'visible', timeout: 5000 });
    await logoutBtn.click();
    await this.page.waitForLoadState('networkidle');
  }

  async selectOptionByText(selectLocator, text) {
    await selectLocator.waitFor({ state: 'visible', timeout: 5000 });
    const option = selectLocator.locator('option', { hasText: text }).first();
    await option.waitFor({ state: 'attached', timeout: 5000 });
    const value = await option.getAttribute('value');
    await selectLocator.selectOption(value);
  }
}
