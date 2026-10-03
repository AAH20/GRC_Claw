import { Page, Browser, expect } from '@playwright/test';

const TEST_USERS: Record<string, { email: string; password: string }> = {
  user: { email: 'test@example.com', password: 'password123' },
  buyer: { email: 'buyer@example.com', password: 'password123' },
  creator: { email: 'creator@example.com', password: 'password123' },
  moderator: { email: 'moderator@example.com', password: 'password123' },
  admin: { email: 'admin@example.com', password: 'password123' },
};

export async function loginAs(page: Page, role: string = 'user'): Promise<void> {
  const creds = TEST_USERS[role] ?? TEST_USERS.user;
  await page.goto('/login');
  await page.fill('input[name="email"]', creds.email);
  await page.fill('input[name="password"]', creds.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*dashboard/, { timeout: 10000 });
}

export async function waitForToast(page: Page, text: string, timeout: number = 5000): Promise<void> {
  await expect(page.locator(`text=${text}`).first()).toBeVisible({ timeout });
}

export async function clearFilters(page: Page): Promise<void> {
  const clearBtn = page.locator('[data-testid="clear-filters"], button:has-text("Clear")').first();
  if (await clearBtn.isVisible()) {
    await clearBtn.click();
  }
}

export async function selectDropdownOption(page: Page, testId: string, value: string): Promise<void> {
  await page.getByTestId(testId).selectOption(value);
}

export async function createAuthenticatedPage(browser: Browser, role: string): Promise<Page> {
  const context = await browser.newContext();
  const page = await context.newPage();
  const creds = TEST_USERS[role] ?? TEST_USERS.user;
  await page.goto('/login');
  await page.fill('input[name="email"]', creds.email);
  await page.fill('input[name="password"]', creds.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*dashboard/, { timeout: 10000 });
  return page;
}

export function generateUniqueString(): string {
  return Math.random().toString(36).substring(2, 10);
}

export async function fillCardDetails(page: Page, details: {
  number: string;
  expiry: string;
  cvc: string;
  name: string;
}): Promise<void> {
  const cardNumber = page.getByTestId('card-number');
  if (await cardNumber.isVisible()) {
    await cardNumber.fill(details.number);
  }
  const cardExpiry = page.getByTestId('card-expiry');
  if (await cardExpiry.isVisible()) {
    await cardExpiry.fill(details.expiry);
  }
  const cardCvc = page.getByTestId('card-cvc');
  if (await cardCvc.isVisible()) {
    await cardCvc.fill(details.cvc);
  }
  const cardName = page.getByTestId('card-name');
  if (await cardName.isVisible()) {
    await cardName.fill(details.name);
  }
}
