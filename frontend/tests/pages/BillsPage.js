import { BasePage } from './BasePage';

export class BillsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addBillButton = page.locator('button:has-text("Add Bill"), button:has-text("New Bill"), button:has-text("Create Bill")');
    
    // Form fields
    this.billNameInput = page.locator('input[name="name"], input[placeholder="Bill Name"]');
    this.amountInput = page.locator('input[name="amount"]');
    this.dueDateInput = page.locator('input[name="due_date"], input[name="dueDate"], input[type="date"]');
    this.categorySelect = page.locator('select[name="category_id"], select[name="categoryId"]');
    this.submitButton = page.locator('button[type="submit"]');

    // Bill lists
    this.billCard = (name) => page.locator(`.bill-card:has-text("${name}"), div:has-text("${name}")`).first();
    this.payBillButton = (name) => this.billCard(name).locator('button:has-text("Pay"), button:has-text("Mark Paid")');
  }

  async navigate() {
    await this.goto('/dashboard/bills');
    await this.waitForLoadingState();
  }

  async createBill({ name, amount, dueDate, category }) {
    await this.addBillButton.click();
    await this.billNameInput.fill(name);
    await this.amountInput.fill(amount.toString());
    if (dueDate) await this.dueDateInput.fill(dueDate);
    if (category) await this.categorySelect.selectOption({ label: category });
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
