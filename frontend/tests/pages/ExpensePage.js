import { BasePage } from './BasePage';

export class ExpensePage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addExpenseButton = page.locator('button:has-text("Add Expense"), button:has-text("New Expense"), button:has-text("Record Company Outflow"), button:has-text("Log Expense"), button:has-text("Record spending")').first();
    
    // Form elements
    this.amountInput = page.locator('.max-w-lg input[placeholder="0.00"]');
    this.descriptionInput = page.locator('.max-w-lg input[placeholder*="AWS Cloud"]');
    this.accountSelect = page.locator('.max-w-lg select').first();
    this.categorySelect = page.locator('.max-w-lg select').last();
    this.dateInput = page.locator('.max-w-lg input[type="date"]');
    this.submitButton = page.locator('.max-w-lg button[type="submit"]');

    // List and indicators
    this.expenseListRow = (desc) => page.locator(`tr:has-text("${desc}"), div[role="row"]:has-text("${desc}")`).first();
  }

  async navigate() {
    await this.goto('/dashboard/expenses');
    await this.waitForLoadingState();
  }

  async createExpense({ amount, description, account, category, date }) {
    await this.addExpenseButton.click();
    await this.amountInput.fill(amount.toString());
    await this.descriptionInput.fill(description);
    if (account) await this.selectOptionByText(this.accountSelect, account);
    if (category) await this.selectOptionByText(this.categorySelect, category);
    if (date) await this.dateInput.fill(date);
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
