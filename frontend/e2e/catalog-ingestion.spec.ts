import { test, expect } from '@playwright/test';

const API = process.env.API_URL || 'http://localhost:8002/api/v1';

test.describe('Catalog Ingestion (E2E-01)', () => {
    test('catalog/paddles returns >=10 paddles with store_url', async ({ request }) => {
        const response = await request.get(`${API}/catalog/paddles?available_in_brazil=true&limit=50`);
        expect(response.status()).toBe(200);

        const body = await response.json();
        const paddles = body.data as any[];

        expect(body.total).toBeGreaterThanOrEqual(10);

        for (const paddle of paddles) {
            const hasStoreUrl = paddle.market_offers?.some(
                (o: any) => o.store_url && o.store_url.length > 0
            );
            expect(hasStoreUrl).toBe(true);
        }
    });

    test('>=50% of paddles have specs (core_thickness or surface_material)', async ({ request }) => {
        const response = await request.get(`${API}/catalog/paddles?available_in_brazil=true&limit=50`);
        expect(response.status()).toBe(200);

        const body = await response.json();
        const paddles = body.data as any[];

        const withSpecs = paddles.filter(
            (p) =>
                p.specs?.core_thickness_mm != null ||
                p.specs?.surface_material != null ||
                p.specs?.face_material != null
        );

        expect(withSpecs.length).toBeGreaterThanOrEqual(Math.ceil(paddles.length * 0.5));
    });

    test('catalog/stores returns >=1 store with name and base_url', async ({ request }) => {
        const response = await request.get(`${API}/catalog/stores`);
        expect(response.status()).toBe(200);

        const body = await response.json();
        const stores = body.data as any[];

        expect(stores.length).toBeGreaterThanOrEqual(1);

        const store = stores[0];
        expect(store.name).toBeTruthy();
        expect(store.base_url || store.url).toBeTruthy();
    });
});
