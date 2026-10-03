import { test, expect, Page } from '@playwright/test';
import { createAuthenticatedPage, waitForToast, generateUniqueString } from '../helpers';

test.describe('Marketplace Listing Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await createAuthenticatedPage(browser, 'user');
  });

  test('should browse marketplace listings', async () => {
    await page.goto('/marketplace');
    await expect(page.locator('[data-testid="marketplace-grid"]')).toBeVisible();
    await expect(page.locator('[data-testid="listing-card"]').first()).toBeVisible();
    const listingCount = await page.locator('[data-testid="listing-card"]').count();
    expect(listingCount).toBeGreaterThan(0);
  });

  test('should filter listings by category', async () => {
    await page.goto('/marketplace');
    await page.click('[data-testid="category-filter"]');
    await page.click('[data-testid="category-option-gaming"]');
    await expect(page.locator('[data-testid="listing-card"]')).toHaveCount(
      await page.locator('[data-testid="listing-card"]').count()
    );
    const activeFilter = page.locator('[data-testid="active-filter"]');
    await expect(activeFilter).toContainText('Gaming');
  });

  test('should search listings by keyword', async () => {
    await page.goto('/marketplace');
    await page.fill('[data-testid="search-input"]', 'premium');
    await page.click('[data-testid="search-btn"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    const resultCount = await page.locator('[data-testid="listing-card"]').count();
    expect(resultCount).toBeGreaterThanOrEqual(0);
  });

  test('should sort listings by price ascending', async () => {
    await page.goto('/marketplace');
    await page.selectOption('[data-testid="sort-select"]', 'price-asc');
    await expect(page.locator('[data-testid="sort-indicator"]')).toContainText('Price: Low to High');
    const prices = await page.locator('[data-testid="listing-price"]').allTextContents();
    const numericPrices = prices.map(p => parseFloat(p.replace(/[^0-9.]/g, '')));
    const sorted = [...numericPrices].sort((a, b) => a - b);
    expect(numericPrices).toEqual(sorted);
  });

  test('should view listing detail page', async () => {
    await page.goto('/marketplace');
    await page.click('[data-testid="listing-card"] >> nth=0');
    await expect(page).toHaveURL(/\/marketplace\/listing\//);
    await expect(page.locator('[data-testid="listing-detail"]')).toBeVisible();
    await expect(page.locator('[data-testid="listing-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="listing-price"]')).toBeVisible();
    await expect(page.locator('[data-testid="listing-description"]')).toBeVisible();
  });

  test('should add listing to cart', async () => {
    await page.goto('/marketplace');
    await page.click('[data-testid="listing-card"] >> nth=0');
    await page.click('[data-testid="add-to-cart-btn"]');
    await waitForToast(page, 'Added to cart');
    await expect(page.locator('[data-testid="cart-badge"]')).toHaveText('1');
  });

  test('should handle pagination on marketplace', async () => {
    await page.goto('/marketplace');
    const nextBtn = page.locator('[data-testid="pagination-next"]');
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await expect(page.locator('[data-testid="current-page"]')).toHaveText('2');
    }
  });
});

test.describe('Marketplace Transaction Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await createAuthenticatedPage(browser, 'user');
  });

  test('should complete purchase flow from cart to checkout', async () => {
    await page.goto('/marketplace');
    await page.click('[data-testid="listing-card"] >> nth=0');
    await page.click('[data-testid="add-to-cart-btn"]');
    await page.goto('/cart');
    await expect(page.locator('[data-testid="cart-item"]')).toBeVisible();
    await page.click('[data-testid="checkout-btn"]');
    await expect(page).toHaveURL(/\/checkout/);
    await expect(page.locator('[data-testid="checkout-form"]')).toBeVisible();
  });

  test('should apply discount code during checkout', async () => {
    await page.goto('/checkout');
    await page.fill('[data-testid="discount-code-input"]', 'SAVE20');
    await page.click('[data-testid="apply-discount-btn"]');
    await waitForToast(page, 'Discount applied');
    await expect(page.locator('[data-testid="discount-amount"]')).toBeVisible();
  });

  test('should validate discount code errors', async () => {
    await page.goto('/checkout');
    await page.fill('[data-testid="discount-code-input"]', 'INVALIDCODE');
    await page.click('[data-testid="apply-discount-btn"]');
    await expect(page.locator('[data-testid="discount-error"]')).toBeVisible();
    await expect(page.locator('text=Invalid discount code')).toBeVisible();
  });

  test('should complete payment with saved payment method', async () => {
    await page.goto('/checkout');
    await page.click('[data-testid="saved-payment-method"] >> nth=0');
    await page.click('[data-testid="complete-purchase-btn"]');
    await expect(page.locator('[data-testid="payment-processing"]')).toBeVisible();
    await expect(page).toHaveURL(/\/checkout\/success/, { timeout: 15000 });
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
  });

  test('should view order history after purchase', async () => {
    await page.goto('/orders');
    await expect(page.locator('[data-testid="order-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="order-item"]').first()).toBeVisible();
    await page.click('[data-testid="order-item"] >> nth=0');
    await expect(page.locator('[data-testid="order-detail"]')).toBeVisible();
    await expect(page.locator('[data-testid="order-status"]')).toBeVisible();
  });

  test('should download purchased content', async () => {
    await page.goto('/orders');
    await page.click('[data-testid="order-item"] >> nth=0');
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-content-btn"]');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBeTruthy();
  });

  test('should request refund for a purchase', async () => {
    await page.goto('/orders');
    await page.click('[data-testid="order-item"] >> nth=0');
    await page.click('[data-testid="request-refund-btn"]');
    await expect(page.locator('[data-testid="refund-modal"]')).toBeVisible();
    await page.fill('[data-testid="refund-reason"]', 'Content did not match description.');
    await page.click('[data-testid="submit-refund-btn"]');
    await waitForToast(page, 'Refund request submitted');
  });

  test('should handle payment failure gracefully', async () => {
    await page.goto('/checkout');
    await page.click('[data-testid="saved-payment-method"] >> nth=0');
    await page.click('[data-testid="complete-purchase-btn"]');
    await expect(page.locator('[data-testid="payment-error"]')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Payment failed')).toBeVisible();
    await expect(page.locator('[data-testid="retry-payment-btn"]')).toBeVisible();
  });
});
