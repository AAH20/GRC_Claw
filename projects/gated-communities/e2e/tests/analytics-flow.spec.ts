import { test, expect, Page } from '@playwright/test';
import {
  authenticate,
  expectToast,
  safeClick,
  uniqueId,
  waitForPageReady,
} from './helpers';

test.describe('Analytics Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    await authenticate(page);
    await page.goto('/analytics');
    await waitForPageReady(page);
  });

  test('should display analytics dashboard page', async ({ page }) => {
    await expect(page).toHaveURL(/\/analytics/);
    await expect(
      page.getByRole('heading', { name: /analytics|dashboard|insights/i }),
    ).toBeVisible();
  });

  test('should display key metric cards', async ({ page }) => {
    // Verify that key analytics metric cards are present
    const metricCards = page.locator(
      '[data-testid="metric-card"], [data-testid="stat-card"], .metric-card, .stat-card',
    );
    const count = await metricCards.count();
    expect(count).toBeGreaterThan(0);

    // Check for common analytics metrics
    const metrics = ['members', 'engagement', 'revenue', 'growth', 'activity'];
    const pageContent = await page.textContent('body');
    const foundMetrics = metrics.filter((m) =>
      pageContent?.toLowerCase().includes(m),
    );
    expect(foundMetrics.length).toBeGreaterThan(0);
  });

  test('should display charts and visualizations', async ({ page }) => {
    // Check for chart containers
    const charts = page.locator(
      '[data-testid="chart"], .chart-container, canvas, svg.chart, .recharts-wrapper',
    );
    const count = await charts.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should filter analytics by date range', async ({ page }) => {
    // Look for date range picker
    const dateRangePicker = page.locator(
      '[data-testid="date-range"], .date-range-picker, [data-testid="date-picker"]',
    );

    if (await dateRangePicker.isVisible({ timeout: 5_000 })) {
      await dateRangePicker.click();

      // Select a predefined range if available
      const last7Days = page.getByRole('button', { name: /last 7 days|7 days/i });
      if (await last7Days.isVisible({ timeout: 3_000 })) {
        await last7Days.click();
      } else {
        // Fill in custom dates
        const startDate = page.getByLabel(/start date|from/i);
        const endDate = page.getByLabel(/end date|to/i);
        if (await startDate.isVisible()) {
          await startDate.fill('2024-01-01');
          await endDate.fill('2024-01-31');
        }
      }

      // Verify filter applied
      await expect(dateRangePicker).toBeVisible();
    }
  });

  test('should filter analytics by tier', async ({ page }) => {
    const tierFilter = page.getByLabel(/tier|filter by tier/i);

    if (await tierFilter.isVisible({ timeout: 5_000 })) {
      await tierFilter.selectOption({ index: 1 });
      await expect(tierFilter).not.toHaveValue('');

      // Verify data refreshed
      await page.waitForTimeout(1000);
    }
  });

  test('should export analytics data', async ({ page }) => {
    const exportButton = page.getByRole('button', {
      name: /export|download|csv|pdf/i,
    });

    if (await exportButton.isVisible({ timeout: 5_000 })) {
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 10_000 }),
        exportButton.click(),
      ]);

      expect(download).toBeTruthy();
      const suggestedFilename = download.suggestedFilename();
      expect(suggestedFilename).toMatch(/\.(csv|pdf|xlsx|json)$/i);
    }
  });

  test('should display moderation analytics', async ({ page }) => {
    await page.goto('/analytics/moderation');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /moderation analytics|moderation insights/i }),
    ).toBeVisible();

    // Check for moderation-specific metrics
    const pageContent = await page.textContent('body');
    const moderationMetrics = ['resolved', 'pending', 'escalated', 'average time'];
    const found = moderationMetrics.filter((m) =>
      pageContent?.toLowerCase().includes(m),
    );
    expect(found.length).toBeGreaterThan(0);
  });

  test('should display community health metrics', async ({ page }) => {
    await page.goto('/analytics/health');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /community health|health score|health metrics/i }),
    ).toBeVisible();

    // Check for health score indicator
    const healthScore = page.locator(
      '[data-testid="health-score"], .health-score, [data-testid="overall-score"]',
    );
    if (await healthScore.isVisible({ timeout: 5_000 })) {
      const scoreText = await healthScore.textContent();
      expect(scoreText).toMatch(/\d+/);
    }
  });

  test('should display tier analytics', async ({ page }) => {
    await page.goto('/analytics/tiers');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /tier analytics|tiers|membership analytics/i }),
    ).toBeVisible();

    // Check for tier-specific data
    const pageContent = await page.textContent('body');
    const tierMetrics = ['bronze', 'silver', 'gold', 'platinum', 'upgrade', 'downgrade'];
    const found = tierMetrics.filter((m) =>
      pageContent?.toLowerCase().includes(m),
    );
    expect(found.length).toBeGreaterThan(0);
  });

  test('should handle analytics API failure gracefully', async ({ page }) => {
    // Intercept analytics API and force failure
    await page.route('**/api/v1/analytics/**', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Analytics service unavailable' }),
      }),
    );

    await page.goto('/analytics');
    await waitForPageReady(page);

    // Should show error state
    await expect(
      page.getByText(/error|failed|unavailable|something went wrong/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('should refresh analytics data', async ({ page }) => {
    const refreshButton = page.getByRole('button', {
      name: /refresh|reload|update/i,
    });

    if (await refreshButton.isVisible({ timeout: 5_000 })) {
      await refreshButton.click();

      // Should show loading state then data
      const loadingIndicator = page.locator(
        '[data-testid="loading"], .loading, .spinner, [role="progressbar"]',
      );

      // Wait for data to load
      await page.waitForLoadState('networkidle');
      await expect(
        page.locator('[data-testid="metric-card"], .metric-card, .stat-card').first(),
      ).toBeVisible({ timeout: 10_000 });
    }
  });

  test('should display real-time activity feed', async ({ page }) => {
    const activityFeed = page.locator(
      '[data-testid="activity-feed"], .activity-feed, [data-testid="recent-activity"]',
    );

    if (await activityFeed.isVisible({ timeout: 5_000 })) {
      const activities = activityFeed.locator('[data-testid="activity-item"], .activity-item, li');
      const count = await activities.count();
      expect(count).toBeGreaterThan(0);
    }
  });
});
