import { test, expect, Page } from '@playwright/test';
import {
  authenticate,
  expectToast,
  safeClick,
  uniqueId,
  waitForPageReady,
  TEST_TIER,
} from './helpers';

test.describe('Tier Management and Upgrade Flow', () => {
  test.beforeEach(async ({ page }) => {
    await authenticate(page);
    await page.goto('/tiers');
    await waitForPageReady(page);
  });

  test('should display tiers list page', async ({ page }) => {
    await expect(page).toHaveURL(/\/tiers/);
    await expect(
      page.getByRole('heading', { name: /tiers|membership tiers/i }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: /create tier|new tier|add tier/i }),
    ).toBeVisible();
  });

  test('should create a new tier with valid data', async ({ page }) => {
    const tierName = uniqueId('tier');

    await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');

    const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
    await expect(form).toBeVisible({ timeout: 10_000 });

    await page.getByLabel(/name/i).fill(tierName);
    await page.getByLabel(/description/i).fill(TEST_TIER.description);

    // Select tier level
    const levelSelect = page.getByLabel(/level/i);
    if (await levelSelect.isVisible()) {
      await levelSelect.selectOption(TEST_TIER.level);
    }

    // Set monthly fee
    const feeInput = page.getByLabel(/monthly fee|price|fee/i);
    if (await feeInput.isVisible()) {
      await feeInput.fill(String(TEST_TIER.monthlyFee));
    }

    // Add benefits
    const benefitsInput = page.getByLabel(/benefits/i);
    if (await benefitsInput.isVisible()) {
      for (const benefit of TEST_TIER.benefits) {
        await benefitsInput.fill(benefit);
        await page.getByRole('button', { name: /add benefit/i }).click();
      }
    }

    await page.getByRole('button', { name: /create|submit|save/i }).click();

    await expectToast(page, /tier.*created|created.*tier/i);
    await expect(page.getByText(tierName)).toBeVisible({ timeout: 10_000 });
  });

  test('should validate tier creation required fields', async ({ page }) => {
    await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');

    const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
    await expect(form).toBeVisible();

    // Submit without filling required fields
    await page.getByRole('button', { name: /create|submit|save/i }).click();

    await expect(
      page.getByText(/name is required|name.*required/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('should view tier details', async ({ page }) => {
    const tierName = uniqueId('tier');

    // Create a tier
    await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');
    const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
    await expect(form).toBeVisible();
    await page.getByLabel(/name/i).fill(tierName);
    await page.getByLabel(/description/i).fill('Tier for detail view test');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Click on tier to view details
    await page.getByText(tierName).click();
    await waitForPageReady(page);

    await expect(page).toHaveURL(/\/tiers\/.+/);
    await expect(page.getByText(tierName)).toBeVisible();
    await expect(page.getByText('Tier for detail view test')).toBeVisible();
  });

  test('should update an existing tier', async ({ page }) => {
    const tierName = uniqueId('tier');
    const updatedDescription = 'Updated tier description';

    // Create a tier
    await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');
    const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
    await expect(form).toBeVisible();
    await page.getByLabel(/name/i).fill(tierName);
    await page.getByLabel(/description/i).fill('Original tier description');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Navigate to tier and edit
    await page.getByText(tierName).click();
    await waitForPageReady(page);

    await safeClick(page, '[data-testid="edit-tier-button"], button:has-text("Edit")');
    await page.getByLabel(/description/i).fill(updatedDescription);
    await page.getByRole('button', { name: /save|update/i }).click();

    await expectToast(page, /updated|saved/i);
    await expect(page.getByText(updatedDescription)).toBeVisible();
  });

  test('should delete a tier with confirmation', async ({ page }) => {
    const tierName = uniqueId('tier');

    // Create a tier to delete
    await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');
    const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
    await expect(form).toBeVisible();
    await page.getByLabel(/name/i).fill(tierName);
    await page.getByLabel(/description/i).fill('Tier to be deleted');
    await page.getByRole('button', { name: /create|submit|save/i }).click();
    await expectToast(page, /created/i);

    // Navigate to tier and delete
    await page.getByText(tierName).click();
    await waitForPageReady(page);

    await safeClick(page, '[data-testid="delete-tier-button"], button:has-text("Delete")');

    const confirmDialog = page.locator('[role="dialog"], [data-testid="confirm-dialog"]');
    await expect(confirmDialog).toBeVisible();
    await confirmDialog.getByRole('button', { name: /confirm|delete|yes/i }).click();

    await expectToast(page, /deleted|removed/i);
    await expect(page.getByText(tierName)).not.toBeVisible();
  });

  test('should request a tier upgrade', async ({ page }) => {
    // Navigate to upgrade page
    await page.goto('/tiers/upgrade');
    await waitForPageReady(page);

    await expect(
      page.getByRole('heading', { name: /upgrade|membership upgrade/i }),
    ).toBeVisible();

    // Select target tier
    const targetTier = page.getByLabel(/target tier|upgrade to/i);
    if (await targetTier.isVisible()) {
      await targetTier.selectOption({ index: 1 });
    }

    // Submit upgrade request
    await page.getByRole('button', { name: /request upgrade|submit/i }).click();

    await expectToast(page, /upgrade.*requested|request.*submitted/i);
  });

  test('should approve a tier upgrade request', async ({ page }) => {
    // First create an upgrade request
    await page.goto('/tiers/upgrade');
    await waitForPageReady(page);

    const targetTier = page.getByLabel(/target tier|upgrade to/i);
    if (await targetTier.isVisible()) {
      await targetTier.selectOption({ index: 1 });
    }
    await page.getByRole('button', { name: /request upgrade|submit/i }).click();
    await expectToast(page, /requested/i);

    // Navigate to upgrade requests management
    await page.goto('/tiers/upgrades');
    await waitForPageReady(page);

    // Approve the first pending request
    const approveButton = page.getByRole('button', { name: /approve/i }).first();
    if (await approveButton.isVisible({ timeout: 5_000 })) {
      await approveButton.click();
      await expectToast(page, /approved|accepted/i);
    }
  });

  test('should deny a tier upgrade request with reason', async ({ page }) => {
    // Create an upgrade request
    await page.goto('/tiers/upgrade');
    await waitForPageReady(page);

    const targetTier = page.getByLabel(/target tier|upgrade to/i);
    if (await targetTier.isVisible()) {
      await targetTier.selectOption({ index: 1 });
    }
    await page.getByRole('button', { name: /request upgrade|submit/i }).click();
    await expectToast(page, /requested/i);

    // Navigate to upgrade requests
    await page.goto('/tiers/upgrades');
    await waitForPageReady(page);

    // Deny the first pending request
    const denyButton = page.getByRole('button', { name: /deny|reject/i }).first();
    if (await denyButton.isVisible({ timeout: 5_000 })) {
      await denyButton.click();

      // Fill in denial reason if a dialog appears
      const reasonInput = page.locator('[role="dialog"]').getByLabel(/reason/i);
      if (await reasonInput.isVisible({ timeout: 3_000 })) {
        await reasonInput.fill('Does not meet requirements at this time');
      }

      await page.getByRole('button', { name: /confirm|deny|reject/i }).click();
      await expectToast(page, /denied|rejected/i);
    }
  });

  test('should filter tiers by level', async ({ page }) => {
    // Create tiers with different levels
    const bronzeName = uniqueId('bronze');
    const silverName = uniqueId('silver');

    for (const [name, level] of [[bronzeName, 'bronze'], [silverName, 'silver']] as const) {
      await safeClick(page, '[data-testid="create-tier-button"], button:has-text("Create Tier")');
      const form = page.locator('[data-testid="create-tier-form"], form[name="create-tier"], [role="dialog"]');
      await expect(form).toBeVisible();
      await page.getByLabel(/name/i).fill(name);
      await page.getByLabel(/description/i).fill(`${level} tier`);

      const levelSelect = page.getByLabel(/level/i);
      if (await levelSelect.isVisible()) {
        await levelSelect.selectOption(level);
      }

      await page.getByRole('button', { name: /create|submit|save/i }).click();
      await expectToast(page, /created/i);
      await page.waitForTimeout(500);
    }

    // Filter by bronze level
    const levelFilter = page.getByLabel(/filter by level|level filter/i);
    if (await levelFilter.isVisible()) {
      await levelFilter.selectOption('bronze');
      await expect(page.getByText(bronzeName)).toBeVisible();
      await expect(page.getByText(silverName)).not.toBeVisible();

      // Filter by silver level
      await levelFilter.selectOption('silver');
      await expect(page.getByText(silverName)).toBeVisible();
      await expect(page.getByText(bronzeName)).not.toBeVisible();
    }
  });
});
