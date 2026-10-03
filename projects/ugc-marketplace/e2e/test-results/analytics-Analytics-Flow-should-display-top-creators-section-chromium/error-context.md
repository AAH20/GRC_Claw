# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics.spec.ts >> Analytics Flow >> should display top creators section
- Location: tests/analytics.spec.ts:27:7

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Analytics Flow', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/login');
> 6  |     await page.fill('input[name="email"]', 'test@example.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  7  |     await page.fill('input[name="password"]', 'password123');
  8  |     await page.click('button[type="submit"]');
  9  |     await page.waitForURL(/.*dashboard/);
  10 |     await page.click('text=Analytics');
  11 |     await page.waitForURL(/.*analytics/);
  12 |   });
  13 | 
  14 |   test('should display analytics page', async ({ page }) => {
  15 |     await expect(page).toHaveURL(/.*analytics/);
  16 |     await expect(page.locator('h1')).toContainText('Analytics');
  17 |   });
  18 | 
  19 |   test('should display analytics cards', async ({ page }) => {
  20 |     await expect(page.locator('[data-testid="analytics-card"]').first()).toBeVisible();
  21 |   });
  22 | 
  23 |   test('should display content performance section', async ({ page }) => {
  24 |     await expect(page.locator('[data-testid="content-performance"]')).toBeVisible();
  25 |   });
  26 | 
  27 |   test('should display top creators section', async ({ page }) => {
  28 |     await expect(page.locator('[data-testid="top-creators"]')).toBeVisible();
  29 |   });
  30 | });
  31 | 
```