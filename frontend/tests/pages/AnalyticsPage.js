import { BasePage } from './BasePage';

export class AnalyticsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Date range selectors and chart objects
    this.timeframeSelect = page.locator('select[name="timeframe"], select[aria-label="Timeframe"]');
    this.chartsContainer = page.locator('.recharts-wrapper, .chart-container');
    this.categoriesBreakdownList = page.locator('.category-breakdown-list, ul:has-text("Categories")');
  }

  async navigate() {
    await this.goto('/dashboard/analytics');
    await this.waitForLoadingState();
  }

  async selectTimeframe(value) {
    await this.timeframeSelect.selectOption({ value });
    await this.waitForLoadingState();
  }

  async areChartsVisible() {
    return await this.chartsContainer.first().isVisible();
  }
}
