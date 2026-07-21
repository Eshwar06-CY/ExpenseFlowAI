import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Profile settings
    this.nameInput = page.locator('input[name="name"], input[placeholder="Your Name"]');
    this.emailInput = page.locator('input[name="email"]');
    this.currencySelect = page.locator('select[name="default_currency"], select[name="currency"]');
    this.themeSelect = page.locator('select[name="theme"]');
    
    // Security update inputs
    this.currentPasswordInput = page.locator('input[name="current_password"], input[placeholder="Current Password"]');
    this.newPasswordInput = page.locator('input[name="new_password"], input[placeholder="New Password"]');
    this.confirmPasswordInput = page.locator('input[name="confirm_password"], input[placeholder="Confirm New Password"]');

    // Save buttons
    this.saveProfileButton = page.locator('button:has-text("Save Changes"), button:has-text("Update Profile")');
    this.saveSecurityButton = page.locator('button:has-text("Update Password"), button:has-text("Change Password")');
  }

  async navigate() {
    await this.goto('/dashboard/settings');
    await this.waitForLoadingState();
  }

  async updateProfile({ name, currency, theme }) {
    if (name) await this.nameInput.fill(name);
    if (currency) await this.currencySelect.selectOption({ value: currency });
    if (theme) await this.themeSelect.selectOption({ value: theme });
    await this.saveProfileButton.click();
    await this.waitForLoadingState();
  }

  async updatePassword(currentPassword, newPassword) {
    await this.currentPasswordInput.fill(currentPassword);
    await this.newPasswordInput.fill(newPassword);
    await this.confirmPasswordInput.fill(newPassword);
    await this.saveSecurityButton.click();
    await this.waitForLoadingState();
  }
}
