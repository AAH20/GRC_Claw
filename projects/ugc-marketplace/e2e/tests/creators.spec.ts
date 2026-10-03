import { test, expect } from '@playwright/test';

test.describe('Creators Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Creators');
    await page.waitForURL(/.*creators/);
  });

  test('should display creators page', async ({ page }) => {
    await expect(page).toHaveURL(/.*creators/);
    await expect(page.locator('h1')).toContainText('Creators');
  });

  test('should display creator grid', async ({ page }) => {
    await expect(page.locator('[data-testid="creator-grid"]')).toBeVisible();
  });

  test('should display creator cards', async ({ page }) => {
    await expect(page.locator('[data-testid="creator-card"]').first()).toBeVisible();
  });

  test('should search creators', async ({ page }) => {
    await page.fill('input[name="search"]', 'test');
    await expect(page.locator('[data-testid="creator-grid"]')).toBeVisible();
  });

  test('should filter creators by status', async ({ page }) => {
    await page.selectOption('select[name="status"]', 'active');
    await expect(page.locator('[data-testid="creator-grid"]')).toBeVisible();
  });
});
