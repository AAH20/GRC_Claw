import { test, expect } from '@playwright/test';

test.describe('Content Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Content');
    await page.waitForURL(/.*content/);
  });

  test('should display content page', async ({ page }) => {
    await expect(page).toHaveURL(/.*content/);
    await expect(page.locator('h1')).toContainText('Content');
  });

  test('should display content grid', async ({ page }) => {
    await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  });

  test('should display content cards', async ({ page }) => {
    await expect(page.locator('[data-testid="content-card"]').first()).toBeVisible();
  });

  test('should have create content button', async ({ page }) => {
    await expect(page.locator('button:has-text("Create Content")')).toBeVisible();
  });

  test('should filter content by type', async ({ page }) => {
    await page.selectOption('select[name="type"]', 'video');
    await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  });

  test('should filter content by status', async ({ page }) => {
    await page.selectOption('select[name="status"]', 'published');
    await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  });

  test('should search content', async ({ page }) => {
    await page.fill('input[name="search"]', 'test');
    await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  });
});
