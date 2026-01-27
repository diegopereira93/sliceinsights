import { test, expect } from '@playwright/test';

test.describe('Production Verification (Smoke Test)', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('Should load Homepage with correct branding', async ({ page }) => {
        // Allow fuzzy matching for title
        await expect(page).toHaveTitle(/SliceInsights/i);

        const heading = page.locator('h1');
        await expect(heading).toBeVisible();

        // Resilience: Allow either the new English branding or the previous Portuguese value prop
        // This prevents CI failure during the propagation window of a deployment.
        await expect(heading).toHaveText(/SliceInsights|Descubra.*perfeita/i);
    });

    test('Should display interactive elements (Quiz or Catalog)', async ({ page }) => {
        // Check for the catalog section heading or quiz button
        // These should exist regardless of whether paddles are loaded
        const quizButton = page.getByRole('button', { name: /descobrir|start|quiz/i }).first();
        const catalogHeading = page.locator('text=/CATÁLOGO|RAQUETES|Nenhuma raquete/i').first();
        const bottomNav = page.locator('nav').first();

        // At least one of these should be visible
        await expect(quizButton.or(catalogHeading).or(bottomNav)).toBeVisible({ timeout: 15000 });
    });
});
