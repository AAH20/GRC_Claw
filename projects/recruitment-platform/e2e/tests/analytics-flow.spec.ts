import { test, expect, Page } from "@playwright/test";

/**
 * Analytics Dashboard Flow E2E Tests
 *
 * Covers analytics dashboard views, charts, data filtering,
 * export functionality, and KPI verification.
 */

async function loginAndNavigateToAnalytics(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@example.com");
  await page.getByLabel("Password").fill("admin123");
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await page.getByRole("link", { name: /analytics|reports|insights/i }).click();
  await expect(page).toHaveURL(/\/analytics/);
}

test.describe("Analytics Dashboard Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToAnalytics(page);
  });

  test("should display analytics dashboard page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /analytics|dashboard|reports/i }).first()
    ).toBeVisible();
  });

  test("should display KPI cards with metrics", async ({ page }) => {
    // Verify key metric cards are visible
    const kpiLabels = [
      /total candidates/i,
      /total jobs/i,
      /total applications/i,
      /total interviews/i,
      /hire rate/i,
      /avg time to hire/i,
    ];

    for (const label of kpiLabels) {
      await expect(page.getByText(label).first()).toBeVisible();
    }
  });

  test("should display applications by month chart", async ({ page }) => {
    await expect(
      page.getByText(/applications by month|monthly applications/i).first()
    ).toBeVisible();
    // Chart container should be visible
    await expect(page.locator("[data-testid='chart-applications-by-month']").first()).toBeVisible();
  });

  test("should display candidates by status chart", async ({ page }) => {
    await expect(
      page.getByText(/candidates by status|status breakdown/i).first()
    ).toBeVisible();
    await expect(page.locator("[data-testid='chart-candidates-by-status']").first()).toBeVisible();
  });

  test("should display jobs by department chart", async ({ page }) => {
    await expect(
      page.getByText(/jobs by department|department breakdown/i).first()
    ).toBeVisible();
    await expect(page.locator("[data-testid='chart-jobs-by-department']").first()).toBeVisible();
  });

  test("should display source breakdown chart", async ({ page }) => {
    await expect(
      page.getByText(/source breakdown|sources/i).first()
    ).toBeVisible();
    await expect(page.locator("[data-testid='chart-source-breakdown']").first()).toBeVisible();
  });

  test("should filter analytics by date range", async ({ page }) => {
    // Set date range filter
    await page.getByLabel("Start Date").fill("2026-01-01");
    await page.getByLabel("End Date").fill("2026-12-31");
    await page.getByRole("button", { name: /apply|filter|update/i }).click();

    // Verify data is still displayed
    await expect(
      page.getByText(/total candidates|total jobs/i).first()
    ).toBeVisible();
  });

  test("should filter analytics by department", async ({ page }) => {
    // Filter by department
    await page.getByLabel("Department").selectOption("Engineering");
    await page.getByRole("button", { name: /apply|filter|update/i }).click();

    // Verify data is displayed
    await expect(
      page.getByText(/total candidates|total jobs/i).first()
    ).toBeVisible();
  });

  test("should export analytics data", async ({ page }) => {
    // Click export button
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: /export|download/i }).click();
    const download = await downloadPromise;

    // Verify download started
    expect(download.suggestedFilename()).toMatch(/\.(csv|xlsx|pdf|json)$/);
  });

  test("should display recruitment funnel visualization", async ({ page }) => {
    await expect(
      page.getByText(/funnel|pipeline|conversion/i).first()
    ).toBeVisible();
  });

  test("should display time-to-hire trend", async ({ page }) => {
    await expect(
      page.getByText(/time to hire|time-to-hire/i).first()
    ).toBeVisible();
  });

  test("should display diversity metrics", async ({ page }) => {
    await expect(
      page.getByText(/diversity|inclusion/i).first()
    ).toBeVisible();
  });

  test("should display cost analysis", async ({ page }) => {
    await expect(
      page.getByText(/cost|expense|budget/i).first()
    ).toBeVisible();
  });

  test("should handle empty analytics data gracefully", async ({ page }) => {
    // Filter by a date range with no data
    await page.getByLabel("Start Date").fill("2020-01-01");
    await page.getByLabel("End Date").fill("2020-01-31");
    await page.getByRole("button", { name: /apply|filter|update/i }).click();

    // Should show empty state or zero values
    await expect(
      page.getByText(/no data|empty|zero|0/i).first()
    ).toBeVisible();
  });

  test("should refresh analytics data", async ({ page }) => {
    // Click refresh button
    await page.getByRole("button", { name: /refresh|reload/i }).click();

    // Verify data is still displayed
    await expect(
      page.getByText(/total candidates|total jobs/i).first()
    ).toBeVisible();
  });
});
