import { test, expect, Page } from '@playwright/test';
import { loginAs, waitForToast, clearFilters, selectDropdownOption } from '../helpers';

test.describe('Search and Filtering Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await loginAs(page, 'buyer');
  });

  test('should display search results for a valid query', async ({ page }) => {
    await page.getByTestId('search-input').fill('gaming');
    await page.getByTestId('search-submit').click();
    await expect(page).toHaveURL(/search\?q=gaming/);
    const results = page.getByTestId('search-result-card');
    await expect(results.first()).toBeVisible();
    const count = await results.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show empty state for no results', async ({ page }) => {
    await page.getByTestId('search-input').fill('xyznonexistent123');
    await page.getByTestId('search-submit').click();
    await expect(page.getByTestId('empty-state')).toBeVisible();
    await expect(page.getByTestId('empty-state')).toContainText('No results found');
  });

  test('should filter results by category', async ({ page }) => {
    await page.getByTestId('search-input').fill('art');
    await page.getByTestId('search-submit').click();
    await page.getByTestId('filter-category').click();
    await page.getByRole('option', { name: 'Digital Art' }).click();
    await expect(page).toHaveURL(/category=digital-art/);
    const cards = page.getByTestId('search-result-card');
    const count = await cards.count();
    for (let i = 0; i < count; i++) {
      await expect(cards.nth(i)).toContainText('Digital Art');
    }
  });

  test('should filter results by price range', async ({ page }) => {
    await page.getByTestId('search-input').fill('template');
    await page.getByTestId('search-submit').click();
    await page.getByTestId('price-min').fill('10');
    await page.getByTestId('price-max').fill('50');
    await page.getByTestId('apply-filters').click();
    const prices = page.getByTestId('result-price');
    const count = await prices.count();
    for (let i = 0; i < count; i++) {
      const text = await prices.nth(i).textContent();
      const value = parseFloat(text?.replace(/[^0-9.]/g, '') ?? '0');
      expect(value).toBeGreaterThanOrEqual(10);
      expect(value).toBeLessThanOrEqual(50);
    }
  });

  test('should sort results by price low to high', async ({ page }) => {
    await page.getByTestId('search-input').fill('music');
    await page.getByTestId('search-submit').click();
    await selectDropdownOption(page, 'sort-select', 'price-asc');
    const prices = page.getByTestId('result-price');
    const count = await prices.count();
    const values: number[] = [];
    for (let i = 0; i < count; i++) {
      const text = await prices.nth(i).textContent();
      values.push(parseFloat(text?.replace(/[^0-9.]/g, '') ?? '0'));
    }
    const sorted = [...values].sort((a, b) => a - b);
    expect(values).toEqual(sorted);
  });

  test('should sort results by newest first', async ({ page }) => {
    await page.getByTestId('search-input').fill('video');
    await page.getByTestId('search-submit').click();
    await selectDropdownOption(page, 'sort-select', 'newest');
    const dates = page.getByTestId('result-date');
    const count = await dates.count();
    const timestamps: number[] = [];
    for (let i = 0; i < count; i++) {
      const text = await dates.nth(i).textContent();
      timestamps.push(new Date(text ?? '').getTime());
    }
    const sorted = [...timestamps].sort((a, b) => b - a);
    expect(timestamps).toEqual(sorted);
  });

  test('should clear all filters', async ({ page }) => {
    await page.getByTestId('search-input').fill('photo');
    await page.getByTestId('search-submit').click();
    await page.getByTestId('filter-category').click();
    await page.getByRole('option', { name: 'Photography' }).click();
    await page.getByTestId('price-min').fill('5');
    await page.getByTestId('apply-filters').click();
    await clearFilters(page);
    await expect(page.getByTestId('price-min')).toHaveValue('');
    await expect(page.getByTestId('filter-category')).toContainText('All Categories');
  });

  test('should paginate through search results', async ({ page }) => {
    await page.getByTestId('search-input').fill('design');
    await page.getByTestId('search-submit').click();
    const firstPageFirst = await page.getByTestId('search-result-card').first().textContent();
    await page.getByTestId('pagination-next').click();
    await expect(page).toHaveURL(/page=2/);
    const secondPageFirst = await page.getByTestId('search-result-card').first().textContent();
    expect(secondPageFirst).not.toEqual(firstPageFirst);
  });

  test('should maintain filters when navigating back', async ({ page }) => {
    await page.getByTestId('search-input').fill('illustration');
    await page.getByTestId('search-submit').click();
    await page.getByTestId('filter-category').click();
    await page.getByRole('option', { name: 'Illustration' }).click();
    await page.getByTestId('search-result-card').first().click();
    await page.goBack();
    await expect(page.getByTestId('filter-category')).toContainText('Illustration');
  });

  test('should show search suggestions while typing', async ({ page }) => {
    await page.getByTestId('search-input').fill('gam');
    const suggestions = page.getByTestId('search-suggestion');
    await expect(suggestions.first()).toBeVisible();
    const count = await suggestions.count();
    expect(count).toBeGreaterThan(0);
    await suggestions.first().click();
    await expect(page).toHaveURL(/search\?q=/);
  });

  test('should handle special characters in search query', async ({ page }) => {
    await page.getByTestId('search-input').fill('<script>alert(1)</script>');
    await page.getByTestId('search-submit').click();
    await expect(page.getByTestId('empty-state')).toBeVisible();
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('<script>');
  });
});
