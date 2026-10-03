import { test, expect, Page } from '@playwright/test';
import { loginAs, waitForToast } from '../helpers';

test.describe('Admin Moderation and User Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await loginAs(page, 'admin');
  });

  test('should access admin dashboard', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.getByTestId('admin-dashboard')).toBeVisible();
    await expect(page.getByTestId('stats-cards')).toBeVisible();
    await expect(page.getByTestId('recent-reports')).toBeVisible();
  });

  test('should view reported content queue', async ({ page }) => {
    await page.goto('/admin/moderation');
    const queue = page.getByTestId('moderation-queue');
    await expect(queue).toBeVisible();
    const items = page.getByTestId('moderation-item');
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should approve reported content', async ({ page }) => {
    await page.goto('/admin/moderation');
    const firstItem = page.getByTestId('moderation-item').first();
    const contentId = await firstItem.getAttribute('data-content-id');
    await firstItem.getByTestId('approve-content').click();
    await waitForToast(page, 'Content approved');
    await expect(page.getByTestId('moderation-item').filter({ has: page.locator(`[data-content-id="${contentId}"]`) })).not.toBeVisible();
  });

  test('should reject reported content with reason', async ({ page }) => {
    await page.goto('/admin/moderation');
    const firstItem = page.getByTestId('moderation-item').first();
    await firstItem.getByTestId('reject-content').click();
    await page.getByTestId('reject-reason').fill('Violates community guidelines');
    await page.getByTestId('confirm-reject').click();
    await waitForToast(page, 'Content rejected');
  });

  test('should view user management list', async ({ page }) => {
    await page.goto('/admin/users');
    const users = page.getByTestId('user-row');
    await expect(users.first()).toBeVisible();
    const count = await users.count();
    expect(count).toBeGreaterThan(0);
    await expect(users.first()).toContainText('@');
  });

  test('should suspend a user account', async ({ page }) => {
    await page.goto('/admin/users');
    const userRow = page.getByTestId('user-row').first();
    const username = await userRow.getByTestId('username').textContent();
    await userRow.getByTestId('suspend-user').click();
    await page.getByTestId('suspend-reason').fill('Violation of terms of service');
    await page.getByTestId('confirm-suspend').click();
    await waitForToast(page, 'User suspended');
    await expect(page.getByTestId('user-row').filter({ hasText: username ?? '' }).getByTestId('user-status')).toContainText('Suspended');
  });

  test('should reactivate a suspended user', async ({ page }) => {
    await page.goto('/admin/users');
    const suspendedRow = page.getByTestId('user-row').filter({ has: page.getByTestId('user-status').filter({ hasText: 'Suspended' }) }).first();
    await suspendedRow.getByTestId('reactivate-user').click();
    await page.getByTestId('confirm-reactivate').click();
    await waitForToast(page, 'User reactivated');
    await expect(suspendedRow.getByTestId('user-status')).toContainText('Active');
  });

  test('should view platform analytics', async ({ page }) => {
    await page.goto('/admin/analytics');
    await expect(page.getByTestId('revenue-chart')).toBeVisible();
    await expect(page.getByTestId('user-growth-chart')).toBeVisible();
    await expect(page.getByTestId('content-stats')).toBeVisible();
    await expect(page.getByTestId('total-revenue')).toBeVisible();
    await expect(page.getByTestId('total-users')).toBeVisible();
  });

  test('should search users by email or username', async ({ page }) => {
    await page.goto('/admin/users');
    await page.getByTestId('user-search').fill('testuser');
    await page.getByTestId('user-search-submit').click();
    const rows = page.getByTestId('user-row');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const text = await rows.nth(i).textContent();
      expect(text).toMatch(/testuser/i);
    }
  });

  test('should view content details in moderation', async ({ page }) => {
    await page.goto('/admin/moderation');
    await page.getByTestId('moderation-item').first().getByTestId('view-content').click();
    await expect(page.getByTestId('content-detail-modal')).toBeVisible();
    await expect(page.getByTestId('content-preview')).toBeVisible();
    await expect(page.getByTestId('report-reason')).toBeVisible();
    await expect(page.getByTestId('reporter-info')).toBeVisible();
  });

  test('should bulk approve multiple content items', async ({ page }) => {
    await page.goto('/admin/moderation');
    const items = page.getByTestId('moderation-item');
    const count = Math.min(3, await items.count());
    for (let i = 0; i < count; i++) {
      await page.getByTestId('moderation-item').nth(i).getByTestId('select-checkbox').check();
    }
    await page.getByTestId('bulk-approve').click();
    await page.getByTestId('confirm-bulk-action').click();
    await waitForToast(page, `${count} items approved`);
  });

  test('should export user data', async ({ page }) => {
    await page.goto('/admin/users');
    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('export-users').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('users');
  });
});
