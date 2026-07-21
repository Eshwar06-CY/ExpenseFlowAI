import { BasePage } from './BasePage';

export class RegisterPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Form inputs
    this.nameInput = page.locator('input[placeholder="John Doe"]');
    this.emailInput = page.locator('input[type="email"]');
    this.passwordInput = page.locator('input[placeholder="••••••••"]').first();
    this.confirmPasswordInput = page.locator('input[placeholder="••••••••"]').last();
    this.acceptTermsCheckbox = page.locator('input[type="checkbox"]');
    this.submitButton = page.locator('button[type="submit"]');

    // Messages
    this.errorMessage = page.locator('.p-3.bg-red-500\\/10');
    this.loginLink = page.locator('a[href="/login"]');
  }

  async navigate() {
    await this.goto('/register');
  }

  async register({ name, email, password, confirmPassword, acceptTerms = true }) {
    await this.navigate();
    if (name) await this.nameInput.fill(name);
    if (email) await this.emailInput.fill(email);
    if (password) await this.passwordInput.fill(password);
    if (confirmPassword) await this.confirmPasswordInput.fill(confirmPassword);
    if (acceptTerms) {
      const isChecked = await this.acceptTermsCheckbox.isChecked();
      if (!isChecked) await this.acceptTermsCheckbox.check();
    } else {
      const isChecked = await this.acceptTermsCheckbox.isChecked();
      if (isChecked) await this.acceptTermsCheckbox.uncheck();
    }
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
