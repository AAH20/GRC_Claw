# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard Flow >> should navigate to moderation page
- Location: tests/dashboard.spec.ts:55:7

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - button "Open Next.js Dev Tools" [ref=e8] [cursor=pointer]
  - alert [ref=e12]
  - generic [ref=e14]:
    - generic [ref=e15]:
      - heading "Welcome Back" [level=3] [ref=e20]
      - paragraph [ref=e21]: Sign in to your RecruitHub account
    - generic [ref=e22]:
      - generic [ref=e23]:
        - generic [ref=e24]:
          - generic [ref=e25]: Email
          - textbox "Email" [ref=e27]:
            - /placeholder: you@company.com
        - generic [ref=e28]:
          - generic [ref=e29]: Password
          - textbox "Password" [ref=e31]:
            - /placeholder: Enter your password
        - button "Sign In" [ref=e32]
      - paragraph [ref=e33]:
        - text: Don't have an account?
        - link "Sign up" [ref=e34] [cursor=pointer]:
          - /url: /register
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Dashboard Flow', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/login');
> 6  |     await page.fill('input[name="email"]', 'test@example.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  7  |     await page.fill('input[name="password"]', 'password123');
  8  |     await page.click('button[type="submit"]');
  9  |     await page.waitForURL(/.*dashboard/);
  10 |   });
  11 | 
  12 |   test('should display dashboard page', async ({ page }) => {
  13 |     await expect(page).toHaveURL(/.*dashboard/);
  14 |     await expect(page.locator('h1')).toContainText('Dashboard');
  15 |   });
  16 | 
  17 |   test('should display navigation sidebar', async ({ page }) => {
  18 |     await expect(page.locator('nav')).toBeVisible();
  19 |     await expect(page.locator('text=Listings')).toBeVisible();
  20 |     await expect(page.locator('text=Content')).toBeVisible();
  21 |     await expect(page.locator('text=Transactions')).toBeVisible();
  22 |     await expect(page.locator('text=Creators')).toBeVisible();
  23 |     await expect(page.locator('text=Analytics')).toBeVisible();
  24 |   });
  25 | 
  26 |   test('should display header with user info', async ({ page }) => {
  27 |     await expect(page.locator('header')).toBeVisible();
  28 |   });
  29 | 
  30 |   test('should navigate to listings page', async ({ page }) => {
  31 |     await page.click('text=Listings');
  32 |     await expect(page).toHaveURL(/.*listings/);
  33 |   });
  34 | 
  35 |   test('should navigate to content page', async ({ page }) => {
  36 |     await page.click('text=Content');
  37 |     await expect(page).toHaveURL(/.*content/);
  38 |   });
  39 | 
  40 |   test('should navigate to transactions page', async ({ page }) => {
  41 |     await page.click('text=Transactions');
  42 |     await expect(page).toHaveURL(/.*transactions/);
  43 |   });
  44 | 
  45 |   test('should navigate to creators page', async ({ page }) => {
  46 |     await page.click('text=Creators');
  47 |     await expect(page).toHaveURL(/.*creators/);
  48 |   });
  49 | 
  50 |   test('should navigate to analytics page', async ({ page }) => {
  51 |     await page.click('text=Analytics');
  52 |     await expect(page).toHaveURL(/.*analytics/);
  53 |   });
  54 | 
  55 |   test('should navigate to moderation page', async ({ page }) => {
  56 |     await page.click('text=Moderation');
  57 |     await expect(page).toHaveURL(/.*moderation/);
  58 |   });
  59 | 
  60 |   test('should navigate to settings page', async ({ page }) => {
  61 |     await page.click('text=Settings');
  62 |     await expect(page).toHaveURL(/.*settings/);
  63 |   });
  64 | 
  65 |   test('should navigate to profile page', async ({ page }) => {
  66 |     await page.click('text=Profile');
  67 |     await expect(page).toHaveURL(/.*profile/);
  68 |   });
  69 | 
  70 |   test('should navigate to notifications page', async ({ page }) => {
  71 |     await page.click('text=Notifications');
  72 |     await expect(page).toHaveURL(/.*notifications/);
  73 |   });
  74 | });
  75 | 
```