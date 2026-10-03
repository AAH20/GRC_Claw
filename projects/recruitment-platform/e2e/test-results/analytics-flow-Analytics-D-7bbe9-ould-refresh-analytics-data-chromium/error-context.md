# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics-flow.spec.ts >> Analytics Dashboard Flow >> should refresh analytics data
- Location: tests/analytics-flow.spec.ts:145:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/dashboard/
Received string:  "http://localhost:3000/login"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    14 × locator resolved to <html lang="en">…</html>
       - unexpected value "http://localhost:3000/login"

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- alert
- img
- heading "Welcome Back" [level=3]
- paragraph: Sign in to your RecruitHub account
- text: Not Found Email
- img
- textbox "Email":
  - /placeholder: you@company.com
  - text: admin@example.com
- text: Password
- img
- textbox "Password":
  - /placeholder: Enter your password
  - text: admin123
- button "Sign In"
- paragraph:
  - text: Don't have an account?
  - link "Sign up":
    - /url: /register
```

# Test source

```ts
  1   | import { test, expect, Page } from "@playwright/test";
  2   | 
  3   | /**
  4   |  * Analytics Dashboard Flow E2E Tests
  5   |  *
  6   |  * Covers analytics dashboard views, charts, data filtering,
  7   |  * export functionality, and KPI verification.
  8   |  */
  9   | 
  10  | async function loginAndNavigateToAnalytics(page: Page): Promise<void> {
  11  |   await page.goto("/login");
  12  |   await page.getByLabel("Email").fill("admin@example.com");
  13  |   await page.getByLabel("Password").fill("admin123");
  14  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
> 15  |   await expect(page).toHaveURL(/\/dashboard/);
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  16  |   await page.getByRole("link", { name: /analytics|reports|insights/i }).click();
  17  |   await expect(page).toHaveURL(/\/analytics/);
  18  | }
  19  | 
  20  | test.describe("Analytics Dashboard Flow", () => {
  21  |   test.beforeEach(async ({ page }) => {
  22  |     await loginAndNavigateToAnalytics(page);
  23  |   });
  24  | 
  25  |   test("should display analytics dashboard page", async ({ page }) => {
  26  |     await expect(
  27  |       page.getByRole("heading", { name: /analytics|dashboard|reports/i }).first()
  28  |     ).toBeVisible();
  29  |   });
  30  | 
  31  |   test("should display KPI cards with metrics", async ({ page }) => {
  32  |     // Verify key metric cards are visible
  33  |     const kpiLabels = [
  34  |       /total candidates/i,
  35  |       /total jobs/i,
  36  |       /total applications/i,
  37  |       /total interviews/i,
  38  |       /hire rate/i,
  39  |       /avg time to hire/i,
  40  |     ];
  41  | 
  42  |     for (const label of kpiLabels) {
  43  |       await expect(page.getByText(label).first()).toBeVisible();
  44  |     }
  45  |   });
  46  | 
  47  |   test("should display applications by month chart", async ({ page }) => {
  48  |     await expect(
  49  |       page.getByText(/applications by month|monthly applications/i).first()
  50  |     ).toBeVisible();
  51  |     // Chart container should be visible
  52  |     await expect(page.locator("[data-testid='chart-applications-by-month']").first()).toBeVisible();
  53  |   });
  54  | 
  55  |   test("should display candidates by status chart", async ({ page }) => {
  56  |     await expect(
  57  |       page.getByText(/candidates by status|status breakdown/i).first()
  58  |     ).toBeVisible();
  59  |     await expect(page.locator("[data-testid='chart-candidates-by-status']").first()).toBeVisible();
  60  |   });
  61  | 
  62  |   test("should display jobs by department chart", async ({ page }) => {
  63  |     await expect(
  64  |       page.getByText(/jobs by department|department breakdown/i).first()
  65  |     ).toBeVisible();
  66  |     await expect(page.locator("[data-testid='chart-jobs-by-department']").first()).toBeVisible();
  67  |   });
  68  | 
  69  |   test("should display source breakdown chart", async ({ page }) => {
  70  |     await expect(
  71  |       page.getByText(/source breakdown|sources/i).first()
  72  |     ).toBeVisible();
  73  |     await expect(page.locator("[data-testid='chart-source-breakdown']").first()).toBeVisible();
  74  |   });
  75  | 
  76  |   test("should filter analytics by date range", async ({ page }) => {
  77  |     // Set date range filter
  78  |     await page.getByLabel("Start Date").fill("2026-01-01");
  79  |     await page.getByLabel("End Date").fill("2026-12-31");
  80  |     await page.getByRole("button", { name: /apply|filter|update/i }).click();
  81  | 
  82  |     // Verify data is still displayed
  83  |     await expect(
  84  |       page.getByText(/total candidates|total jobs/i).first()
  85  |     ).toBeVisible();
  86  |   });
  87  | 
  88  |   test("should filter analytics by department", async ({ page }) => {
  89  |     // Filter by department
  90  |     await page.getByLabel("Department").selectOption("Engineering");
  91  |     await page.getByRole("button", { name: /apply|filter|update/i }).click();
  92  | 
  93  |     // Verify data is displayed
  94  |     await expect(
  95  |       page.getByText(/total candidates|total jobs/i).first()
  96  |     ).toBeVisible();
  97  |   });
  98  | 
  99  |   test("should export analytics data", async ({ page }) => {
  100 |     // Click export button
  101 |     const downloadPromise = page.waitForEvent("download");
  102 |     await page.getByRole("button", { name: /export|download/i }).click();
  103 |     const download = await downloadPromise;
  104 | 
  105 |     // Verify download started
  106 |     expect(download.suggestedFilename()).toMatch(/\.(csv|xlsx|pdf|json)$/);
  107 |   });
  108 | 
  109 |   test("should display recruitment funnel visualization", async ({ page }) => {
  110 |     await expect(
  111 |       page.getByText(/funnel|pipeline|conversion/i).first()
  112 |     ).toBeVisible();
  113 |   });
  114 | 
  115 |   test("should display time-to-hire trend", async ({ page }) => {
```