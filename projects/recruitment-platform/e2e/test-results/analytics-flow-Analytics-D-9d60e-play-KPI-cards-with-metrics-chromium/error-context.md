# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics-flow.spec.ts >> Analytics Dashboard Flow >> should display KPI cards with metrics
- Location: tests/analytics-flow.spec.ts:31:7

# Error details

```
TimeoutError: locator.fill: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Email')

```

# Page snapshot

```yaml
- generic:
  - generic [active]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - navigation [ref=e6]:
          - button [disabled] [ref=e7]:
            - img "previous" [ref=e8]
          - generic [ref=e10]:
            - generic [ref=e11]: 1/
            - generic [ref=e12]: "1"
          - button [disabled] [ref=e13]:
            - img "next" [ref=e14]
        - generic [ref=e17]:
          - generic "Latest available version is detected (16.3.8)." [ref=e20]: Next.js 16.3.8
          - generic [ref=e21]: Turbopack
      - dialog "Runtime Error" [ref=e23]:
        - generic [ref=e26]:
          - generic [ref=e28]:
            - generic [ref=e29]:
              - generic [ref=e30]: Runtime Error
              - generic [ref=e32]:
                - button "Copy Error Info" [ref=e33] [cursor=pointer]
                - button "No related documentation found" [disabled] [ref=e36]
                - button "Attach Node.js inspector" [ref=e39] [cursor=pointer]
            - generic [ref=e48]: The default export is not a React Component in "/login/layout"
          - generic [ref=e52]:
            - paragraph [ref=e53]:
              - text: Call Stack
              - generic [ref=e54]: "24"
            - button "Show 24 ignore-listed frame(s)" [ref=e55] [cursor=pointer]
      - contentinfo [ref=e58]:
        - region "Error feedback" [ref=e59]:
          - paragraph [ref=e60]:
            - link "Was this helpful?" [ref=e61] [cursor=pointer]:
              - /url: https://nextjs.org/telemetry#error-feedback
          - button "Mark as helpful" [ref=e62] [cursor=pointer]
          - button "Mark as not helpful" [ref=e66] [cursor=pointer]
    - generic [ref=e73] [cursor=pointer]:
      - button "Open Next.js Dev Tools" [ref=e74]
      - generic [ref=e78]:
        - button "Open issues overlay" [ref=e79]:
          - generic [ref=e80]:
            - generic [aria-hidden] [ref=e81]: "0"
            - generic [ref=e82]: "1"
          - generic [ref=e83]: Issue
        - button "Collapse issues badge" [ref=e84]
  - alert [ref=e87]
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
> 12  |   await page.getByLabel("Email").fill("admin@example.com");
      |                                  ^ TimeoutError: locator.fill: Timeout 15000ms exceeded.
  13  |   await page.getByLabel("Password").fill("admin123");
  14  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
  15  |   await expect(page).toHaveURL(/\/dashboard/);
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
```