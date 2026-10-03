import { test, expect } from '@playwright/test';

test.describe('Transactions Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Transactions');
    await page.waitForURL(/.*transactions/);
  });

  test('should display transactions page', async ({ page }) => {
    await expect(page).toHaveURL(/.*transactions/);
    await expect(page.locator('h1')).toContainText('Transactions');
  });

  test('should display transaction list', async ({ page }) => {
    await expect(page.locator('[data-testid="transaction-list"]')).toBeVisible();
  });

  test('should display transaction chart', async ({ page }) => {
    await expect(page.locator('[data-testid="transaction-chart"]')).toBeVisible();
  });

  test('should filter transactions by type', async ({ page }) => {
    await page.selectOption('select[name="type"]', 'sale');
    await expect(page.locator('[data-testid="transaction-list"]')).toBeVisible();
  });

  test('should filter transactions by status', async ({ page }) => {
    await page.selectOption('select[name="status"]', 'completed');
    await expect(page.locator('[data-testid="transaction-list"]')).toBeVisible();
  });
});
