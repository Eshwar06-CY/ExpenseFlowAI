import { BasePage } from './BasePage';

export class TransfersPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addTransferButton = page.locator('button:has-text("Add Transfer"), button:has-text("New Transfer"), button:has-text("Transfer Money"), button:has-text("Execute Internal Transfer")').first();
    
    // Form fields
    this.sourceAccountSelect = page.locator('div.max-w-md select').first();
    this.destinationAccountSelect = page.locator('div.max-w-md select').last();
    this.amountInput = page.locator('div.max-w-md input[placeholder="0.00"]');
    this.descriptionInput = page.locator('div.max-w-md input[type="text"]');
    this.dateInput = page.locator('div.max-w-md input[type="date"]');
    this.submitButton = page.locator('div.max-w-md button[type="submit"]');
  }

  async navigate() {
    await this.goto('/dashboard/transfers');
    await this.waitForLoadingState();
  }

  async makeTransfer({ fromAccount, toAccount, amount, description, date }) {
    await this.addTransferButton.click();
    if (fromAccount) await this.selectOptionByText(this.sourceAccountSelect, fromAccount);
    if (toAccount) await this.selectOptionByText(this.destinationAccountSelect, toAccount);
    await this.amountInput.fill(amount.toString());
    if (description) await this.descriptionInput.fill(description);
    if (date) await this.dateInput.fill(date);
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
