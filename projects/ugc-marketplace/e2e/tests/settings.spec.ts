import { test, expect } from '@playwright/test';

test.describe('Settings Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Settings');
    await page.waitForURL(/.*settings/);
  });

  test('should display settings page', async ({ page }) => {
    await expect(page).toHaveURL(/.*settings/);
    await expect(page.locator('h1')).toContainText('Settings');
  });

  test('should display settings tabs', async ({ page }) => {
    await expect(page.locator('text=Profile')).toBeVisible();
    await expect(page.locator('text=Notifications')).toBeVisible();
    await expect(page.locator('text=Security')).toBeVisible();
  });

  test('should display profile settings form', async ({ page }) => {
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
  });

  test('should save profile settings', async ({ page }) => {
    await page.fill('input[name="name"]', 'Test User');
    await page.click('button:has-text("Save")');
    await expect(page.locator('text=Settings saved')).toBeVisible();
  });
});
