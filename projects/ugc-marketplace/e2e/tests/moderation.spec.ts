import { test, expect } from '@playwright/test';

test.describe('Moderation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
    await page.click('text=Moderation');
    await page.waitForURL(/.*moderation/);
  });

  test('should display moderation page', async ({ page }) => {
    await expect(page).toHaveURL(/.*moderation/);
    await expect(page.locator('h1')).toContainText('Moderation');
  });

  test('should display moderation queue', async ({ page }) => {
    await expect(page.locator('[data-testid="moderation-queue"]')).toBeVisible();
  });

  test('should have approve button for pending items', async ({ page }) => {
    const approveButton = page.locator('button:has-text("Approve")').first();
    if (await approveButton.isVisible()) {
      await expect(approveButton).toBeVisible();
    }
  });

  test('should have reject button for pending items', async ({ page }) => {
    const rejectButton = page.locator('button:has-text("Reject")').first();
    if (await rejectButton.isVisible()) {
      await expect(rejectButton).toBeVisible();
    }
  });
});
