import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8002';

test.describe('API Compatibility', () => {
  test('GET /api/healthz returns status ok', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/healthz`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
  });

  test('GET /api/paddles returns PaddleListResponse', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/paddles`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('paddles');
    expect(body).toHaveProperty('total');
    expect(Array.isArray(body.paddles)).toBe(true);
    if (body.paddles.length > 0) {
      const paddle = body.paddles[0];
      expect(paddle).toHaveProperty('id');
      expect(paddle).toHaveProperty('name');
      expect(paddle).toHaveProperty('brand');
      expect(paddle).toHaveProperty('powerScore');
      expect(paddle).toHaveProperty('controlScore');
      expect(typeof paddle.id).toBe('number');
    }
  });

  test('GET /api/paddles supports query params', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/paddles?limit=5&offset=0`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.paddles.length).toBeLessThanOrEqual(5);
  });

  test('GET /api/stats/market returns MarketStats', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/stats/market`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('totalPaddles');
    expect(body).toHaveProperty('averagePrice');
    expect(body).toHaveProperty('coreThicknessDistribution');
    expect(body).toHaveProperty('priceRangeDistribution');
    expect(body).toHaveProperty('powerVsControlData');
    expect(typeof body.totalPaddles).toBe('number');
  });

  test('GET /api/stats/brands returns BrandStat array', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/stats/brands`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
    if (body.length > 0) {
      expect(body[0]).toHaveProperty('brand');
      expect(body[0]).toHaveProperty('count');
      expect(body[0]).toHaveProperty('avgPrice');
      expect(body[0]).toHaveProperty('marketShare');
    }
  });

  test('GET /api/stats/hidden-gems returns Paddle array', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/stats/hidden-gems`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test('POST /api/leads accepts LeadInput', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/leads`, {
      data: {
        name: 'E2E Test User',
        email: `e2e-test-${Date.now()}@example.com`,
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('success');
    expect(body.success).toBe(true);
  });
});
