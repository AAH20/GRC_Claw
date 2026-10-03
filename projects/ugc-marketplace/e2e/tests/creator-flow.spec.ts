import { test, expect, Page } from '@playwright/test';
import { createAuthenticatedPage, waitForToast, generateUniqueString } from '../helpers';

test.describe('Creator Onboarding Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await createAuthenticatedPage(browser, 'creator');
  });

  test('should display creator onboarding wizard for new creators', async () => {
    await page.goto('/creator/onboarding');
    await expect(page.locator('[data-testid="onboarding-wizard"]')).toBeVisible();
    await expect(page.locator('text=Welcome to Creator Hub')).toBeVisible();
    await expect(page.locator('[data-testid="onboarding-step-1"]')).toBeVisible();
  });

  test('should complete creator profile setup', async () => {
    await page.goto('/creator/onboarding');
    await page.fill('[data-testid="creator-display-name"]', `Test Creator ${generateUniqueString()}`);
    await page.fill('[data-testid="creator-bio"]', 'A passionate content creator focused on quality UGC.');
    await page.selectOption('[data-testid="creator-category"]', 'gaming');
    await page.click('[data-testid="onboarding-next-btn"]');
    await expect(page.locator('[data-testid="onboarding-step-2"]')).toBeVisible();
  });

  test('should validate required fields in creator profile', async () => {
    await page.goto('/creator/onboarding');
    await page.click('[data-testid="onboarding-next-btn"]');
    await expect(page.locator('[data-testid="error-display-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-bio"]')).toBeVisible();
  });

  test('should allow creators to upload a profile avatar', async () => {
    await page.goto('/creator/onboarding');
    const fileInput = page.locator('[data-testid="avatar-upload-input"]');
    await fileInput.setInputFiles({
      name: 'avatar.png',
      mimeType: 'image/png',
      buffer: Buffer.from('fake-image-data'),
    });
    await expect(page.locator('[data-testid="avatar-preview"]')).toBeVisible();
    await expect(page.locator('text=Avatar uploaded successfully')).toBeVisible();
  });

  test('should save creator payout information', async () => {
    await page.goto('/creator/onboarding');
    await page.click('[data-testid="onboarding-next-btn"]');
    await page.click('[data-testid="onboarding-next-btn"]');
    await page.fill('[data-testid="payout-paypal-email"]', 'creator@test.com');
    await page.click('[data-testid="save-payout-btn"]');
    await waitForToast(page, 'Payout information saved');
  });
});

test.describe('Creator Content Creation Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await createAuthenticatedPage(browser, 'creator');
    await page.goto('/creator/dashboard');
  });

  test('should navigate to content creation page', async () => {
    await page.click('[data-testid="create-content-btn"]');
    await expect(page).toHaveURL(/\/creator\/content\/create/);
    await expect(page.locator('[data-testid="content-creation-form"]')).toBeVisible();
  });

  test('should create a new text-based content listing', async () => {
    await page.goto('/creator/content/create');
    await page.fill('[data-testid="content-title"]', `Test Content ${generateUniqueString()}`);
    await page.fill('[data-testid="content-description"]', 'This is a test content description for E2E testing.');
    await page.selectOption('[data-testid="content-type"]', 'text');
    await page.fill('[data-testid="content-price"]', '25.00');
    await page.click('[data-testid="submit-content-btn"]');
    await waitForToast(page, 'Content created successfully');
    await expect(page).toHaveURL(/\/creator\/content/);
  });

  test('should create a new video-based content listing', async () => {
    await page.goto('/creator/content/create');
    await page.fill('[data-testid="content-title"]', `Video Content ${generateUniqueString()}`);
    await page.fill('[data-testid="content-description"]', 'A premium video content listing.');
    await page.selectOption('[data-testid="content-type"]', 'video');
    await page.fill('[data-testid="content-price"]', '50.00');
    const videoInput = page.locator('[data-testid="video-upload-input"]');
    await videoInput.setInputFiles({
      name: 'test-video.mp4',
      mimeType: 'video/mp4',
      buffer: Buffer.from('fake-video-data'),
    });
    await page.click('[data-testid="submit-content-btn"]');
    await waitForToast(page, 'Content created successfully');
  });

  test('should validate content pricing constraints', async () => {
    await page.goto('/creator/content/create');
    await page.fill(`[data-testid="content-title"]`, 'Invalid Price Content');
    await page.fill('[data-testid="content-description"]', 'Testing price validation.');
    await page.fill('[data-testid="content-price"]', '-10');
    await page.click('[data-testid="submit-content-btn"]');
    await expect(page.locator('[data-testid="error-price"]')).toBeVisible();
    await expect(page.locator('text=Price must be greater than 0')).toBeVisible();
  });

  test('should save content as draft', async () => {
    await page.goto('/creator/content/create');
    await page.fill('[data-testid="content-title"]', `Draft Content ${generateUniqueString()}`);
    await page.fill('[data-testid="content-description"]', 'This will be saved as a draft.');
    await page.click('[data-testid="save-draft-btn"]');
    await waitForToast(page, 'Draft saved');
    await expect(page.locator('[data-testid="draft-badge"]')).toBeVisible();
  });

  test('should view content analytics after creation', async () => {
    await page.goto('/creator/content');
    await page.click('[data-testid="content-item"] >> nth=0');
    await page.click('[data-testid="view-analytics-btn"]');
    await expect(page.locator('[data-testid="content-analytics-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="views-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue-count"]')).toBeVisible();
  });

  test('should edit existing content listing', async () => {
    await page.goto('/creator/content');
    await page.click('[data-testid="content-item"] >> nth=0');
    await page.click('[data-testid="edit-content-btn"]');
    await page.fill('[data-testid="content-title"]', `Updated Content ${generateUniqueString()}`);
    await page.click('[data-testid="save-content-btn"]');
    await waitForToast(page, 'Content updated successfully');
  });

  test('should delete content listing with confirmation', async () => {
    await page.goto('/creator/content');
    await page.click('[data-testid="content-item"] >> nth=0');
    await page.click('[data-testid="delete-content-btn"]');
    await expect(page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
    await page.click('[data-testid="confirm-delete-btn"]');
    await waitForToast(page, 'Content deleted');
  });
});
