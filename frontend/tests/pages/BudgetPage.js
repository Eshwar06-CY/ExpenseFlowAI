import { BasePage } from './BasePage';

export class BudgetPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addBudgetButton = page.locator('button:has-text("Add Budget"), button:has-text("New Budget"), button:has-text("Set Budget")');
    
    // Form selectors
    this.categorySelect = page.locator('select[name="category_id"], select[name="categoryId"]');
    this.limitInput = page.locator('input[name="limit"], input[name="amount"]');
    this.periodSelect = page.locator('select[name="period"]');
    this.submitButton = page.locator('button[type="submit"]');

    // Budget card
    this.budgetProgressCard = (catName) => page.locator(`.budget-card:has-text("${catName}"), div:has-text("${catName}")`).first();
  }

  async navigate() {
    await this.goto('/dashboard/budgets');
    await this.waitForLoadingState();
  }

  async setBudget({ category, limit, period = 'monthly' }) {
    await this.addBudgetButton.click();
    if (category) await this.categorySelect.selectOption({ label: category });
    await this.limitInput.fill(limit.toString());
    if (period) await this.periodSelect.selectOption({ value: period });
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
