import { BasePage } from './BasePage';

export class GoalsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addGoalButton = page.locator('button:has-text("Add Goal"), button:has-text("New Goal"), button:has-text("Create Goal")');
    
    // Form selectors
    this.goalNameInput = page.locator('input[name="name"]');
    this.targetAmountInput = page.locator('input[name="target_amount"], input[name="targetAmount"]');
    this.currentAmountInput = page.locator('input[name="current_amount"], input[name="currentAmount"]');
    this.targetDateInput = page.locator('input[name="target_date"], input[type="date"]');
    this.submitButton = page.locator('button[type="submit"]');

    // Goals display
    this.goalCard = (name) => page.locator(`.goal-card:has-text("${name}"), div:has-text("${name}")`).first();
  }

  async navigate() {
    await this.goto('/dashboard/goals');
    await this.waitForLoadingState();
  }

  async createGoal({ name, targetAmount, currentAmount = 0, targetDate }) {
    await this.addGoalButton.click();
    await this.goalNameInput.fill(name);
    await this.targetAmountInput.fill(targetAmount.toString());
    await this.currentAmountInput.fill(currentAmount.toString());
    if (targetDate) await this.targetDateInput.fill(targetDate);
    await this.submitButton.click();
    await this.waitForLoadingState();
  }
}
