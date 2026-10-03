import { test, expect } from '@playwright/test';

test.describe('Profile Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Profile');
    await page.waitForURL(/.*profile/);
  });

  test('should display profile page', async ({ page }) => {
    await expect(page).toHaveURL(/.*profile/);
    await expect(page.locator('h1')).toContainText('Profile');
  });

  test('should display user avatar', async ({ page }) => {
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test('should display user name', async ({ page }) => {
    await expect(page.locator('[data-testid="user-name"]')).toBeVisible();
  });

  test('should display user bio', async ({ page }) => {
    await expect(page.locator('[data-testid="user-bio"]')).toBeVisible();
  });

  test('should have edit profile button', async ({ page }) => {
    await expect(page.locator('button:has-text("Edit Profile")')).toBeVisible();
  });
});
