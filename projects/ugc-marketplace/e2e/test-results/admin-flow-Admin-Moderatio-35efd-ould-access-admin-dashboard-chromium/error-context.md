# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-flow.spec.ts >> Admin Moderation and User Management Flow >> should access admin dashboard
- Location: tests/admin-flow.spec.ts:10:7

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
  1  | import { Page, Browser, expect } from '@playwright/test';
  2  | 
  3  | const TEST_USERS: Record<string, { email: string; password: string }> = {
  4  |   user: { email: 'test@example.com', password: 'password123' },
  5  |   buyer: { email: 'buyer@example.com', password: 'password123' },
  6  |   creator: { email: 'creator@example.com', password: 'password123' },
  7  |   moderator: { email: 'moderator@example.com', password: 'password123' },
  8  |   admin: { email: 'admin@example.com', password: 'password123' },
  9  | };
  10 | 
  11 | export async function loginAs(page: Page, role: string = 'user'): Promise<void> {
  12 |   const creds = TEST_USERS[role] ?? TEST_USERS.user;
  13 |   await page.goto('/login');
> 14 |   await page.fill('input[name="email"]', creds.email);
     |              ^ Error: page.fill: Test timeout of 30000ms exceeded.
  15 |   await page.fill('input[name="password"]', creds.password);
  16 |   await page.click('button[type="submit"]');
  17 |   await page.waitForURL(/.*dashboard/, { timeout: 10000 });
  18 | }
  19 | 
  20 | export async function waitForToast(page: Page, text: string, timeout: number = 5000): Promise<void> {
  21 |   await expect(page.locator(`text=${text}`).first()).toBeVisible({ timeout });
  22 | }
  23 | 
  24 | export async function clearFilters(page: Page): Promise<void> {
  25 |   const clearBtn = page.locator('[data-testid="clear-filters"], button:has-text("Clear")').first();
  26 |   if (await clearBtn.isVisible()) {
  27 |     await clearBtn.click();
  28 |   }
  29 | }
  30 | 
  31 | export async function selectDropdownOption(page: Page, testId: string, value: string): Promise<void> {
  32 |   await page.getByTestId(testId).selectOption(value);
  33 | }
  34 | 
  35 | export async function createAuthenticatedPage(browser: Browser, role: string): Promise<Page> {
  36 |   const context = await browser.newContext();
  37 |   const page = await context.newPage();
  38 |   const creds = TEST_USERS[role] ?? TEST_USERS.user;
  39 |   await page.goto('/login');
  40 |   await page.fill('input[name="email"]', creds.email);
  41 |   await page.fill('input[name="password"]', creds.password);
  42 |   await page.click('button[type="submit"]');
  43 |   await page.waitForURL(/.*dashboard/, { timeout: 10000 });
  44 |   return page;
  45 | }
  46 | 
  47 | export function generateUniqueString(): string {
  48 |   return Math.random().toString(36).substring(2, 10);
  49 | }
  50 | 
  51 | export async function fillCardDetails(page: Page, details: {
  52 |   number: string;
  53 |   expiry: string;
  54 |   cvc: string;
  55 |   name: string;
  56 | }): Promise<void> {
  57 |   const cardNumber = page.getByTestId('card-number');
  58 |   if (await cardNumber.isVisible()) {
  59 |     await cardNumber.fill(details.number);
  60 |   }
  61 |   const cardExpiry = page.getByTestId('card-expiry');
  62 |   if (await cardExpiry.isVisible()) {
  63 |     await cardExpiry.fill(details.expiry);
  64 |   }
  65 |   const cardCvc = page.getByTestId('card-cvc');
  66 |   if (await cardCvc.isVisible()) {
  67 |     await cardCvc.fill(details.cvc);
  68 |   }
  69 |   const cardName = page.getByTestId('card-name');
  70 |   if (await cardName.isVisible()) {
  71 |     await cardName.fill(details.name);
  72 |   }
  73 | }
  74 | 
```