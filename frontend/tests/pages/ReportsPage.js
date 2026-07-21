import { BasePage } from './BasePage';

export class ReportsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Export selectors
    this.reportTypeSelect = page.locator('select[name="report_type"], select[name="type"]');
    this.periodSelect = page.locator('select[name="period"]');
    this.exportPdfButton = page.locator('button:has-text("Export PDF"), button:has-text("Download PDF")');
    this.exportCsvButton = page.locator('button:has-text("Export CSV"), button:has-text("Download CSV")');
  }

  async navigate() {
    await this.goto('/dashboard/reports');
    await this.waitForLoadingState();
  }

  async selectReportType(type) {
    await this.reportTypeSelect.selectOption({ value: type });
  }

  async selectPeriod(period) {
    await this.periodSelect.selectOption({ value: period });
  }

  async downloadPdfReport() {
    // Return a promise that resolves when the download completes
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportPdfButton.click();
    return await downloadPromise;
  }
}
