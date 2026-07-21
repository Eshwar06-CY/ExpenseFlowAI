import { BasePage } from './BasePage';

export class IncomePage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addIncomeButton = page.locator('button:has-text("Add Income"), button:has-text("New Income"), button:has-text("Record Company Inflow"), button:has-text("Log Income"), button:has-text("Record income")').first();
    
    // Transaction fields inside modal dialog
    this.amountInput = page.locator('.max-w-lg input[placeholder="0.00"]');
    this.descriptionInput = page.locator('.max-w-lg input[placeholder*="Acme Corp"]');
    this.accountSelect = page.locator('.max-w-lg select').first();
    this.categorySelect = page.locator('.max-w-lg select').last();
    this.dateInput = page.locator('.max-w-lg input[type="date"]');
    this.submitButton = page.locator('.max-w-lg button[type="submit"]');

    // Filters and tables
    this.searchBar = page.locator('input[placeholder*="Search"]');
    this.transactionRow = (desc) => page.locator(`tr:has-text("${desc}"), div[role="row"]:has-text("${desc}")`).first();
  }

  async navigate() {
    await this.goto('/dashboard/income');
    await this.waitForLoadingState();
  }

  async createIncome({ amount, description, account, category, date }) {
    await this.addIncomeButton.click();
    await this.amountInput.fill(amount.toString());
    await this.descriptionInput.fill(description);
    if (account) await this.selectOptionByText(this.accountSelect, account);
    if (category) await this.selectOptionByText(this.categorySelect, category);
    if (date) await this.dateInput.fill(date);
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
