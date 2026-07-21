import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // KPI Summary Panel selectors
    this.totalMoneyCard = page.locator('.edl-card').filter({ has: page.locator('p:has-text("Total money I have")') }).first();
    this.moneySpentCard = page.locator('.edl-card').filter({ has: page.locator('p:has-text("Money spent")') }).first();
    this.moneyEarnedCard = page.locator('.edl-card').filter({ has: page.locator('p:has-text("Money earned")') }).first();
    
    // Onboarding Wizard selectors (if active)
    this.onboardingModal = page.locator('.onboarding-wizard-container, [role="dialog"]:has-text("Welcome to ExpenseFlow")');
    this.onboardingNextButton = page.locator('button:has-text("Next"), button:has-text("Continue")');
    this.onboardingCloseButton = page.locator('button:has-text("Skip"), button:has-text("Close")');

    // Layout configuration options
    this.customizeDashboardButton = page.locator('button:has-text("Customize"), button:has-text("Layout")');
  }

  async navigate() {
    await this.goto('/dashboard');
    await this.waitForLoadingState();
  }

  async isOnboardingVisible() {
    return await this.onboardingModal.isVisible();
  }

  async skipOnboardingIfVisible() {
    if (await this.isOnboardingVisible()) {
      await this.onboardingCloseButton.click();
      await this.onboardingModal.waitFor({ state: 'hidden', timeout: 5000 });
    }
  }

  async getTotalMoneyValue() {
    return await this.totalMoneyCard.locator('.text-2xl, .font-bold').textContent();
  }
}
