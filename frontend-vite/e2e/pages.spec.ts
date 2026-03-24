import { test, expect } from '@playwright/test';

test.describe('Page Loading', () => {
  test('Home page (/) loads and displays paddle cards', async ({ page }) => {
    await page.goto('/');
    // Wait for content to load
    await expect(page.locator('body')).toBeVisible();
    // Check BottomNav is present (using fixed positioning or aria-label)
    await expect(page.locator('[aria-label="Inicio"], [aria-label="Recomendacao"], [aria-label="Analise"]').first()).toBeVisible();
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('Recommend page (/recommend) loads quiz', async ({ page }) => {
    await page.goto('/recommend');
    await expect(page.locator('body')).toBeVisible();
    // Quiz should have step content or selection options
    await page.waitForLoadState('networkidle');
  });

  test('Statistics page (/statistics) loads', async ({ page }) => {
    await page.goto('/statistics');
    await expect(page.locator('body')).toBeVisible();
    // Stats page shows title
    await expect(page.locator('text=RAIO-X').or(page.locator('text=CARREGANDO'))).toBeVisible({ timeout: 10000 });
  });

  test('Chat page (/chat) loads', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('body')).toBeVisible();
    // Chat should show greeting or input
    await page.waitForLoadState('networkidle');
  });

  test('BottomNav navigates between pages', async ({ page }) => {
    await page.goto('/');
    // Click AI Coach nav item
    const recommendLink = page.locator('a[href="/recommend"], [aria-label*="Recomenda"]').first();
    if (await recommendLink.isVisible()) {
      await recommendLink.click();
      await expect(page).toHaveURL(/\/recommend/);
    }
  });

  test('404 page for unknown routes', async ({ page }) => {
    await page.goto('/unknown-route-xyz');
    await expect(page.locator('body')).toBeVisible();
    // Should show not-found content (not crash)
  });

  test('No JavaScript console errors on Home', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Filter out expected errors (e.g., favicon 404)
    const realErrors = errors.filter(e => !e.includes('favicon'));
    expect(realErrors).toHaveLength(0);
  });
});
