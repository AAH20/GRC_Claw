import { test, expect, Page } from '@playwright/test';
import {
  authenticate,
  expectToast,
  safeClick,
  uniqueId,
  waitForPageReady,
  TEST_MODERATION_CONTENT,
} from './helpers';

test.describe('Content Moderation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await authenticate(page);
    await page.goto('/moderation');
    await waitForPageReady(page);
  });

  test('should display moderation queue page', async ({ page }) => {
    await expect(page).toHaveURL(/\/moderation/);
    await expect(
      page.getByRole('heading', { name: /moderation|moderation queue/i }),
    ).toBeVisible();
  });

  test('should submit content for moderation', async ({ page }) => {
    // Navigate to content submission
    await page.goto('/moderation/submit');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /submit content|moderation submit|new content/i }),
    ).toBeVisible();

    // Fill in content submission form
    await page.getByLabel(/content|text|message/i).fill(TEST_MODERATION_CONTENT.content);

    // Select content type
    const typeSelect = page.getByLabel(/content type|type/i);
    if (await typeSelect.isVisible()) {
      await typeSelect.selectOption(TEST_MODERATION_CONTENT.contentType);
    }

    // Submit for moderation
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();

    // Verify submission was processed
    await expectToast(page, /submitted|processed|queued/i);
  });

  test('should view moderation queue items', async ({ page }) => {
    // Submit content first
    await page.goto('/moderation/submit');
    await waitForPageReady(page);
    await page.getByLabel(/content|text|message/i).fill(uniqueId('moderate'));
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();
    await expectToast(page, /submitted|processed|queued/i);

    // Navigate to queue
    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    // Verify queue has items
    const queueItems = page.locator('[data-testid="queue-item"], [data-testid="moderation-item"], tbody tr');
    await expect(queueItems.first()).toBeVisible({ timeout: 10_000 });
  });

  test('should filter moderation queue by status', async ({ page }) => {
    // Submit content to ensure queue has items
    await page.goto('/moderation/submit');
    await waitForPageReady(page);
    await page.getByLabel(/content|text|message/i).fill('Filter test content');
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();
    await expectToast(page, /submitted|processed|queued/i);

    // Navigate to queue
    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    // Filter by status
    const statusFilter = page.getByLabel(/status|filter by status/i);
    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('pending');
      // Should show pending items
      await expect(
        page.locator('[data-testid="queue-item"], tbody tr').first(),
      ).toBeVisible();

      await statusFilter.selectOption('resolved');
      // Should show resolved items or empty state
    }
  });

  test('should filter moderation queue by priority', async ({ page }) => {
    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    const priorityFilter = page.getByLabel(/priority|filter by priority/i);
    if (await priorityFilter.isVisible()) {
      await priorityFilter.selectOption('high');
      // Verify filter applied
      await expect(priorityFilter).toHaveValue('high');

      await priorityFilter.selectOption('critical');
      await expect(priorityFilter).toHaveValue('critical');
    }
  });

  test('should resolve a moderation queue item', async ({ page }) => {
    // Submit content
    await page.goto('/moderation/submit');
    await waitForPageReady(page);
    await page.getByLabel(/content|text|message/i).fill('Content to resolve');
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();
    await expectToast(page, /submitted|processed|queued/i);

    // Navigate to queue
    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    // Click on first queue item
    const firstItem = page.locator('[data-testid="queue-item"], tbody tr').first();
    await firstItem.click();
    await waitForPageReady(page);

    // Resolve the item
    const resolveButton = page.getByRole('button', { name: /resolve|approve|dismiss/i });
    if (await resolveButton.isVisible({ timeout: 5_000 })) {
      await resolveButton.click();

      // Select resolution decision if prompted
      const decisionSelect = page.getByLabel(/decision|resolution/i);
      if (await decisionSelect.isVisible({ timeout: 3_000 })) {
        await decisionSelect.selectOption('approve');
      }

      await page.getByRole('button', { name: /confirm|submit/i }).click();
      await expectToast(page, /resolved|approved|completed/i);
    }
  });

  test('should escalate a moderation item', async ({ page }) => {
    // Submit content
    await page.goto('/moderation/submit');
    await waitForPageReady(page);
    await page.getByLabel(/content|text|message/i).fill('Content to escalate');
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();
    await expectToast(page, /submitted|processed|queued/i);

    // Navigate to queue
    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    // Click on first queue item
    const firstItem = page.locator('[data-testid="queue-item"], tbody tr').first();
    await firstItem.click();
    await waitForPageReady(page);

    // Escalate the item
    const escalateButton = page.getByRole('button', { name: /escalate|flag|report/i });
    if (await escalateButton.isVisible({ timeout: 5_000 })) {
      await escalateButton.click();

      // Fill escalation reason if prompted
      const reasonInput = page.getByLabel(/reason|notes|comment/i);
      if (await reasonInput.isVisible({ timeout: 3_000 })) {
        await reasonInput.fill('Requires senior moderator review');
      }

      await page.getByRole('button', { name: /confirm|submit|escalate/i }).click();
      await expectToast(page, /escalated|flagged|reported/i);
    }
  });

  test('should view moderation statistics', async ({ page }) => {
    await page.goto('/moderation/stats');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /statistics|stats|metrics|analytics/i }),
    ).toBeVisible();

    // Verify stat cards are visible
    const statCards = page.locator('[data-testid="stat-card"], .stat-card, .metric-card');
    const count = await statCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should handle moderation API failure gracefully', async ({ page }) => {
    // Intercept moderation API and force failure
    await page.route('**/api/v1/moderation/**', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Moderation service unavailable' }),
      }),
    );

    await page.goto('/moderation/queue');
    await waitForPageReady(page);

    // Should show error state
    await expect(
      page.getByText(/error|failed|unavailable|something went wrong/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('should validate content submission form', async ({ page }) => {
    await page.goto('/moderation/submit');
    await waitForPageReady(page);

    // Try to submit empty content
    await page.getByRole('button', { name: /submit|moderate|send/i }).click();

    // Should show validation error
    await expect(
      page.getByText(/content is required|content.*required|cannot be empty/i),
    ).toBeVisible({ timeout: 5_000 });
  });
});
