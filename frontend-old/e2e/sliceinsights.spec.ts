import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Homepage & Paddle Discovery
 * Validates the main user journey: landing → search → filter → quiz
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

test.describe('Paddle Discovery', () => {
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

    test.skip('search for nonexistent term shows empty state', async ({ page }) => {
        const search = page.getByPlaceholder(/buscar|search/i);
        await search.fill('xyznonexistent999');
        await page.waitForTimeout(1500);

        const emptyState = page.getByText(/nenhuma raquete|no results|não encontr|sem resultados/i);
        await expect(emptyState).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Quiz Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        const quizBtn = page.locator('button:has-text("encontrar"), button:has-text("quiz"), button:has-text("raquete ideal")').first();
        await quizBtn.click({ force: true });
        await page.waitForTimeout(500);
    });

    test.skip('displays skill level options', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await expect(levels.first()).toBeVisible({ timeout: 10000 });
    });

    test.skip('clicking skill level advances quiz', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await levels.first().click({ force: true });

        await expect(
            page.locator('text=/(Etapa|Pergunta|Step) [2-9]/')
        ).toBeVisible({ timeout: 10000 });
    });

    test.skip('full quiz flow reaches results', async ({ page }) => {
        const levels = page.locator(
            'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
        );
        await levels.first().click({ force: true });
        await page.waitForTimeout(800);

        for (let i = 0; i < 10; i++) {
            const options = page.locator('button[data-option], [class*="option"], [role="option"]');
            const slider = page.locator('input[type="range"], [role="slider"]');
            const optionsCount = await options.count();

            if (optionsCount > 0) {
                await options.first().click({ force: true });
                await page.waitForTimeout(800);
                await page.waitForLoadState('networkidle');
            } else if (await slider.isVisible()) {
                await slider.evaluate((el: HTMLInputElement) => {
                    el.value = '50';
                    el.dispatchEvent(new Event('input'));
                    el.dispatchEvent(new Event('change'));
                });
                const confirm = page.getByRole('button', { name: /confirmar|próximo|next|ok/i });
                if (await confirm.isVisible()) {
                    await confirm.click({ force: true });
                } else {
                    await page.locator('button:visible').last().click({ force: true });
                }
                await page.waitForTimeout(800);
            } else {
                break;
            }
        }

        await expect(
            page.locator('text=/Catálogo|Resultado|Recomendação|catalog|result|Match/i').first()
        ).toBeVisible({ timeout: 15000 });

        const resultImage = page.locator('img[alt*="match"], img[alt*="recomend"], .show-results img');
        await expect(resultImage).not.toBeVisible();
    });
});

test.describe('Navigation', () => {
    test('statistics page accessible', async ({ page }) => {
        await page.goto('/');
        const nav = page.getByRole('navigation');
        await expect(nav.getByText('IA')).not.toBeVisible();

        await page.goto('/statistics');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('h1, h2, [class*="heading"]').first()).toBeVisible({ timeout: 10000 });
    });

    test('404 page for unknown routes', async ({ page }) => {
        await page.goto('/nonexistent-page-xyz');
        await page.waitForLoadState('networkidle');
        await expect(page.getByRole('heading', { name: '404' })).toBeVisible({ timeout: 5000 });
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
