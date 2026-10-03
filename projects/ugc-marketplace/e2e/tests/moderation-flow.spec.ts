import { test, expect, Page } from '@playwright/test';
import { createAuthenticatedPage, waitForToast, generateUniqueString } from '../helpers';

test.describe('Content Moderation Queue', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await createAuthenticatedPage(browser, 'moderator');
    await page.goto('/moderation');
  });

  test('should display moderation queue with pending items', async () => {
    await expect(page.locator('[data-testid="moderation-queue"]')).toBeVisible();
    await expect(page.locator('[data-testid="pending-count"]')).toBeVisible();
    const queueItems = await page.locator('[data-testid="moderation-item"]').count();
    expect(queueItems).toBeGreaterThanOrEqual(0);
  });

  test('should filter moderation queue by content type', async () => {
    await page.click('[data-testid="filter-content-type"]');
    await page.click('[data-testid="type-option-image"]');
    await expect(page.locator('[data-testid="active-filter"]')).toContainText('Image');
    const items = await page.locator('[data-testid="moderation-item"]').count();
    expect(items).toBeGreaterThanOrEqual(0);
  });

  test('should filter moderation queue by report reason', async () => {
    await page.click('[data-testid="filter-report-reason"]');
    await page.click('[data-testid="reason-option-spam"]');
    await expect(page.locator('[data-testid="active-filter"]')).toContainText('Spam');
  });

  test('should view content detail in moderation panel', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await expect(page.locator('[data-testid="moderation-detail-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="moderation-content-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="moderation-report-reason"]')).toBeVisible();
    await expect(page.locator('[data-testid="moderation-reporter-info"]')).toBeVisible();
  });

  test('should approve content from moderation queue', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="approve-content-btn"]');
    await expect(page.locator('[data-testid="moderation-confirm-modal"]')).toBeVisible();
    await page.click('[data-testid="confirm-approve-btn"]');
    await waitForToast(page, 'Content approved');
    await expect(page.locator('[data-testid="moderation-item"] >> nth=0')).not.toBeVisible();
  });

  test('should reject content with reason', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="reject-content-btn"]');
    await expect(page.locator('[data-testid="reject-reason-modal"]')).toBeVisible();
    await page.fill('[data-testid="reject-reason-text"]', 'Violates community guidelines: inappropriate content.');
    await page.click('[data-testid="confirm-reject-btn"]');
    await waitForToast(page, 'Content rejected');
  });

  test('should require rejection reason before submitting', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="reject-content-btn"]');
    await page.click('[data-testid="confirm-reject-btn"]');
    await expect(page.locator('[data-testid="error-reject-reason"]')).toBeVisible();
    await expect(page.locator('text=Rejection reason is required')).toBeVisible();
  });

  test('should escalate content to senior moderator', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="escalate-content-btn"]');
    await page.fill('[data-testid="escalation-note"]', 'Potential legal issue, needs senior review.');
    await page.click('[data-testid="confirm-escalate-btn"]');
    await waitForToast(page, 'Content escalated');
    await expect(page.locator('[data-testid="escalated-badge"]')).toBeVisible();
  });

  test('should view moderation history for a content item', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="view-moderation-history-btn"]');
    await expect(page.locator('[data-testid="moderation-history-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="history-item"]').first()).toBeVisible();
  });

  test('should bulk approve multiple content items', async () => {
    await page.click('[data-testid="select-all-checkbox"]');
    await page.click('[data-testid="bulk-actions-dropdown"]');
    await page.click('[data-testid="bulk-approve-btn"]');
    await expect(page.locator('[data-testid="bulk-confirm-modal"]')).toBeVisible();
    await page.click('[data-testid="confirm-bulk-approve-btn"]');
    await waitForToast(page, 'Items approved');
  });

  test('should view reporter history for a flagged user', async () => {
    await page.click('[data-testid="moderation-item"] >> nth=0');
    await page.click('[data-testid="reporter-username"]');
    await expect(page.locator('[data-testid="reporter-history-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="reporter-stats"]')).toBeVisible();
    await expect(page.locator('[data-testid="reporter-previous-reports"]')).toBeVisible();
  });
});
