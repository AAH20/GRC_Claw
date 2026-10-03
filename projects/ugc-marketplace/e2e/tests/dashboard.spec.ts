import { test, expect } from '@playwright/test';

test.describe('Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
  });

  test('should display dashboard page', async ({ page }) => {
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should display navigation sidebar', async ({ page }) => {
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('text=Listings')).toBeVisible();
    await expect(page.locator('text=Content')).toBeVisible();
    await expect(page.locator('text=Transactions')).toBeVisible();
    await expect(page.locator('text=Creators')).toBeVisible();
    await expect(page.locator('text=Analytics')).toBeVisible();
  });

  test('should display header with user info', async ({ page }) => {
    await expect(page.locator('header')).toBeVisible();
  });

  test('should navigate to listings page', async ({ page }) => {
    await page.click('text=Listings');
    await expect(page).toHaveURL(/.*listings/);
  });

  test('should navigate to content page', async ({ page }) => {
    await page.click('text=Content');
    await expect(page).toHaveURL(/.*content/);
  });

  test('should navigate to transactions page', async ({ page }) => {
    await page.click('text=Transactions');
    await expect(page).toHaveURL(/.*transactions/);
  });

  test('should navigate to creators page', async ({ page }) => {
    await page.click('text=Creators');
    await expect(page).toHaveURL(/.*creators/);
  });

  test('should navigate to analytics page', async ({ page }) => {
    await page.click('text=Analytics');
    await expect(page).toHaveURL(/.*analytics/);
  });

  test('should navigate to moderation page', async ({ page }) => {
    await page.click('text=Moderation');
    await expect(page).toHaveURL(/.*moderation/);
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.click('text=Settings');
    await expect(page).toHaveURL(/.*settings/);
  });

  test('should navigate to profile page', async ({ page }) => {
    await page.click('text=Profile');
    await expect(page).toHaveURL(/.*profile/);
  });

  test('should navigate to notifications page', async ({ page }) => {
    await page.click('text=Notifications');
    await expect(page).toHaveURL(/.*notifications/);
  });
});
