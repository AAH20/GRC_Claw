import { test, expect, Page } from '@playwright/test';
import { loginAs, waitForToast, fillCardDetails } from '../helpers';

test.describe('Payment and Payout Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should complete a purchase with valid credit card', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await page.getByTestId('checkout-dialog').waitFor();
    await fillCardDetails(page, {
      number: '4242424242424242',
      expiry: '12/28',
      cvc: '123',
      name: 'Test User',
    });
    await page.getByTestId('confirm-payment').click();
    await waitForToast(page, 'Payment successful');
    await expect(page).toHaveURL(/orders\/confirmation/);
    await expect(page.getByTestId('order-status')).toContainText('Completed');
  });

  test('should reject purchase with invalid card number', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await fillCardDetails(page, {
      number: '1234567890123456',
      expiry: '12/28',
      cvc: '123',
      name: 'Test User',
    });
    await page.getByTestId('confirm-payment').click();
    await expect(page.getByTestId('payment-error')).toBeVisible();
    await expect(page.getByTestId('payment-error')).toContainText('Invalid card number');
  });

  test('should reject purchase with expired card', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await fillCardDetails(page, {
      number: '4242424242424242',
      expiry: '01/20',
      cvc: '123',
      name: 'Test User',
    });
    await page.getByTestId('confirm-payment').click();
    await expect(page.getByTestId('payment-error')).toContainText('Card has expired');
  });

  test('should add item to cart and checkout', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('add-to-cart').click();
    await waitForToast(page, 'Added to cart');
    await page.getByTestId('cart-icon').click();
    await expect(page.getByTestId('cart-item')).toBeVisible();
    await page.getByTestId('checkout-button').click();
    await expect(page).toHaveURL(/checkout/);
    await expect(page.getByTestId('cart-total')).toBeVisible();
  });

  test('should apply discount code during checkout', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await page.getByTestId('discount-input').fill('SAVE20');
    await page.getByTestId('apply-discount').click();
    await waitForToast(page, 'Discount applied');
    const originalText = await page.getByTestId('order-subtotal').textContent();
    const discountText = await page.getByTestId('discount-amount').textContent();
    const totalText = await page.getByTestId('order-total').textContent();
    const original = parseFloat(originalText?.replace(/[^0-9.]/g, '') ?? '0');
    const discount = parseFloat(discountText?.replace(/[^0-9.]/g, '') ?? '0');
    const total = parseFloat(totalText?.replace(/[^0-9.]/g, '') ?? '0');
    expect(total).toBeCloseTo(original - discount, 2);
  });

  test('should reject invalid discount code', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await page.getByTestId('discount-input').fill('INVALIDCODE');
    await page.getByTestId('apply-discount').click();
    await expect(page.getByTestId('discount-error')).toContainText('Invalid discount code');
  });

  test('should view transaction history', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/transactions');
    const rows = page.getByTestId('transaction-row');
    await expect(rows.first()).toBeVisible();
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    await expect(rows.first()).toContainText('$');
  });

  test('should request payout as creator', async ({ page }) => {
    await loginAs(page, 'creator');
    await page.goto('/settings/payouts');
    await page.getByTestId('payout-balance').waitFor();
    const balanceText = await page.getByTestId('payout-balance').textContent();
    const balance = parseFloat(balanceText?.replace(/[^0-9.]/g, '') ?? '0');
    expect(balance).toBeGreaterThan(0);
    await page.getByTestId('request-payout').click();
    await page.getByTestId('payout-amount').fill(balance.toString());
    await page.getByTestId('confirm-payout').click();
    await waitForToast(page, 'Payout requested');
  });

  test('should prevent payout exceeding balance', async ({ page }) => {
    await loginAs(page, 'creator');
    await page.goto('/settings/payouts');
    await page.getByTestId('request-payout').click();
    await page.getByTestId('payout-amount').fill('999999');
    await page.getByTestId('confirm-payout').click();
    await expect(page.getByTestId('payout-error')).toContainText('Insufficient balance');
  });

  test('should display order details after purchase', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/orders');
    await page.getByTestId('order-row').first().click();
    await expect(page.getByTestId('order-detail')).toBeVisible();
    await expect(page.getByTestId('order-id')).toBeVisible();
    await expect(page.getByTestId('order-date')).toBeVisible();
    await expect(page.getByTestId('order-total')).toBeVisible();
    await expect(page.getByTestId('order-items')).toBeVisible();
  });

  test('should handle payment cancellation gracefully', async ({ page }) => {
    await loginAs(page, 'buyer');
    await page.goto('/listings/sample-listing');
    await page.getByTestId('buy-now-button').click();
    await page.getByTestId('cancel-payment').click();
    await expect(page.getByTestId('checkout-dialog')).not.toBeVisible();
    await expect(page).toHaveURL(/listings\/sample-listing/);
  });
});
