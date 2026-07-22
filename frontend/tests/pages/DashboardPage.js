import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // KPI Summary Panel selectors
    this.totalMoneyCard = page.locator('p').filter({ hasText: /Total money/i }).locator('..');
    this.moneySpentCard = page.locator('p').filter({ hasText: /Money spent/i }).locator('..');
    this.moneyEarnedCard = page.locator('p').filter({ hasText: /Money earned/i }).locator('..');
    
    // Onboarding Wizard selectors (if active)
    this.onboardingModal = page.locator('.onboarding-wizard-container');
    this.onboardingNextButton = page.locator('button:has-text("Next"), button:has-text("Continue")');
    this.onboardingCloseButton = page.locator('button:has-text("Skip Setup"), button:has-text("Skip"), button:has-text("Close")');

    // Layout configuration options
    this.customizeDashboardButton = page.locator('button:has-text("Customize"), button:has-text("Layout")');
  }

  async navigate() {
    await this.goto('/dashboard');
    await this.waitForLoadingState();
    await this.skipOnboardingIfVisible();
  }

  async isOnboardingVisible() {
    try {
      return await this.onboardingModal.isVisible({ timeout: 2000 });
    } catch (e) {
      return false;
    }
  }

  async skipOnboardingIfVisible() {
    if (await this.isOnboardingVisible()) {
      try {
        await this.onboardingCloseButton.click();
        await this.onboardingModal.waitFor({ state: 'hidden', timeout: 5000 });
      } catch (e) {}
    }
  }

  async getTotalMoneyValue() {
    return await this.totalMoneyCard.locator('.text-2xl, .font-bold').textContent();
  }
}
