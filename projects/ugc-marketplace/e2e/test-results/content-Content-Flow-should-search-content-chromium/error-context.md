# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: content.spec.ts >> Content Flow >> should search content
- Location: tests/content.spec.ts:41:7

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
  3  | test.describe('Content Flow', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/login');
> 6  |     await page.fill('input[name="email"]', 'test@example.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  7  |     await page.fill('input[name="password"]', 'password123');
  8  |     await page.click('button[type="submit"]');
  9  |     await page.waitForURL(/.*dashboard/);
  10 |     await page.click('text=Content');
  11 |     await page.waitForURL(/.*content/);
  12 |   });
  13 | 
  14 |   test('should display content page', async ({ page }) => {
  15 |     await expect(page).toHaveURL(/.*content/);
  16 |     await expect(page.locator('h1')).toContainText('Content');
  17 |   });
  18 | 
  19 |   test('should display content grid', async ({ page }) => {
  20 |     await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  21 |   });
  22 | 
  23 |   test('should display content cards', async ({ page }) => {
  24 |     await expect(page.locator('[data-testid="content-card"]').first()).toBeVisible();
  25 |   });
  26 | 
  27 |   test('should have create content button', async ({ page }) => {
  28 |     await expect(page.locator('button:has-text("Create Content")')).toBeVisible();
  29 |   });
  30 | 
  31 |   test('should filter content by type', async ({ page }) => {
  32 |     await page.selectOption('select[name="type"]', 'video');
  33 |     await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  34 |   });
  35 | 
  36 |   test('should filter content by status', async ({ page }) => {
  37 |     await page.selectOption('select[name="status"]', 'published');
  38 |     await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  39 |   });
  40 | 
  41 |   test('should search content', async ({ page }) => {
  42 |     await page.fill('input[name="search"]', 'test');
  43 |     await expect(page.locator('[data-testid="content-grid"]')).toBeVisible();
  44 |   });
  45 | });
  46 | 
```