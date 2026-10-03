import { test, expect, Page } from '@playwright/test';
import {
  authenticate,
  expectToast,
  safeClick,
  uniqueId,
  waitForPageReady,
  TEST_COMMUNITY,
} from './helpers';

test.describe('Community Creation and Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    await authenticate(page);
    await page.goto('/communities');
    await waitForPageReady(page);
  });

  test('should display communities list page', async ({ page }) => {
    await expect(page).toHaveURL(/\/communities/);
    await expect(
      page.getByRole('heading', { name: /communities/i }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: /create community|new community/i }),
    ).toBeVisible();
  });

  test('should create a new community with valid data', async ({ page }) => {
    const communityName = uniqueId('community');

    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');

    // Wait for the create form/modal to appear
    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible({ timeout: 10_000 });

    // Fill in community details
    await page.getByLabel(/name/i).fill(communityName);
    await page.getByLabel(/description/i).fill(TEST_COMMUNITY.description);

    // Toggle privacy setting if available
    const privacyToggle = page.getByLabel(/private/i);
    if (await privacyToggle.isVisible()) {
      await privacyToggle.check();
    }

    // Submit the form
    await page.getByRole('button', { name: /create|submit|save/i }).click();

    // Verify success
    await expectToast(page, /community.*created|created.*community/i);

    // Verify the new community appears in the list
    await expect(page.getByText(communityName)).toBeVisible({ timeout: 10_000 });
  });

  test('should validate required fields on community creation', async ({ page }) => {
    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');

    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible();

    // Try to submit without filling required fields
    await page.getByRole('button', { name: /create|submit|save/i }).click();

    // Should show validation errors
    await expect(
      page.getByText(/name is required|name.*required/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('should view community details', async ({ page }) => {
    // First create a community to view
    const communityName = uniqueId('community');
    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');

    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible();

    await page.getByLabel(/name/i).fill(communityName);
    await page.getByLabel(/description/i).fill('Community for detail view test');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Click on the community to view details
    await page.getByText(communityName).click();
    await waitForPageReady(page);

    // Verify community detail page elements
    await expect(page).toHaveURL(/\/communities\/.+/);
    await expect(page.getByText(communityName)).toBeVisible();
    await expect(page.getByText('Community for detail view test')).toBeVisible();
  });

  test('should edit an existing community', async ({ page }) => {
    const communityName = uniqueId('community');
    const updatedDescription = 'Updated description for E2E test';

    // Create a community first
    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');
    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible();
    await page.getByLabel(/name/i).fill(communityName);
    await page.getByLabel(/description/i).fill('Original description');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Navigate to the community
    await page.getByText(communityName).click();
    await waitForPageReady(page);

    // Click edit button
    await safeClick(page, '[data-testid="edit-community-button"], button:has-text("Edit")');

    // Update the description
    await page.getByLabel(/description/i).fill(updatedDescription);
    await page.getByRole('button', { name: /save|update/i }).click();

    // Verify the update
    await expectToast(page, /updated|saved/i);
    await expect(page.getByText(updatedDescription)).toBeVisible();
  });

  test('should delete a community with confirmation', async ({ page }) => {
    const communityName = uniqueId('community');

    // Create a community to delete
    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');
    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible();
    await page.getByLabel(/name/i).fill(communityName);
    await page.getByLabel(/description/i).fill('Community to be deleted');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Navigate to community and delete
    await page.getByText(communityName).click();
    await waitForPageReady(page);

    await safeClick(page, '[data-testid="delete-community-button"], button:has-text("Delete")');

    // Confirm deletion in dialog
    const confirmDialog = page.locator('[role="dialog"], [data-testid="confirm-dialog"]');
    await expect(confirmDialog).toBeVisible();
    await confirmDialog.getByRole('button', { name: /confirm|delete|yes/i }).click();

    // Verify deletion
    await expectToast(page, /deleted|removed/i);
    await expect(page.getByText(communityName)).not.toBeVisible();
  });

  test('should handle community creation API failure gracefully', async ({ page }) => {
    // Intercept the API call and force a failure
    await page.route('**/api/v1/communities', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      }),
    );

    await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');
    const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
    await expect(form).toBeVisible();

    await page.getByLabel(/name/i).fill(uniqueId('community'));
    await page.getByLabel(/description/i).fill('This should fail');
    await page.getByRole('button', { name: /create|submit|save/i }).click();

    // Should show error message
    await expect(
      page.getByText(/error|failed|something went wrong/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('should search and filter communities', async ({ page }) => {
    // Create two communities
    const name1 = uniqueId('alpha');
    const name2 = uniqueId('beta');

    for (const name of [name1, name2]) {
      await safeClick(page, '[data-testid="create-community-button"], button:has-text("Create Community")');
      const form = page.locator('[data-testid="create-community-form"], form[name="create-community"], [role="dialog"]');
      await expect(form).toBeVisible();
      await page.getByLabel(/name/i).fill(name);
      await page.getByLabel(/description/i).fill(`Description for ${name}`);
      await page.getByRole('button', { name: /create|submit|save/i }).click();
      await expectToast(page, /created/i);
      await page.waitForTimeout(500);
    }

    // Search for the first community
    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill(name1);

    await expect(page.getByText(name1)).toBeVisible();
    await expect(page.getByText(name2)).not.toBeVisible();

    // Clear search
    await searchInput.fill('');
    await expect(page.getByText(name1)).toBeVisible();
    await expect(page.getByText(name2)).toBeVisible();
  });
});
