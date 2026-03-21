# Phase 14: Web Catalog Page - Research

**Researched:** 2026-03-21
**Domain:** Next.js 14 + TypeScript — catalog page with server-side initial load, client-side filtered fetch, URL-synced state
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Next.js 14 + TypeScript** — build in existing `frontend/`, NOT Jinja2
- **New route**: `frontend/app/catalog/page.tsx` — dedicated URL `/catalog`, does not replace home
- **Tailwind CSS** already configured — use existing design tokens
- **Dark mode already implemented**: bg `#000000`, accent `#ceff00` (lime), muted `#111111`, border `#222222`
- **React state + fetch with ~400ms debounce** — each filter change fires fetch to `/catalog/paddles` after 400ms pause
- **URL reflects active filters** via `useSearchParams` + `useRouter` — shareable links, back button works
- **Auto-apply on change** — no explicit "Filter" button; Airbnb-style fluid experience
- **Skeleton cards during load** — pulsing grey cards using `bg-muted animate-pulse` (no extra library)
- **Grid**: 3 cols desktop, 2 tablet, 1 mobile
- **Card info**: Photo + Name + Brand badge + Thickness badge + "A partir de" price + "Ver na [Store]" button
- **Paddles without image_url are filtered** — applied in API query (`image_url IS NOT NULL`)
- **"Ver na [StoreName]" button**: opens in new tab, uses cheapest `MarketOffer` URL
- **Filter drawer** (`filter-drawer.tsx`) is project standard — bottom sheet on mobile
- **Required filters**: thickness (14mm/16mm), surface material (Carbon/Fiberglass), price range, brand (multi-select+search), store (select)
- **Extend** `filter-drawer.tsx`: add `surface_material` and `store` slug filters
- **Visual**: follow `paddle-card.tsx` patterns (glass-card, hover ring primary, framer-motion)
- **Skeleton**: `bg-muted animate-pulse` same proportions as real cards

### Claude's Discretion
- Desktop filter layout: fixed sidebar left (new pattern) vs. keep drawer for all sizes
- Pagination vs. infinite scroll (API supports `limit`/`offset`)
- Default sort order (ascending price recommended)
- Empty state when no paddles match filters

### Deferred Ideas (OUT OF SCOPE)
- Fixed sidebar for filters on desktop (may be Phase 15+)
- Paddle comparator activated in catalog page
- User-controlled sort (price, rating, brand)
- Infinite scroll
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WEB-01 | User accesses catalog web page with paddle listing | Server Component SSR pattern + `getApiBaseUrl()` + catalog endpoint `/catalog/paddles` |
| WEB-02 | Page displays filter controls (thickness, material, price, brand, store) | Extend existing `filter-drawer.tsx` with `surface_material` + `store` params |
| WEB-03 | Page updates listing dynamically when filters applied | `useSearchParams`/`useRouter` URL sync + debounced client-side fetch |
</phase_requirements>

---

## Summary

Phase 14 builds on a mature Next.js 14 frontend that already has the core building blocks in place. The `paddle-card.tsx`, `filter-drawer.tsx`, `bottom-nav.tsx`, and the Server Component + Client Component split pattern are all established and consistent. The catalog page follows the same split used in `app/page.tsx`: a Server Component (`catalog/page.tsx`) performs the SSR initial fetch from the Catalog API, then passes data to a `CatalogClient` component that owns all interactive state.

The key distinction from the home page is that filter changes must (a) update URL query params for shareability and (b) trigger a debounced re-fetch to the new `/catalog/paddles` endpoint — not client-side array filtering of a pre-loaded dataset. The Catalog API (`app/api/endpoints/catalog.py`) is already complete and supports all required query parameters: `core_thickness`, `surface_material`, `price_min`, `price_max`, `brand`, `store`, `limit`, `offset`.

The `filter-drawer.tsx` component needs two new filter sections: `surface_material` (badge toggle: Carbon / Fiberglass) and `store` (select from `/catalog/stores` response). The `Paddle` type and `mapBackendToFrontendPaddle` mapper in `lib/api.ts` use the OLD `/api/v1/paddles` response shape; the catalog page must define its own `CatalogPaddle` type matching the new `/catalog/paddles` response shape (no `ratings`, no `specs.swing_weight`, but includes `market_offers[]`).

**Primary recommendation:** Server Component for SSR initial load + `CatalogClient` for interactivity, new `CatalogPaddle` type, extend `FilterDrawer` with two new sections, debounce URL param updates, render "Ver na [StoreName]" from `market_offers[0]` (cheapest, already sorted by API).

---

## Standard Stack

### Core (already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14 | Routing, SSR, Server Components | Project standard |
| React | 18 | UI, hooks (`useState`, `useEffect`, `useCallback`) | Project standard |
| TypeScript | 5 | Type safety | Project standard |
| Tailwind CSS | 3 | Styling with design tokens | Already configured |
| framer-motion | installed | Card entrance animations | Already in use in `paddle-card.tsx` |
| `@radix-ui/react-slider` | installed | Price range slider | Already in `filter-drawer.tsx` |
| shadcn/ui | installed | Card, Button, Badge, Skeleton, Drawer, Separator, Input | All used by existing components |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `use-debounce` | check if installed | `useDebouncedCallback` for filter fetch | If present, use it; otherwise `setTimeout`/`clearTimeout` |
| lucide-react | installed | Icons (Filter, Search, X, Check, ExternalLink) | Icon consistency |

**Check if `use-debounce` is installed:**
```bash
cat frontend/package.json | grep use-debounce
```
If not present, implement debounce with `useRef` + `setTimeout`/`clearTimeout` (no new dependency needed).

**No new packages required** — all tooling is in place.

---

## Architecture Patterns

### Recommended Project Structure
```
frontend/app/catalog/
├── page.tsx              # Server Component — SSR initial fetch + read searchParams
└── catalog-client.tsx    # Client Component — filter state, URL sync, debounced fetch

frontend/components/paddle/
├── paddle-card.tsx       # EXTEND: add "Ver na [Store]" button (new prop: cheapestOffer)
└── filter-drawer.tsx     # EXTEND: add surface_material + store filter sections

frontend/types/
└── catalog.ts            # NEW: CatalogPaddle, CatalogStore, CatalogFilters types

frontend/lib/
└── catalog-api.ts        # NEW: fetchCatalogPaddles(), fetchCatalogStores() functions
```

### Pattern 1: Server Component → Client Component Split
**What:** `page.tsx` is async, fetches initial data from Catalog API using `searchParams` prop, passes to `CatalogClient`.
**When to use:** Any page requiring both SEO/initial render and client interactivity.

```typescript
// frontend/app/catalog/page.tsx — Server Component
import { fetchCatalogPaddles, fetchCatalogStores } from '@/lib/catalog-api';
import CatalogClient from './catalog-client';

export const revalidate = 3600;

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[]>;
}) {
  const filters = parseCatalogFilters(searchParams); // extract known params
  const [paddlesRes, storesRes] = await Promise.all([
    fetchCatalogPaddles(filters),
    fetchCatalogStores(),
  ]);
  return (
    <CatalogClient
      initialPaddles={paddlesRes.data}
      initialTotal={paddlesRes.total}
      stores={storesRes.data}
      initialFilters={filters}
    />
  );
}
```

### Pattern 2: URL-Synced Filter State with Debounced Fetch
**What:** Filter changes update URL params (for shareability) and trigger a debounced API call.
**When to use:** Any filter-driven listing that needs shareable URLs and back-button support.

```typescript
// Inside CatalogClient
const router = useRouter();
const searchParams = useSearchParams();
const debounceRef = useRef<NodeJS.Timeout>();

const updateFilters = (newFilters: Partial<CatalogFilters>) => {
  const merged = { ...filters, ...newFilters };
  setFilters(merged);
  setIsLoading(true);

  // Update URL (shallow — no server roundtrip)
  const params = new URLSearchParams();
  if (merged.brand) params.set('brand', merged.brand);
  if (merged.core_thickness) params.set('core_thickness', merged.core_thickness.toString());
  if (merged.surface_material) params.set('surface_material', merged.surface_material);
  if (merged.price_min) params.set('price_min', merged.price_min.toString());
  if (merged.price_max) params.set('price_max', merged.price_max.toString());
  if (merged.store) params.set('store', merged.store);
  router.replace(`/catalog?${params.toString()}`, { scroll: false });

  // Debounced fetch
  clearTimeout(debounceRef.current);
  debounceRef.current = setTimeout(async () => {
    const res = await fetchCatalogPaddles({ ...merged, limit: PAGE_SIZE, offset: 0 });
    setPaddles(res.data);
    setTotal(res.total);
    setIsLoading(false);
  }, 400);
};
```

### Pattern 3: New CatalogPaddle Type (distinct from existing Paddle)
**What:** The `/catalog/paddles` response shape differs from `/api/v1/paddles`. Define a new type; do NOT reuse `mapBackendToFrontendPaddle`.

```typescript
// frontend/types/catalog.ts
export interface CatalogOffer {
  store_name: string;
  price_brl: number;
  store_url: string;
}

export interface CatalogPaddle {
  id: string;
  brand: string | null;
  model_name: string;
  specs: {
    core_thickness_mm: number | null;
    surface_material: string | null;
  };
  market_offers: CatalogOffer[]; // sorted by price asc (API guarantees this)
}

export interface CatalogStore {
  id: number;
  name: string;
  slug: string;
  base_url: string;
  is_active: boolean;
  available_brands: string[];
}

export interface CatalogFilters {
  core_thickness?: number;
  surface_material?: string;
  price_min?: number;
  price_max?: number;
  brand?: string;
  store?: string;
}
```

### Pattern 4: Skeleton Grid
**What:** While `isLoading` is true, render N skeleton cards matching real card proportions.
**When to use:** Any async data fetch replacing a grid.

```typescript
// No external library — pure Tailwind
function PaddleCardSkeleton() {
  return (
    <div className="rounded-xl overflow-hidden glass-card">
      <div className="aspect-[4/5] bg-muted animate-pulse" />
      <div className="p-6 space-y-3">
        <div className="h-4 bg-muted animate-pulse rounded w-2/3" />
        <div className="h-4 bg-muted animate-pulse rounded w-1/3" />
        <div className="h-8 bg-muted animate-pulse rounded" />
      </div>
    </div>
  );
}
```

### Pattern 5: "Ver na [StoreName]" Button Extension
**What:** Add a store CTA to `PaddleCard`. The cheapest offer is `market_offers[0]` (API sorts by price asc).
**Implementation:** Add optional `cheapestOffer?: CatalogOffer` prop OR create a new `CatalogPaddleCard` that wraps/extends the existing card.
**Recommendation:** Create a dedicated `CatalogPaddleCard` (composition over mutation) to avoid breaking the home page's existing `PaddleCard` interface.

```typescript
// CatalogPaddleCard uses PaddleCard layout + adds the store button
<a href={cheapestOffer.store_url} target="_blank" rel="noopener noreferrer">
  <Button size="sm" className="rounded-xl font-black text-xs">
    <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
    Ver na {cheapestOffer.store_name}
  </Button>
</a>
```

### Pattern 6: Pagination (recommended over infinite scroll)
**What:** Simple "Próxima página" / "Página anterior" controls or numbered pages.
**Why pagination over infinite scroll:** API returns `total` + `limit`/`offset`; simpler to implement, better for URL shareability, back button restores page position naturally.
**Recommended default:** 24 paddles per page (`limit=24`), `offset` tracked in state and URL (`?page=2`).

### Anti-Patterns to Avoid
- **Client-side filtering of full dataset:** Home page does this (`useMemo` filter). Catalog page must NOT — data comes from the Catalog API per query. The API is the source of truth for filtering.
- **Reusing `mapBackendToFrontendPaddle`:** It maps `/api/v1/paddles` shape with synthetic ratings. Catalog API response has no `ratings` block — using the mapper will produce garbage values.
- **Mutating `filter-drawer.tsx` props interface without backward compatibility:** Home page still uses `FilterDrawer`. Add new props as optional with defaults to avoid breaking home.
- **Calling `/catalog/paddles` without `image_url IS NOT NULL`:** The API does NOT currently filter by image_url. Either (a) add `image_url` to the catalog endpoint response and filter client-side, or (b) add a server-side filter. CONTEXT.md says "filter applied in query" — verify this is implemented in the API before assuming it works.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Price range slider | Custom range input | `@radix-ui/react-slider` (already in `filter-drawer.tsx`) | Accessibility, touch support, existing styled |
| Debounce | Complex scheduler | `useRef` + `setTimeout` or `useDebouncedCallback` from `use-debounce` | One-liner, tested |
| Drawer/bottom sheet | Custom modal | shadcn/ui `Drawer` (already in `filter-drawer.tsx`) | Vaul-based, handles mobile gestures |
| Skeleton shimmer | Complex CSS animation | `bg-muted animate-pulse` (Tailwind built-in) | Already available, consistent with brand |
| URL param parsing | Custom querystring parser | `useSearchParams()` + `URLSearchParams` (Next.js built-in) | SSR-safe, handles encoding |
| Empty state | Custom component | `components/ui/empty-state.tsx` (already exists) | Consistent UX |

---

## Common Pitfalls

### Pitfall 1: `image_url` filtering gap
**What goes wrong:** CONTEXT.md states paddles without `image_url` should be filtered — but the current `catalog.py` endpoint does NOT include `image_url` in the response and does NOT filter by it.
**Why it happens:** The API was built for the catalog data layer; image filtering was a frontend UX decision added later.
**How to avoid:** Either add `WHERE paddle.image_url IS NOT NULL` to the catalog query (backend change, Wave 0 task) OR filter client-side after receiving the response (`paddles.filter(p => p.image_url)`). The API response currently does NOT include `image_url` in the paddle object — this field must be added to the endpoint response.
**Warning signs:** Cards showing placeholder images in the catalog grid.

### Pitfall 2: `useSearchParams()` requires Suspense boundary
**What goes wrong:** In Next.js 14, any component calling `useSearchParams()` must be wrapped in `<Suspense>`. Missing this causes a build error or runtime warning.
**Why it happens:** Next.js App Router requirement for client components accessing search params.
**How to avoid:** Wrap `CatalogClient` in `<Suspense fallback={<CatalogSkeleton />}>` inside `page.tsx`.

```typescript
// page.tsx
import { Suspense } from 'react';
export default async function CatalogPage({ searchParams }) {
  return (
    <Suspense fallback={<CatalogGridSkeleton />}>
      <CatalogClient ... />
    </Suspense>
  );
}
```

### Pitfall 3: FilterDrawer props extension breaks home page
**What goes wrong:** Adding required props to `FilterDrawer` causes TypeScript errors in the home page where `FilterDrawer` is also used.
**Why it happens:** `FilterDrawer` is a shared component.
**How to avoid:** Make new props (`surfaceMaterialFilter`, `onSurfaceMaterialChange`, `storeFilter`, `onStoreChange`, `stores`) optional with sensible defaults (`undefined` / no-op).

### Pitfall 4: Debounce + unmount memory leak
**What goes wrong:** If the component unmounts while a debounce timeout is pending, the state update fires on an unmounted component.
**How to avoid:** Clear the timeout in a `useEffect` cleanup:
```typescript
useEffect(() => {
  return () => clearTimeout(debounceRef.current);
}, []);
```

### Pitfall 5: `brand` filter is string (single) not array
**What goes wrong:** The catalog API `brand` param accepts a single string with `ilike` match — not a multi-value array. The home page supports multi-brand client filtering; the catalog page must adapt to the API constraint.
**How to avoid:** For Phase 14, the brand filter is a single-select or type-ahead (matching ONE brand at a time). Multi-brand is deferred or requires a backend change.

### Pitfall 6: Navigation link missing
**What goes wrong:** `/catalog` route exists but is unreachable from the app's navigation.
**How to avoid:** Add `<NavItem href="/catalog" icon={ShoppingBag} label="Catálogo" ...>` to `bottom-nav.tsx`.

---

## Code Examples

### Fetch function for catalog API
```typescript
// frontend/lib/catalog-api.ts
import { getApiBaseUrl } from '@/lib/api';
import { CatalogPaddle, CatalogStore, CatalogFilters } from '@/types/catalog';

export async function fetchCatalogPaddles(
  filters: CatalogFilters & { limit?: number; offset?: number } = {}
): Promise<{ data: CatalogPaddle[]; total: number; limit: number; offset: number }> {
  const params = new URLSearchParams();
  if (filters.core_thickness) params.set('core_thickness', filters.core_thickness.toString());
  if (filters.surface_material) params.set('surface_material', filters.surface_material);
  if (filters.price_min != null) params.set('price_min', filters.price_min.toString());
  if (filters.price_max != null) params.set('price_max', filters.price_max.toString());
  if (filters.brand) params.set('brand', filters.brand);
  if (filters.store) params.set('store', filters.store);
  if (filters.limit) params.set('limit', filters.limit.toString());
  if (filters.offset) params.set('offset', filters.offset.toString());

  const url = `${getApiBaseUrl().replace('/api/v1', '')}/catalog/paddles?${params}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch catalog paddles');
  return res.json();
}

export async function fetchCatalogStores(): Promise<{ data: CatalogStore[]; total: number }> {
  const url = `${getApiBaseUrl().replace('/api/v1', '')}/catalog/stores`;
  const res = await fetch(url, { next: { revalidate: 86400 } }); // stores change rarely
  if (!res.ok) throw new Error('Failed to fetch catalog stores');
  return res.json();
}
```

**Important:** The catalog router is mounted at `/catalog` (prefix in `catalog.py`), NOT under `/api/v1`. Verify the router registration in `app/main.py` — the base URL construction must strip `/api/v1` if catalog is at the root.

### Store select in FilterDrawer
```typescript
// New section to add inside filter-drawer.tsx
{stores && stores.length > 0 && (
  <div>
    <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Loja</h4>
    <div className="flex flex-wrap gap-2">
      <Badge
        variant={storeFilter === "all" ? "default" : "outline"}
        className="cursor-pointer font-bold px-3 py-1.5"
        onClick={() => onStoreChange?.("all")}
      >
        Todas
      </Badge>
      {stores.map(store => (
        <Badge
          key={store.slug}
          variant={storeFilter === store.slug ? "default" : "outline"}
          className={cn("cursor-pointer font-bold px-3 py-1.5",
            storeFilter !== store.slug && "border-white/10 text-zinc-400 hover:text-white"
          )}
          onClick={() => onStoreChange?.(store.slug)}
        >
          {store.name}
        </Badge>
      ))}
    </div>
  </div>
)}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Client-side filter of full dataset (home page) | Server-side API filtering with URL params (catalog page) | Scalable, SEO-friendly, shareable |
| Single fetch at load | Debounced re-fetch on filter change | Real-time feel without hammering API |
| Jinja2 template (STATE.md note, now outdated) | Next.js App Router Server+Client Component split | Modern, aligned with project direction |

---

## Open Questions

1. **Catalog API base URL path**
   - What we know: `getApiBaseUrl()` returns `.../api/v1`; the catalog router uses prefix `/catalog` — the full path may be `.../api/v1/catalog/paddles` or `.../catalog/paddles` depending on `main.py` router registration.
   - What's unclear: Whether catalog router is nested under `/api/v1` or at root.
   - Recommendation: Read `app/main.py` in Wave 0 and confirm the full URL before writing `catalog-api.ts`.

2. **`image_url` in catalog response**
   - What we know: `catalog.py` does NOT currently include `image_url` in the response object and does NOT filter by it.
   - What's unclear: Whether this field needs to be added in a backend Wave 0 task.
   - Recommendation: Add `image_url` to the catalog endpoint response and `WHERE image_url IS NOT NULL` to the query as a Wave 0 backend task.

3. **`use-debounce` package availability**
   - What we know: CONTEXT.md mentions it as a possibility; not confirmed installed.
   - Recommendation: Check `frontend/package.json`; implement with `useRef`+`setTimeout` if absent (no new dependency needed).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright (e2e) + Jest/Vitest (unit, if present) |
| Config file | Check `frontend/playwright.config.*` or `frontend/vitest.config.*` |
| Quick run command | `cd frontend && npx playwright test --grep "catalog" --headed=false` |
| Full suite command | `cd frontend && npx playwright test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | `/catalog` route loads with paddle grid | e2e smoke | `playwright test catalog.spec.ts` | Wave 0 |
| WEB-02 | Filter controls visible (thickness, material, price, brand, store) | e2e | `playwright test catalog.spec.ts` | Wave 0 |
| WEB-03 | Applying a filter updates the paddle grid | e2e | `playwright test catalog.spec.ts` | Wave 0 |

### Sampling Rate
- **Per task commit:** Run `npx tsc --noEmit` (TypeScript compile check, < 30s)
- **Per wave merge:** Full `playwright test catalog.spec.ts`
- **Phase gate:** All tests green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/e2e/catalog.spec.ts` — covers WEB-01, WEB-02, WEB-03
- [ ] Verify Playwright is configured (`frontend/playwright.config.ts`) — if absent, add configuration

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `frontend/components/paddle/paddle-card.tsx` — card structure, framer-motion, badge patterns
- Direct code inspection of `frontend/components/paddle/filter-drawer.tsx` — filter interface, Drawer, Slider, multi-select brand
- Direct code inspection of `frontend/app/page.tsx` + `frontend/components/home-client.tsx` — Server/Client split pattern, useState filter approach
- Direct code inspection of `app/api/endpoints/catalog.py` — confirmed endpoint params, response shape, sort order
- Direct code inspection of `frontend/lib/api.ts` — `getApiBaseUrl()` logic, `BackendPaddle` shape
- Direct code inspection of `frontend/types/paddle.ts` — existing Paddle type
- Direct code inspection of `frontend/components/ui/bottom-nav.tsx` — navigation structure to extend
- `.planning/phases/14-web-catalog-page/14-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- Next.js 14 App Router docs: `useSearchParams()` requires Suspense boundary — well-established requirement
- Next.js 14 App Router: `searchParams` prop on Server Components is synchronous for initial SSR

### Tertiary (LOW confidence)
- Catalog router mount path (root vs. `/api/v1`) — needs verification in `app/main.py`
- `use-debounce` package availability — needs verification in `frontend/package.json`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed installed via code inspection
- Architecture: HIGH — patterns directly derived from existing codebase
- API contract: HIGH — endpoint source code read directly
- Pitfalls: HIGH — derived from actual code gaps and Next.js 14 documented behaviors
- URL path for catalog API: LOW — depends on `main.py` router registration (not read)

**Research date:** 2026-03-21
**Valid until:** 2026-04-20 (stable stack — 30 days)
