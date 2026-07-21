import { BasePage } from './BasePage';

export class CategoriesPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    this.addCategoryButton = page.locator('button:has-text("Add Category")');
    this.seedDefaultsButton = page.locator('button:has-text("Seed defaults"), button:has-text("Seed Standard Templates")');
    
    // Modal input elements
    this.categoryNameInput = page.locator('input[placeholder="e.g. Subscriptions, Groceries"]');
    this.typeSelect = page.locator('select');
    this.submitButton = page.locator('button[type="submit"]');

    // List elements
    this.categoryCard = (name) => page.locator(`.bg-dark-900\\/40:has-text("${name}"), div:has-text("${name}")`).first();
    this.editCategoryButton = (name) => this.categoryCard(name).locator('button').first();
    this.deleteCategoryButton = (name) => this.categoryCard(name).locator('button').last();
  }

  async navigate() {
    await this.goto('/dashboard/categories');
    await this.waitForLoadingState();
  }

  async clickAddCategory() {
    await this.addCategoryButton.click();
  }

  async fillCategoryForm({ name, type }) {
    if (name) await this.categoryNameInput.fill(name);
    if (type) await this.typeSelect.selectOption({ value: type });
  }

  async createCategory({ name, type = 'expense' }) {
    await this.clickAddCategory();
    await this.fillCategoryForm({ name, type });
    await this.submitButton.click();
    await this.waitForLoadingState();
    await this.categoryCard(name).waitFor({ state: 'visible', timeout: 5000 });
  }

  async seedDefaults() {
    await this.seedDefaultsButton.first().click();
    await this.waitForLoadingState();
    await this.categoryCard('Food').waitFor({ state: 'visible', timeout: 5000 });
  }
}
