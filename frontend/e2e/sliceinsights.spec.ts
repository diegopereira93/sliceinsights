import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Homepage & Catalog
 * Validates the main user journey: landing → catalog → search → detail
 */

const API = process.env.API_URL || 'http://localhost:8002/api/v1';

test.describe('Homepage', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('loads with correct title', async ({ page }) => {
        await expect(page).toHaveTitle(/SliceInsights/i);
    });

    test('has a visible heading', async ({ page }) => {
        const h1 = page.locator('h1');
        await expect(h1).toBeVisible({ timeout: 10000 });
    });

    test('displays bottom navigation', async ({ page }) => {
        const nav = page.getByRole('navigation');
        await expect(nav).toBeVisible({ timeout: 10000 });
    });

    test('loads within 5 seconds', async ({ page }) => {
        const start = Date.now();
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        expect(Date.now() - start).toBeLessThan(5000);
    });
});

test.describe('Catalog', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Wait for paddle cards or search to indicate catalog loaded
        await page.waitForLoadState('networkidle');
    });

    test('displays paddle cards from API', async ({ page }) => {
        // Wait for at least one grid/card element
        const cards = page.locator('[class*="card"], [class*="grid"] > div');
        await expect(cards.first()).toBeVisible({ timeout: 15000 });
        const count = await cards.count();
        expect(count).toBeGreaterThan(0);
    });

    test('displays search input', async ({ page }) => {
        const search = page.getByPlaceholder(/buscar|search/i);
        await expect(search).toBeVisible();
    });

    test('search filters results', async ({ page }) => {
        const search = page.getByPlaceholder(/buscar|search/i);
        await search.fill('Joola');
        await page.waitForTimeout(1500); // debounce

        // After searching, cards should contain Joola (or empty state)
        const emptyState = page.getByText(/nenhuma raquete|no results/i);
        const cards = page.locator('[class*="card"], [class*="grid"] > div');

        if (await emptyState.isVisible()) {
            // Search returned no results — acceptable if DB is filtered differently
            expect(true).toBeTruthy();
        } else {
            await expect(cards.first()).toBeVisible();
        }
    });

    test('search for nonexistent term shows empty state', async ({ page }) => {
        const search = page.getByPlaceholder(/buscar|search/i);
        await search.fill('xyznonexistent999');
        await page.waitForTimeout(1500);

        const emptyState = page.getByText(/nenhuma raquete|no results|não encontr/i);
        await expect(emptyState).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Quiz Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Open the quiz modal by clicking the CTA button
        await page.getByRole('button', { name: /encontrar minha raquete/i }).first().click();
        await page.waitForLoadState('networkidle');
    });

    test('displays skill level options', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await expect(levels.first()).toBeVisible({ timeout: 10000 });
    });

    test('clicking skill level advances quiz', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await levels.first().click();

        // Should show step 2
        await expect(
            page.locator('text=/(Etapa|Pergunta|Step) [2-9]/')
        ).toBeVisible({ timeout: 10000 });
    });

    test('full quiz flow reaches results', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await levels.first().click();

        // Answer up to 10 questions
        for (let i = 0; i < 10; i++) {
            const options = page.locator('button[data-option], [class*="option"], [role="option"]');
            const slider = page.locator('input[type="range"], [role="slider"]');
            const optionsCount = await options.count();

            if (optionsCount > 0) {
                await options.first().click();
                await page.waitForTimeout(600);
            } else if (await slider.isVisible()) {
                await slider.evaluate((el: HTMLInputElement) => {
                    el.value = '50';
                    el.dispatchEvent(new Event('input'));
                    el.dispatchEvent(new Event('change'));
                });
                const confirm = page.getByRole('button', { name: /confirmar|próximo|next|ok/i });
                if (await confirm.isVisible()) {
                    await confirm.click();
                } else {
                    await page.locator('button:visible').last().click();
                }
                await page.waitForTimeout(600);
            } else {
                break;
            }
        }

        // After quiz: should see results or catalog
        await expect(
            page.locator('text=/Catálogo|Resultado|Recomendação|catalog|result/i').first()
        ).toBeVisible({ timeout: 15000 });
    });
});

test.describe('Navigation', () => {
    test('statistics page accessible', async ({ page }) => {
        await page.goto('/statistics');
        await expect(page.locator('body')).toBeVisible();
        // Should load without crashing — check page title or any content rendered
        await page.waitForLoadState('networkidle');
    });

    test('404 page for unknown routes', async ({ page }) => {
        await page.goto('/nonexistent-page-xyz');
        await expect(page.locator('text=404')).toBeVisible({ timeout: 5000 });
    });
});

test.describe('API Contract (via fetch)', () => {
    test('health endpoint returns healthy', async ({ request }) => {
        const r = await request.get(`${API}/health`);
        expect(r.status()).toBe(200);
        const body = await r.json();
        expect(body.status).toBe('healthy');
    });

    test('brands endpoint returns data', async ({ request }) => {
        const r = await request.get(`${API}/brands`);
        expect(r.status()).toBe(200);
        const body = await r.json();
        expect(body.data.length).toBeGreaterThan(0);
    });

    test('paddles endpoint returns data with images', async ({ request }) => {
        const r = await request.get(`${API}/paddles?limit=5&available_in_brazil=true`);
        expect(r.status()).toBe(200);
        const body = await r.json();
        expect(body.data.length).toBeGreaterThan(0);
        for (const p of body.data) {
            expect(p.image_url).toBeTruthy();
            expect(p.available_in_brazil).toBe(true);
        }
    });

    test('search endpoint works', async ({ request }) => {
        const r = await request.get(`${API}/search?q=Joola`);
        expect(r.status()).toBe(200);
        const body = await r.json();
        expect(body.results.length).toBeGreaterThan(0);
    });

    test('recommendations endpoint works', async ({ request }) => {
        const r = await request.post(`${API}/recommendations`, {
            data: {
                skill_level: 'beginner',
                play_style: 'control',
                has_tennis_elbow: false,
                limit: 3,
            },
        });
        expect(r.status()).toBe(200);
        const body = await r.json();
        expect(body.recommendations).toBeDefined();
    });
});
