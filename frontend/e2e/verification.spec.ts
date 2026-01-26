import { test, expect } from '@playwright/test';

test.describe('Production Verification (Smoke Test)', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('Should load Homepage with correct branding', async ({ page }) => {
        // Allow fuzzy matching for flexibility
        await expect(page).toHaveTitle(/SliceInsights/i);

        const heading = page.locator('h1');
        await expect(heading).toBeVisible();
        // Should contain brand name
        await expect(heading).toContainText(/SliceInsights/i);
    });

    test('Should display interactive elements (Quiz or Catalog)', async ({ page }) => {
        // Check for buttons suitable for interaction
        const interactiveElement = page.locator('button, a[href*="quiz"], a[href*="paddles"]').first();
        await expect(interactiveElement).toBeVisible();
    });
});
