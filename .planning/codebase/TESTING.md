# Testing Patterns

**Analysis Date:** 2026-03-19

## Test Framework

**Runner:**
- Playwright v1.40.0 - E2E testing framework
- Config: `frontend/playwright.config.ts`

**Assertion Library:**
- Playwright's built-in expect API (`expect()` from `@playwright/test`)

**Run Commands:**
```bash
playwright test                    # Run all Playwright tests
playwright test --ui              # Interactive UI mode
npx playwright test --debug       # Debug mode with step-through
playwright show-report            # View HTML test report
```

**Test Location:**
- E2E tests: `frontend/e2e/sliceinsights.spec.ts`
- Test data: No unit test files detected; project uses E2E-focused testing

## Test File Organization

**Location:**
- Playwright E2E tests co-located in `frontend/e2e/` directory
- Pattern: separate from source code but within frontend package

**Naming:**
- File suffix: `.spec.ts`
- Example: `sliceinsights.spec.ts`

**Structure:**
```
frontend/e2e/
└── sliceinsights.spec.ts     # Main E2E test suite with multiple describe blocks
```

## Test Structure

**Suite Organization:**
```typescript
test.describe('Homepage', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('loads with correct title', async ({ page }) => {
        await expect(page).toHaveTitle(/SliceInsights/i);
    });
});

test.describe('Catalog', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('displays paddle cards from API', async ({ page }) => {
        const cards = page.locator('[class*="card"], [class*="grid"] > div');
        await expect(cards.first()).toBeVisible({ timeout: 15000 });
        const count = await cards.count();
        expect(count).toBeGreaterThan(0);
    });
});
```

**Patterns:**
- Setup with `test.beforeEach()`: Navigation, waits for load state
- Teardown: Implicit (Playwright clears browser state between tests)
- Assertions: Synchronous (`expect()`) and async (`await expect()`)
- Timeouts: Explicit (e.g., `{ timeout: 15000 }`) for slower operations

## Mocking

**Framework:**
- No explicit mocking library—tests hit real backend API
- Environment variable: `API = process.env.API_URL || 'http://localhost:8002/api/v1'`

**Patterns:**
```typescript
test('API contract (via fetch)', async ({ request }) => {
    const r = await request.get(`${API}/health`);
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(body.status).toBe('healthy');
});
```

**What to Mock:**
- No mocking observed—tests verify real API endpoints (health, brands, paddles, search, recommendations)

**What NOT to Mock:**
- Frontend rendering is tested without mocking backend responses
- API contract tests explicitly call real endpoints to ensure compatibility

## Fixtures and Factories

**Test Data:**
```typescript
const API = process.env.API_URL || 'http://localhost:8002/api/v1';

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
});
```

**Location:**
- Test data embedded inline in test cases
- No separate fixtures file
- Uses realistic payload structures matching API contracts

## Coverage

**Requirements:**
- No coverage enforcement detected; no jest/vitest config found
- E2E tests focus on critical user journeys: homepage → catalog → search → detail → quiz → API contracts

**View Coverage:**
- No coverage reporting configured
- Tests validate happy path and error conditions but lack formal coverage metrics

## Test Types

**Unit Tests:**
- Not found in codebase
- Backend services (RecommendationEngine, LLMService) lack unit test coverage

**Integration Tests:**
- E2E tests double as integration tests, hitting real API endpoints
- Example: `test('paddles endpoint returns data with images')` validates full data pipeline

**E2E Tests:**
- Framework: Playwright
- Scope: Full user workflows from page load through interaction
- Coverage areas:
  - Homepage rendering and navigation
  - Catalog display and filtering
  - Search functionality
  - Quiz flow (step progression, result delivery)
  - API contract validation (health, brands, paddles, recommendations)

## Test Suites

**Homepage:**
- Title validation
- Heading visibility
- Navigation presence
- Load time (<5 seconds)

**Catalog:**
- Paddle card rendering
- Search input presence
- Search filtering (Joola brand, nonexistent term)
- Empty state display

**Quiz Flow:**
- Skill level options rendered
- Quiz progression (clicking advances steps)
- Full 10-question flow to results

**Navigation:**
- Statistics page accessibility
- 404 error handling

**API Contract:**
- Health endpoint: status=200, body.status='healthy'
- Brands endpoint: returns array of brands
- Paddles endpoint: returns paddle objects with image_url and availability
- Search endpoint: query-based filtering
- Recommendations endpoint: POST with skill/style/budget parameters

## Common Patterns

**Async Testing:**
```typescript
test('full quiz flow reaches results', async ({ page }) => {
    const levels = page.locator(
        'button:has-text("Iniciante"), button:has-text("Intermediário"), button:has-text("Avançado")'
    );
    await levels.first().click();

    for (let i = 0; i < 10; i++) {
        const options = page.locator('button[data-option], [class*="option"], [role="option"]');
        if (optionsCount > 0) {
            await options.first().click();
            await page.waitForTimeout(600);  // Debounce wait
        }
    }

    await expect(
        page.locator('text=/Catálogo|Resultado/i').first()
    ).toBeVisible({ timeout: 15000 });
});
```

**Selectors:**
- Role-based: `page.getByRole('button', { name: /encontrar minha raquete/i })`
- Placeholder-based: `page.getByPlaceholder(/buscar|search/i)`
- Locator patterns: `page.locator('h1')`, `page.locator('[class*="card"]')`
- Case-insensitive regex: `/nenhuma raquete|no results/i`

**Waits:**
- Page load: `await page.waitForLoadState('networkidle')`
- Visibility: `await expect(element).toBeVisible({ timeout: 15000 })`
- Custom delay: `await page.waitForTimeout(1500)` for debounce/animation

**Error Testing:**
```typescript
test('search for nonexistent term shows empty state', async ({ page }) => {
    const search = page.getByPlaceholder(/buscar|search/i);
    await search.fill('xyznonexistent999');
    await page.waitForTimeout(1500);

    const emptyState = page.getByText(/nenhuma raquete|no results|não encontr/i);
    await expect(emptyState).toBeVisible({ timeout: 5000 });
});
```

## Test Configuration

**Playwright Config Location:**
- `frontend/playwright.config.ts`

**Environment Variables:**
- `API_URL`: Backend API endpoint (defaults to `http://localhost:8002/api/v1`)
- Browser: Chromium (default, no explicit override)
- Base URL: Not hardcoded; tests navigate using relative paths (e.g., `/`, `/statistics`)

## Gaps and Observations

- **No unit tests** for backend services or React components
- **No snapshot testing** observed
- **No API mocking** — tests depend on running backend
- **Manual test data** — no factories or seeders for test database
- **Portuguese-only selectors** — regex patterns for Brazilian Portuguese UI text
- **No CI/CD test reporting** detected in github workflows (may exist but not in primary test files)

---

*Testing analysis: 2026-03-19*
