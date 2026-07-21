import { test, expect } from '@playwright/test';

test('ExpenseFlow Home Page Loads', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/ExpenseFlow/i);
});