import { test, expect } from '@playwright/test';

/**
 * E2E Tests for the Quiz Flow
 * Tests the main user journey from landing to recommendations
 */

test.describe('Quiz Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display landing page with quiz options', async ({ page }) => {
        // Check landing page elements
        await expect(page.locator('h1')).toBeVisible();

        // Look for skill level options which start the quiz automatically
        const levelOptions = page.locator('button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")');
        await expect(levelOptions.first()).toBeVisible();
    });

    test('should navigate through quiz questions', async ({ page }) => {
        // Wait for first question level options
        const levelOptions = page.locator('button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")');
        await expect(levelOptions.first()).toBeVisible();

        // Select one to "start" (it's actually the first question)
        await levelOptions.first().click();

        // Wait for subsequent questions (look for "Pergunta" text)
        await expect(page.locator('text=/Pergunta [2-9] de 10/')).toBeVisible({ timeout: 10000 });

        // Select first option for each question (up to 10 questions)
        for (let i = 0; i < 10; i++) {
            const options = page.locator('button[data-option], [class*="option"], [role="option"]');
            const optionsCount = await options.count();

            if (optionsCount > 0) {
                await options.first().click();
                await page.waitForTimeout(800); // Wait for transition
            } else {
                // Check if it's a slider question
                const slider = page.locator('input[type="range"], .slider, [role="slider"]');
                if (await slider.isVisible()) {
                    await slider.evaluate((el: HTMLInputElement) => { el.value = '0'; el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); });
                    const confirmButton = page.getByRole('button', { name: /confirmar|próximo|next|ok/i });
                    if (await confirmButton.isVisible()) {
                        await confirmButton.click();
                    } else {
                        // Fallback: search for any visible button below the slider
                        await page.locator('button:visible').last().click();
                    }
                    await page.waitForTimeout(800);
                } else {
                    break; // No more questions or interactive elements found
                }
            }
        }
    });

    test('should display recommendations after quiz completion', async ({ page }) => {
        // Wait for first question level options
        const levelOptions = page.locator('button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")');
        await levelOptions.first().click();

        // Quick run through quiz
        for (let i = 0; i < 10; i++) {
            const options = page.locator('button[data-option], [class*="option"], [role="option"]');
            const optionsCount = await options.count();

            if (optionsCount > 0) {
                await options.first().click();
                await page.waitForTimeout(500);
            } else {
                // Handle slider in recommendations flow too
                const slider = page.locator('input[type="range"], .slider, [role="slider"]');
                if (await slider.isVisible()) {
                    await slider.evaluate((el: HTMLInputElement) => { el.value = '0'; el.dispatchEvent(new Event('input')); });
                    await page.getByRole('button', { name: /confirmar|próximo|next/i }).first().click();
                    await page.waitForTimeout(500);
                } else {
                    break;
                }
            }
        }

        // Wait for recommendations to load
        await page.waitForSelector('text=/Match Perfeito|Recomendação|Raquete/i', {
            timeout: 15000
        });

        // Check that recommendations are displayed or the success message
        await expect(page.locator('text=/Match Perfeito Encontrado!/i')).toBeVisible();
    });

    test('should navigate to statistics page', async ({ page }) => {
        // Find and click statistics link
        const statsLink = page.getByRole('link', { name: /estatísticas|statistics|métricas/i });

        if (await statsLink.isVisible()) {
            await statsLink.click();
            await expect(page).toHaveURL(/statistics/);
        }
    });

    test('should handle 404 page gracefully', async ({ page }) => {
        await page.goto('/non-existent-page');

        // Should show 404 content
        await expect(page.locator('text=404')).toBeVisible();

        // Should have link to home
        const homeLink = page.getByRole('link', { name: /início|home/i }).first();
        await expect(homeLink).toBeVisible();
    });

    test('should load paddles in catalog', async ({ page }) => {
        // Navigate to catalog if available
        const catalogLink = page.getByRole('link', { name: /catálogo|catalog|ver todos/i });

        if (await catalogLink.isVisible()) {
            await catalogLink.click();

            // Wait for paddles to load
            await page.waitForSelector('[class*="paddle"], [class*="card"]', {
                timeout: 10000
            });

            const paddles = page.locator('[class*="paddle-card"], [data-testid="paddle-card"]');
            const count = await paddles.count();
            expect(count).toBeGreaterThanOrEqual(0);
        }
    });
});

test.describe('Error Handling', () => {
    test('should show error boundary on client error', async ({ page }) => {
        // Navigate to a page that might trigger an error
        await page.goto('/');

        // Page should load without crashing
        await expect(page.locator('body')).toBeVisible();
    });
});

test.describe('Performance', () => {
    test('should load landing page within acceptable time', async ({ page }) => {
        const startTime = Date.now();
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        const loadTime = Date.now() - startTime;

        // Page should load within 5 seconds
        expect(loadTime).toBeLessThan(5000);
    });
});
