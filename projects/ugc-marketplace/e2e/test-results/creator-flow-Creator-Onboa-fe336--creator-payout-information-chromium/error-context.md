# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creator-flow.spec.ts >> Creator Onboarding Flow >> should save creator payout information
- Location: tests/creator-flow.spec.ts:46:7

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

# Test source

```ts
  1   | import { test, expect, Page } from '@playwright/test';
  2   | import { createAuthenticatedPage, waitForToast, generateUniqueString } from '../helpers';
  3   | 
  4   | test.describe('Creator Onboarding Flow', () => {
  5   |   let page: Page;
  6   | 
> 7   |   test.beforeEach(async ({ browser }) => {
      |        ^ Test timeout of 30000ms exceeded while running "beforeEach" hook.
  8   |     page = await createAuthenticatedPage(browser, 'creator');
  9   |   });
  10  | 
  11  |   test('should display creator onboarding wizard for new creators', async () => {
  12  |     await page.goto('/creator/onboarding');
  13  |     await expect(page.locator('[data-testid="onboarding-wizard"]')).toBeVisible();
  14  |     await expect(page.locator('text=Welcome to Creator Hub')).toBeVisible();
  15  |     await expect(page.locator('[data-testid="onboarding-step-1"]')).toBeVisible();
  16  |   });
  17  | 
  18  |   test('should complete creator profile setup', async () => {
  19  |     await page.goto('/creator/onboarding');
  20  |     await page.fill('[data-testid="creator-display-name"]', `Test Creator ${generateUniqueString()}`);
  21  |     await page.fill('[data-testid="creator-bio"]', 'A passionate content creator focused on quality UGC.');
  22  |     await page.selectOption('[data-testid="creator-category"]', 'gaming');
  23  |     await page.click('[data-testid="onboarding-next-btn"]');
  24  |     await expect(page.locator('[data-testid="onboarding-step-2"]')).toBeVisible();
  25  |   });
  26  | 
  27  |   test('should validate required fields in creator profile', async () => {
  28  |     await page.goto('/creator/onboarding');
  29  |     await page.click('[data-testid="onboarding-next-btn"]');
  30  |     await expect(page.locator('[data-testid="error-display-name"]')).toBeVisible();
  31  |     await expect(page.locator('[data-testid="error-bio"]')).toBeVisible();
  32  |   });
  33  | 
  34  |   test('should allow creators to upload a profile avatar', async () => {
  35  |     await page.goto('/creator/onboarding');
  36  |     const fileInput = page.locator('[data-testid="avatar-upload-input"]');
  37  |     await fileInput.setInputFiles({
  38  |       name: 'avatar.png',
  39  |       mimeType: 'image/png',
  40  |       buffer: Buffer.from('fake-image-data'),
  41  |     });
  42  |     await expect(page.locator('[data-testid="avatar-preview"]')).toBeVisible();
  43  |     await expect(page.locator('text=Avatar uploaded successfully')).toBeVisible();
  44  |   });
  45  | 
  46  |   test('should save creator payout information', async () => {
  47  |     await page.goto('/creator/onboarding');
  48  |     await page.click('[data-testid="onboarding-next-btn"]');
  49  |     await page.click('[data-testid="onboarding-next-btn"]');
  50  |     await page.fill('[data-testid="payout-paypal-email"]', 'creator@test.com');
  51  |     await page.click('[data-testid="save-payout-btn"]');
  52  |     await waitForToast(page, 'Payout information saved');
  53  |   });
  54  | });
  55  | 
  56  | test.describe('Creator Content Creation Flow', () => {
  57  |   let page: Page;
  58  | 
  59  |   test.beforeEach(async ({ browser }) => {
  60  |     page = await createAuthenticatedPage(browser, 'creator');
  61  |     await page.goto('/creator/dashboard');
  62  |   });
  63  | 
  64  |   test('should navigate to content creation page', async () => {
  65  |     await page.click('[data-testid="create-content-btn"]');
  66  |     await expect(page).toHaveURL(/\/creator\/content\/create/);
  67  |     await expect(page.locator('[data-testid="content-creation-form"]')).toBeVisible();
  68  |   });
  69  | 
  70  |   test('should create a new text-based content listing', async () => {
  71  |     await page.goto('/creator/content/create');
  72  |     await page.fill('[data-testid="content-title"]', `Test Content ${generateUniqueString()}`);
  73  |     await page.fill('[data-testid="content-description"]', 'This is a test content description for E2E testing.');
  74  |     await page.selectOption('[data-testid="content-type"]', 'text');
  75  |     await page.fill('[data-testid="content-price"]', '25.00');
  76  |     await page.click('[data-testid="submit-content-btn"]');
  77  |     await waitForToast(page, 'Content created successfully');
  78  |     await expect(page).toHaveURL(/\/creator\/content/);
  79  |   });
  80  | 
  81  |   test('should create a new video-based content listing', async () => {
  82  |     await page.goto('/creator/content/create');
  83  |     await page.fill('[data-testid="content-title"]', `Video Content ${generateUniqueString()}`);
  84  |     await page.fill('[data-testid="content-description"]', 'A premium video content listing.');
  85  |     await page.selectOption('[data-testid="content-type"]', 'video');
  86  |     await page.fill('[data-testid="content-price"]', '50.00');
  87  |     const videoInput = page.locator('[data-testid="video-upload-input"]');
  88  |     await videoInput.setInputFiles({
  89  |       name: 'test-video.mp4',
  90  |       mimeType: 'video/mp4',
  91  |       buffer: Buffer.from('fake-video-data'),
  92  |     });
  93  |     await page.click('[data-testid="submit-content-btn"]');
  94  |     await waitForToast(page, 'Content created successfully');
  95  |   });
  96  | 
  97  |   test('should validate content pricing constraints', async () => {
  98  |     await page.goto('/creator/content/create');
  99  |     await page.fill(`[data-testid="content-title"]`, 'Invalid Price Content');
  100 |     await page.fill('[data-testid="content-description"]', 'Testing price validation.');
  101 |     await page.fill('[data-testid="content-price"]', '-10');
  102 |     await page.click('[data-testid="submit-content-btn"]');
  103 |     await expect(page.locator('[data-testid="error-price"]')).toBeVisible();
  104 |     await expect(page.locator('text=Price must be greater than 0')).toBeVisible();
  105 |   });
  106 | 
  107 |   test('should save content as draft', async () => {
```