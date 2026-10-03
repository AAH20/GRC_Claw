import { test, expect } from '@playwright/test';

test.describe('Notifications Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Notifications');
    await page.waitForURL(/.*notifications/);
  });

  test('should display notifications page', async ({ page }) => {
    await expect(page).toHaveURL(/.*notifications/);
    await expect(page.locator('h1')).toContainText('Notifications');
  });

  test('should display notification list', async ({ page }) => {
    await expect(page.locator('[data-testid="notification-list"]')).toBeVisible();
  });

  test('should have mark all as read button', async ({ page }) => {
    await expect(page.locator('button:has-text("Mark all as read")')).toBeVisible();
  });
});
