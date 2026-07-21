import { BasePage } from './BasePage';

export class LoginPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);
    
    // Auth Input Selectors
    this.emailInput = page.locator('input[type="email"]');
    this.passwordInput = page.locator('input[type="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.registerLink = page.locator('a[href="/register"]');
    this.forgotPasswordLink = page.locator('a[href="/forgot-password"]');
  }

  async navigate() {
    await this.goto('/login');
  }

  async fillEmail(email) {
    await this.emailInput.fill(email);
  }

  async fillPassword(password) {
    await this.passwordInput.fill(password);
  }

  async clickSubmit() {
    await this.submitButton.click();
    await this.waitForLoadingState();
  }

  async login(email, password) {
    await this.navigate();
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.clickSubmit();
  }
}
