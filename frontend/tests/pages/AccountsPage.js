import { BasePage } from './BasePage';

export class AccountsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addAccountButton = page.locator('button:has-text("Add Account"), button:has-text("New Account"), button:has-text("Create First Account")').first();
    
    // Create / Edit modal selectors
    this.accountNameInput = page.locator('input[placeholder*="Chase checking"]');
    this.accountTypeSelect = page.locator('select').first();
    this.balanceInput = page.locator('input[type="number"]');
    this.currencySelect = page.locator('select').last();
    this.submitAccountButton = page.locator('button[type="submit"]');
    
    // Card elements
    this.accountCard = (name) => page.locator(`.edl-card:has-text("${name}")`).first();
    this.deleteAccountButton = (name) => this.accountCard(name).locator('button').last();
  }

  async navigate() {
    await this.goto('/dashboard/accounts');
    await this.waitForLoadingState();
  }

  async clickAddAccount() {
    await this.addAccountButton.click();
  }

  async fillAccountForm({ name, type, balance, currency }) {
    if (name) await this.accountNameInput.fill(name);
    if (type) {
      const actualType = (type === 'checking' || type === 'savings') ? 'bank' : type;
      await this.accountTypeSelect.selectOption({ value: actualType });
    }
    if (balance !== undefined) await this.balanceInput.fill(balance.toString());
    if (currency) await this.currencySelect.selectOption({ value: currency });
  }

  async createAccount({ name, type = 'bank', balance = 0, currency = 'USD' }) {
    await this.clickAddAccount();
    await this.fillAccountForm({ name, type, balance, currency });
    await this.submitAccountButton.click();
    await this.waitForLoadingState();
    await this.accountCard(name).waitFor({ state: 'visible', timeout: 5000 });
  }
}
