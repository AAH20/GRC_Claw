import { test, expect } from '@playwright/test';

test.describe('Listings Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Listings');
    await page.waitForURL(/.*listings/);
  });

  test('should display listings page', async ({ page }) => {
    await expect(page).toHaveURL(/.*listings/);
    await expect(page.locator('h1')).toContainText('Listings');
  });

  test('should display listing table', async ({ page }) => {
    await expect(page.locator('table')).toBeVisible();
  });

  test('should display listing table headers', async ({ page }) => {
    await expect(page.locator('th:has-text("Title")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Price")')).toBeVisible();
  });

  test('should have create listing button', async ({ page }) => {
    await expect(page.locator('button:has-text("Create Listing")')).toBeVisible();
  });

  test('should filter listings by status', async ({ page }) => {
    await page.selectOption('select[name="status"]', 'active');
    await expect(page.locator('table')).toBeVisible();
  });

  test('should search listings', async ({ page }) => {
    await page.fill('input[name="search"]', 'test');
    await expect(page.locator('table')).toBeVisible();
  });
});
