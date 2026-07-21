import { BasePage } from './BasePage';

export class ForgotPasswordPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.emailInput = page.locator('input[type="email"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.successMessageBox = page.locator('h3:has-text("Check your inbox")');
    this.successMessageText = page.locator('p:has-text("We sent a recovery email")');
    this.backToLoginLink = page.locator('a[href="/login"]');
  }

  async navigate() {
    await this.goto('/forgot-password');
  }

  async submitResetRequest(email) {
    await this.navigate();
    await this.emailInput.fill(email);
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
