import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Viewport Responsiveness
 * Validates that the 3 target pages render correctly across mobile, tablet, and desktop viewports.
 * Run via Playwright projects: desktop, mobile, tablet (see playwright.config.ts).
 */

const routes = ['/', '/recommend', '/statistics'];

for (const route of routes) {
    test.describe(`Responsiveness: ${route}`, () => {
        test(`renders without horizontal overflow`, async ({ page }) => {
            await page.goto(route);
            await page.waitForLoadState('networkidle');
            await expect(page.locator('h1').first()).toBeVisible({ timeout: 15000 });

            const hasOverflow = await page.evaluate(() =>
                document.documentElement.scrollWidth > window.innerWidth
            );
            expect(hasOverflow).toBe(false);
        });

        test(`main content is visible`, async ({ page }) => {
            await page.goto(route);
            await page.waitForLoadState('networkidle');
            await expect(page.locator('main').first()).toBeVisible({ timeout: 15000 });
        });
    });
}

// Additional mobile-specific interaction tests
test(`/recommend buttons are accessible at mobile viewport`, async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/recommend');
    await page.waitForLoadState('networkidle');
    // Verify at least one button is visible and clickable
    const buttons = page.getByRole('button');
    await expect(buttons.first()).toBeVisible({ timeout: 15000 });
});

test(`/ displays cards at mobile viewport`, async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const cards = page.locator('[class*="card"], [class*="grid"] > div');
    await expect(cards.first()).toBeVisible({ timeout: 15000 });
});
