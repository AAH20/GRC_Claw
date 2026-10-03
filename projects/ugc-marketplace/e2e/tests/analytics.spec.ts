import { test, expect } from '@playwright/test';

test.describe('Analytics Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Analytics');
    await page.waitForURL(/.*analytics/);
  });

  test('should display analytics page', async ({ page }) => {
    await expect(page).toHaveURL(/.*analytics/);
    await expect(page.locator('h1')).toContainText('Analytics');
  });

  test('should display analytics cards', async ({ page }) => {
    await expect(page.locator('[data-testid="analytics-card"]').first()).toBeVisible();
  });

  test('should display content performance section', async ({ page }) => {
    await expect(page.locator('[data-testid="content-performance"]')).toBeVisible();
  });

  test('should display top creators section', async ({ page }) => {
    await expect(page.locator('[data-testid="top-creators"]')).toBeVisible();
  });
});
