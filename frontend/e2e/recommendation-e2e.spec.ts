import { test, expect } from '@playwright/test';

const API = process.env.API_URL || 'http://localhost:8002/api/v1';

test.describe('Recommendation API (E2E-02)', () => {
    test('POST /recommend returns >=1 recommendation with store_url', async ({ request }) => {
        const response = await request.post(`${API}/recommend`, {
            data: {
                skill_level: 'beginner',
                play_style: 'control',
                budget_max_brl: null,
                has_tennis_elbow: false,
                weight_preference: 'no_preference',
                limit: 3,
            },
        });

        expect(response.status()).toBe(200);

        const body = await response.json();
        expect(body.recommendations.length).toBeGreaterThanOrEqual(1);

        for (const rec of body.recommendations) {
            const hasStoreUrl = rec.market_offers?.some(
                (o: any) => o.store_url && typeof o.store_url === 'string' && !['null', '', 'placeholder'].includes(o.store_url)
            );
            expect(hasStoreUrl).toBe(true);
        }
    });

    test('each recommendation has match_reasons with >=1 item >=10 chars', async ({ request }) => {
        const response = await request.post(`${API}/recommend`, {
            data: {
                skill_level: 'beginner',
                play_style: 'control',
                budget_max_brl: null,
                has_tennis_elbow: false,
                weight_preference: 'no_preference',
                limit: 3,
            },
        });

        expect(response.status()).toBe(200);

        const body = await response.json();

        for (const rec of body.recommendations) {
            expect(rec.match_reasons.length).toBeGreaterThanOrEqual(1);
            expect(rec.match_reasons[0].length).toBeGreaterThanOrEqual(10);
        }
    });

    test('recommended paddle_id exists in catalog', async ({ request }) => {
        const recResponse = await request.post(`${API}/recommend`, {
            data: {
                skill_level: 'beginner',
                play_style: 'control',
                budget_max_brl: null,
                has_tennis_elbow: false,
                weight_preference: 'no_preference',
                limit: 3,
            },
        });

        expect(recResponse.status()).toBe(200);

        const recBody = await recResponse.json();
        const firstPaddleId = recBody.recommendations[0].paddle_id;

        const catalogResponse = await request.get(`${API}/catalog/paddles?available_in_brazil=true&limit=100`);
        expect(catalogResponse.status()).toBe(200);

        const catalogBody = await catalogResponse.json();
        const exists = catalogBody.data.some((p: any) => p.id === firstPaddleId);
        expect(exists).toBe(true);
    });
});

test.describe('Recommendation UI (E2E-02)', () => {
    test('quiz UI flow produces >=1 recommendation card', async ({ page }) => {
        await page.goto('/recommend');
        await page.waitForLoadState('networkidle');

        await expect(page.getByText('Qual seu nivel de jogo?')).toBeVisible({ timeout: 10000 });

        await page.getByText('Iniciante').click();
        await page.getByText('Controle').click();
        await page.getByRole('button', { name: 'Proximo' }).click();

        await page.getByText('Sem limite de orcamento').click();
        await page.getByRole('button', { name: 'Proximo' }).click();

        await page.getByText('Sem preferencia').click();
        await page.getByRole('button', { name: 'Ver Recomendacoes' }).click();

        const card = page.locator('[class*="rounded-xl"]').first();
        await expect(card).toBeVisible({ timeout: 45000 });
        await expect(page.getByRole('link', { name: /Comprar/i }).first()).toBeVisible({ timeout: 5000 });
    });
});
