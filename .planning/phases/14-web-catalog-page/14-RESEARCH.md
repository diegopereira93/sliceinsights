# Phase 14: Web Catalog Page - Research

**Researched:** 2026-03-21
**Domain:** Next.js 14 frontend — catalog page with dynamic filters, SSR + client interactivity
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Next.js 14 + TypeScript** — build in existing `frontend/`, NOT Jinja2
- **New route**: `frontend/app/catalog/page.tsx` — URL `/catalog`, does NOT replace home page
- **Tailwind CSS** already configured — use existing design tokens
- **Dark mode already implemented**: bg `#000000`, accent `#ceff00`, muted `#111111`, border `#222222`
- **React state + fetch with debounce ~400ms** — filter changes fire fetch after 400ms pause (not htmx)
- **URL reflects active filters** via `useSearchParams` + `useRouter` — shareable links, back button, SEO
- **Auto-apply on change** — no explicit "Filter" button; fluid experience like Airbnb
- **Skeleton cards during loading** — gray pulsing cards with `bg-muted animate-pulse` (no extra library)
- **Grid**: 3 cols desktop, 2 tablet, 1 mobile
- **Card info**: Photo + Name + Brand badge + Thickness badge + Price from + "Ver na [Loja]" button
- **Paddles without image are filtered** — only paddles with `image_url` filled appear (`image_url IS NOT NULL`)
- **"Ver na [Loja]" button**: label "Ver na [StoreName]", opens in new tab, uses `url` from cheapest `MarketOffer`
- **Filter drawer**: use existing `filter-drawer.tsx` (bottom sheet on mobile) — ADD `surface_material` and `store` props
- **Filters required**: thickness (14mm/16mm), surface material (Carbon/Fiberglass), price range, brand (multi-select + search), store (select)
- **Design tokens**: `bg-background`, `text-primary` (`#ceff00`), `border-border`, `bg-muted`
- **Follow visual pattern** of existing `paddle-card.tsx` (glass-card, hover ring primary, framer-motion)

### Claude's Discretion
- Desktop filter layout: fixed left sidebar vs. keeping bottom drawer for all sizes
- Pagination vs. infinite scroll (API supports `limit`/`offset`)
- Default sort order (price ascending recommended)
- Empty state when no paddles match filters

### Deferred Ideas (OUT OF SCOPE)
- Fixed desktop sidebar for filters (may be Phase 15+)
- Paddle comparator on catalog page (`paddle-comparator.tsx` exists but activating it is new)
- User-driven sort (by price, rating, brand)
- Infinite scroll (API supports offset, but simple pagination satisfies WEB-01 initially)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WEB-01 | User accesses catalog web page with paddle listing | SSR Server Component reads `searchParams`, fetches `/catalog/paddles`, passes initial data to Client Component — pattern confirmed in `app/page.tsx` |
| WEB-02 | Page shows filter controls (thickness, material, price, brand, store) | Extend existing `filter-drawer.tsx` (has thickness, brand, price already) — add `surface_material` + `store` props; backward-compatible extension |
| WEB-03 | Page updates listing dynamically when filters are applied | Client Component with `useSearchParams` + `useRouter.replace` + `useEffect` + debounce 400ms; `isLoading` state drives skeleton/card swap |
</phase_requirements>

---

## Summary

Phase 14 is a pure frontend phase. The backend (Phase 13 catalog API) is already complete and deployed. All research confirms that the existing frontend codebase provides nearly all required building blocks: `paddle-card.tsx`, `filter-drawer.tsx`, `empty-state.tsx`, `bottom-nav.tsx`, and all shadcn/ui primitives.

The primary work is: (1) create `frontend/app/catalog/page.tsx` as a Server Component that SSR-fetches initial paddle data and passes it to a Client Component; (2) build `CatalogPaddleCard` as a new composition of the existing card pattern with a "Ver na [Loja]" CTA; (3) extend `filter-drawer.tsx` with two new optional props (`surface_material`, `store`); (4) wire URL state via `useSearchParams`/`useRouter`; (5) add `/catalog` to `bottom-nav.tsx`; (6) create Wave 0 test stubs.

The catalog API returns a different response shape than the existing `/paddles` endpoint — a new `CatalogPaddle` type is required. One minor backend touch is needed: the current `catalog.py` response does not return `image_url`, which must be added for card images to display.

**Primary recommendation:** Compose rather than rewrite. `CatalogPaddleCard` is a new component following the glass-card pattern without modifying `paddle-card.tsx`. `FilterDrawer` gets two new optional props — existing callers are unaffected.

---

## Standard Stack

### Core (all already installed — no new npm installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14.x | App Router, SSR, Client Components | Project's chosen framework |
| TypeScript | 5.x | Type safety | Already configured |
| Tailwind CSS | 3.x | Utility classes, design tokens | Already configured with project tokens |
| framer-motion | installed | Card entrance animations | Used in `paddle-card.tsx` |
| @radix-ui/react-slider | installed | Price range slider | Used in `filter-drawer.tsx` |
| lucide-react | installed | ExternalLink, Filter, ShoppingBag icons | Configured via shadcn |
| shadcn/ui (new-york) | installed | Card, Button, Badge, Skeleton, Drawer, Input, Separator | `components.json` initialized |

### No New Dependencies Required

All needed libraries are already installed. No `npm install` step in this phase.

---

## Architecture Patterns

### Recommended File Structure

```
frontend/app/catalog/
├── page.tsx              <- Server Component: SSR fetch + Suspense wrapper + passes initialData
└── catalog-client.tsx    <- Client Component ('use client'): filter state, URL sync, fetch

frontend/components/catalog/
├── catalog-paddle-card.tsx   <- New composition: glass-card + "Ver na [Loja]" CTA
├── catalog-grid.tsx          <- Grid wrapper (skeleton/loaded/empty/error states)
├── catalog-filter-bar.tsx    <- Sticky bar: "Filtros" button + ActiveFilterChips
└── catalog-pagination.tsx    <- "Anterior" / "Pagina X de Y" / "Proxima"

frontend/types/catalog.ts     <- New types: CatalogPaddle, CatalogOffer, CatalogFilters, CatalogStore
frontend/__tests__/           <- Wave 0: catalog-page.test.tsx, catalog-filters.test.tsx
e2e/catalog.spec.ts           <- Wave 0: e2e stub for WEB-03
```

### Pattern 1: SSR + Client Hybrid (matches existing `app/page.tsx`)

```typescript
// app/catalog/page.tsx  (Server Component)
import { Suspense } from 'react';
import { getApiBaseUrl } from '@/lib/api';
import CatalogClient from './catalog-client';
import { SkeletonGrid } from '@/components/catalog/catalog-grid';

export const revalidate = 3600;

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const apiBase = getApiBaseUrl();
  const params = buildQueryString(searchParams);
  let initialData = { data: [], total: 0, limit: 24, offset: 0 };
  let initialStores: CatalogStore[] = [];

  try {
    const [paddlesRes, storesRes] = await Promise.all([
      fetch(`${apiBase}/catalog/paddles?${params}&limit=24`),
      fetch(`${apiBase}/catalog/stores`),
    ]);
    initialData = await paddlesRes.json();
    const storesJson = await storesRes.json();
    initialStores = storesJson.data ?? [];
  } catch {
    // CatalogClient handles empty state gracefully
  }

  return (
    <Suspense fallback={<SkeletonGrid />}>
      <CatalogClient initialData={initialData} initialStores={initialStores} />
    </Suspense>
  );
}
```

### Pattern 2: URL State + Debounced Fetch (Client Component)

```typescript
// catalog-client.tsx  ('use client')
import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api';

export default function CatalogClient({ initialData, initialStores }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState(() => readFiltersFromParams(searchParams));
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      const qs = filtersToQueryString(filters);
      router.replace(`/catalog?${qs}`, { scroll: false }); // no history entry
      try {
        const res = await fetch(`${getApiBaseUrl()}/catalog/paddles?${qs}`);
        setData(await res.json());
      } catch {
        // set error state
      } finally {
        setIsLoading(false);
      }
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [filters]); // depends on filters, NOT searchParams

  // ...render FilterTriggerBar + FilterDrawer + CatalogGrid + PaginationBar
}
```

### Pattern 3: Extending FilterDrawer (backward-compatible)

The existing `FilterDrawerProps` interface gains two optional fields only:

```typescript
interface FilterDrawerProps {
  // ... all existing props unchanged (brands, selectedBrands, priceRange, etc.) ...
  weightFilter?: "all" | "light" | "standard" | "heavy";  // make optional
  onWeightChange?: (weight: "all" | "light" | "standard" | "heavy") => void; // make optional
  surfaceMaterialFilter?: "all" | "Carbon" | "Fiberglass";
  onSurfaceMaterialChange?: (v: "all" | "Carbon" | "Fiberglass") => void;
  storeFilter?: string;       // store slug or "all"
  onStoreChange?: (slug: string) => void;
  stores?: CatalogStore[];
}
```

Existing home page callers do not pass new props — they default to `undefined` and render nothing. Zero breakage to home page.

### Pattern 4: CatalogPaddleCard (new component, does NOT touch paddle-card.tsx)

```typescript
// components/catalog/catalog-paddle-card.tsx
'use client';
import { ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CatalogPaddle } from '@/types/catalog';

export function CatalogPaddleCard({ paddle, index }: { paddle: CatalogPaddle; index: number }) {
  const cheapestOffer = paddle.market_offers[0]; // API returns sorted asc by price_brl
  return (
    <motion.div
      className="glass-card rounded-xl overflow-hidden hover:ring-2 hover:ring-primary/30 transition-all duration-500"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <div className="aspect-[4/5] overflow-hidden">
        <img
          src={paddle.image_url ?? '/placeholder-paddle.png'}
          alt={paddle.model_name}
          loading="lazy"
          className="object-cover w-full h-full"
        />
      </div>
      <div className="p-4 space-y-2">
        <div className="flex gap-2">
          <Badge variant="outline" className="text-xs font-bold">{paddle.brand}</Badge>
          {paddle.specs.core_thickness_mm && (
            <Badge variant="outline" className="text-xs font-bold">{paddle.specs.core_thickness_mm}mm</Badge>
          )}
          {paddle.specs.surface_material && (
            <Badge variant="outline" className="text-xs font-bold">{paddle.specs.surface_material}</Badge>
          )}
        </div>
        <h3 className="text-base font-bold text-foreground leading-tight">{paddle.model_name}</h3>
        <p className="text-sm text-muted-foreground">
          A partir de <span className="text-primary font-bold">R$ {cheapestOffer.price_brl.toLocaleString('pt-BR')}</span>
        </p>
        <a href={cheapestOffer.store_url} target="_blank" rel="noopener noreferrer">
          <Button size="sm" className="w-full rounded-xl font-bold text-xs bg-primary text-primary-foreground">
            <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
            Ver na {cheapestOffer.store_name}
          </Button>
        </a>
      </div>
    </motion.div>
  );
}
```

Note: Uses `<img>` not `next/image` to avoid remote hostname configuration. See Pitfall 6.

### Pattern 5: New TypeScript Types

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
  image_url: string | null;     // requires API fix (see Pitfall 2)
  specs: {
    core_thickness_mm: number | null;
    surface_material: string | null;
  };
  market_offers: CatalogOffer[]; // sorted asc by price_brl by API
}

export interface CatalogStore {
  id: number;
  name: string;
  slug: string;
  base_url: string;
}

export interface CatalogFilters {
  core_thickness?: string;
  surface_material?: string;
  price_min?: number;
  price_max?: number;
  brand?: string;
  store?: string;
  page: number;
}

export interface CatalogResponse {
  data: CatalogPaddle[];
  total: number;
  limit: number;
  offset: number;
}
```

### Pattern 6: Pagination (24 per page, per UI-SPEC)

```typescript
const PAGE_SIZE = 24;
const totalPages = Math.ceil(data.total / PAGE_SIZE);
const offset = (filters.page - 1) * PAGE_SIZE;
// URL: /catalog?page=2  => offset=24
// "Anterior" disabled when filters.page === 1
// "Proxima" disabled when offset + PAGE_SIZE >= data.total
```

### Anti-Patterns to Avoid

- **Do not modify `paddle-card.tsx`** — it is used on the home page with its own prop contract. Build `CatalogPaddleCard` as a separate component.
- **Do not use `router.push` for filter changes** — use `router.replace` to avoid polluting browser history with every filter change.
- **Do not drive `useEffect` from `searchParams`** — seed `filters` state from `searchParams` on mount only; react to `[filters]` in `useEffect`.
- **Do not nest `<button>` inside `<a>`** — the "Ver na [Loja]" pattern wraps `<Button>` (renders as `<button>`) inside `<a>`. This is valid HTML. Never reverse the nesting.
- **Do not call `getApiBaseUrl()` at module load time** — call it inside async functions, matching `lib/api.ts` pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filter bottom sheet | Custom modal | `filter-drawer.tsx` (already exists) | Tested, dark-mode-correct, accessible |
| Empty results state | Custom JSX | `components/ui/empty-state.tsx` (already exists) | Consistent app-wide pattern |
| Animated card entrance | CSS keyframes | `framer-motion` (already installed) | `initial/animate` used in paddle-card.tsx |
| Price range slider | Custom range input | `@radix-ui/react-slider` (already in filter-drawer) | Accessible, already styled |
| Brand search in filter | Custom dropdown | Extend existing brand search in `filter-drawer.tsx` | Pattern already implemented |
| Skeleton cards | Third-party library | `<Skeleton>` from shadcn + `animate-pulse` | Zero new deps |
| Debounce utility | Custom timer logic | `setTimeout`/`clearTimeout` in `useRef` | No library needed; pattern is 4 lines |

**Key insight:** This phase is primarily wiring and extending existing components, not building from scratch.

---

## Common Pitfalls

### Pitfall 1: `useSearchParams` requires Suspense boundary
**What goes wrong:** Next.js 14 throws a build/runtime error if a Client Component using `useSearchParams` is not wrapped in `<Suspense>`.
**Why it happens:** App Router requirement for streaming compatibility.
**How to avoid:** Wrap `<CatalogClient>` in `<Suspense fallback={<SkeletonGrid />}>` inside the Server Component `page.tsx`.
**Warning signs:** Build error "useSearchParams() should be wrapped in a suspense boundary."

### Pitfall 2: Catalog API does NOT return `image_url` in current implementation
**What goes wrong:** Cards have no image to display — all show placeholder.
**Why it happens:** `catalog.py` lines 112–133 build the response dict without `image_url`. The CONTEXT.md says paddles without image are filtered at query level (`image_url IS NOT NULL`), but the field is not returned in the JSON.
**How to avoid:** Add `"image_url": paddle.image_url` to the response dict in `catalog.py`. This is a minor in-phase backend touch (1 line).
**Warning signs:** All catalog cards show placeholder even when paddles have images in the database.

### Pitfall 3: `useEffect` → `router.replace` → `searchParams` change → infinite loop
**What goes wrong:** Updating URL params causes `searchParams` to change, which re-triggers the effect, causing infinite refetch.
**Why it happens:** If `useEffect` depends on `[searchParams]` and also calls `router.replace`, it loops.
**How to avoid:** Keep `filters` as a separate state object seeded from `searchParams` on mount only. `useEffect` depends on `[filters]` exclusively. `router.replace` updates the URL but does NOT update `filters` state.

### Pitfall 4: `weightFilter` is currently required in `FilterDrawerProps`
**What goes wrong:** TypeScript error when calling FilterDrawer from catalog without passing `weightFilter`.
**Why it happens:** The current interface has `weightFilter: "all" | "light" | "standard" | "heavy"` (not optional).
**How to avoid:** Make `weightFilter` and `onWeightChange` optional (`?`) when extending the interface. Pass `"all"` as default value inside the component if undefined.

### Pitfall 5: Brand filter API takes a single string (substring match), not an array
**What goes wrong:** Trying to send multiple brands as array fails — API only accepts one `brand` query param.
**Why it happens:** `catalog.py` uses `Brand.name.ilike(f"%{brand}%")` — single string, partial match.
**How to avoid:** Brand filter in catalog is single-select. The drawer UI can show a searchable list, but only one brand is sent to the API. Document this as a known limitation.

### Pitfall 6: `next/image` blocks external image URLs from unconfigured domains
**What goes wrong:** `<Image src={paddle.image_url} />` fails with "hostname not configured" for store image URLs.
**Why it happens:** `next/image` requires explicit `remotePatterns` in `next.config.js` for each hostname.
**How to avoid:** Use plain `<img loading="lazy">` for catalog cards. Paddle images come from multiple store domains — configuring all hostnames is not practical. `<img>` is the correct choice here.
**Warning signs:** Console error "hostname ... not configured under images in next.config.js"

---

## Code Examples

### Filter-to-query-string serialization
```typescript
// Source: Next.js URLSearchParams pattern
function filtersToQueryString(filters: CatalogFilters): string {
  const params = new URLSearchParams();
  if (filters.core_thickness) params.set('core_thickness', filters.core_thickness);
  if (filters.surface_material) params.set('surface_material', filters.surface_material);
  if (filters.price_min && filters.price_min > 0) params.set('price_min', String(filters.price_min));
  if (filters.price_max && filters.price_max < 4000) params.set('price_max', String(filters.price_max));
  if (filters.brand) params.set('brand', filters.brand);
  if (filters.store) params.set('store', filters.store);
  if (filters.page > 1) params.set('page', String(filters.page));
  params.set('limit', '24');
  const offset = (filters.page - 1) * 24;
  if (offset > 0) params.set('offset', String(offset));
  return params.toString();
}
```

### Active filter chips with dismiss
```typescript
function ActiveFilterChips({ filters, onRemove }) {
  return (
    <div className="flex flex-wrap gap-2">
      {filters.brand && (
        <Badge className="bg-primary text-primary-foreground gap-1 text-xs font-bold">
          {filters.brand}
          <button aria-label="Remover filtro marca" onClick={() => onRemove('brand')}>
            <X className="w-3 h-3" />
          </button>
        </Badge>
      )}
      {/* repeat pattern for each active filter */}
    </div>
  );
}
```

### Skeleton grid (6 cards, per UI-SPEC anatomy)
```typescript
export function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="glass-card rounded-xl overflow-hidden">
          <div className="aspect-[4/5] bg-muted animate-pulse" />
          <div className="p-4 space-y-3">
            <div className="flex gap-2">
              <div className="h-5 w-16 bg-muted animate-pulse rounded-full" />
              <div className="h-5 w-12 bg-muted animate-pulse rounded-full" />
            </div>
            <div className="h-4 w-2/3 bg-muted animate-pulse rounded" />
            <div className="h-4 w-1/3 bg-muted animate-pulse rounded" />
            <div className="h-8 w-full bg-muted animate-pulse rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jinja2 HTML template (STATE.md original decision) | Next.js 14 App Router (overridden in CONTEXT.md) | 2026-03-21 | Build in `frontend/`, not Python templates |
| Pages Router `getServerSideProps` | App Router Server Components | Next.js 13+ | `app/` directory, no `getServerSideProps` |
| `useRouter().query` for URL params | `useSearchParams()` + `useRouter().replace()` | Next.js 13 App Router | Must wrap consuming component in `<Suspense>` |

**Deprecated/outdated:**
- STATE.md decision "Web page uses HTML/Jinja2": superseded by CONTEXT.md locked decision — use Next.js.

---

## Open Questions

1. **Catalog API must return `image_url` — minor backend touch needed**
   - What we know: `catalog.py` response dict does not include `image_url` (confirmed by reading lines 112–133)
   - What's unclear: Whether this is intentional (relying on API already filtering `image_url IS NOT NULL` at query level but not exposing it in JSON)
   - Recommendation: Planner adds a Wave 0 backend task — add `"image_url": paddle.image_url` to the response dict in `catalog.py`. One line. Required for cards to display images.

2. **`next.config.js` image domain configuration**
   - What we know: Catalog cards use `<img>` not `next/image`, so no domain config needed
   - Resolved: Use `<img loading="lazy">` — no `next.config.js` change required.

3. **Stores API response shape**
   - What we know: `GET /catalog/stores` returns `Store` ORM objects — the JSON shape includes `id`, `name`, `slug`, `base_url`, `is_active`, `available_brands`
   - Recommendation: `CatalogStore` type needs only `{ name, slug }` for the filter drawer.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | jest 29.x / Playwright |
| Config file | `frontend/jest.config.ts` (exists) / `playwright.config.ts` (check root) |
| Quick run command | `cd frontend && npm test -- --passWithNoTests` |
| Full suite command | `cd frontend && npm test && npx playwright test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Catalog page renders paddle listing | unit | `cd frontend && npm test -- --testPathPattern=catalog-page` | ❌ Wave 0 |
| WEB-02 | Filter controls render and update URL/listing | unit | `cd frontend && npm test -- --testPathPattern=catalog-filters` | ❌ Wave 0 |
| WEB-03 | Paddle card link navigates to store (new tab) | e2e | `npx playwright test catalog` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npm test -- --passWithNoTests`
- **Per wave merge:** `cd frontend && npm test && npx playwright test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/__tests__/catalog-page.test.tsx` — render stub for WEB-01
- [ ] `frontend/__tests__/catalog-filters.test.tsx` — filter render stub for WEB-02
- [ ] `e2e/catalog.spec.ts` — e2e stub for WEB-03
- [ ] `e2e/` directory — does not exist yet, must be created

---

## Sources

### Primary (HIGH confidence)
- `app/api/endpoints/catalog.py` — actual API response shape, filter params, sort order, `image_url` gap
- `frontend/components/paddle/filter-drawer.tsx` — existing props interface and patterns to extend
- `frontend/components/paddle/paddle-card.tsx` — glass-card pattern, framer-motion usage, badge style
- `frontend/components/ui/bottom-nav.tsx` — NavItem pattern for adding `/catalog` link
- `frontend/app/page.tsx` — confirmed SSR Server Component + Client Component split pattern
- `frontend/lib/api.ts` — `getApiBaseUrl()` runtime pattern, `BackendPaddle` shape (differs from catalog shape)
- `frontend/types/paddle.ts` — existing type shape (confirms `CatalogPaddle` is a distinct new type)
- `.planning/phases/14-web-catalog-page/14-UI-SPEC.md` — approved visual/interaction contract
- `.planning/phases/14-web-catalog-page/14-VALIDATION.md` — Wave 0 test file requirements

### Secondary (MEDIUM confidence)
- Next.js 14 App Router documentation — `useSearchParams` + Suspense boundary requirement

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present in existing frontend code
- Architecture: HIGH — SSR+Client pattern directly observed in `app/page.tsx`; no speculation
- Pitfalls: HIGH — Pitfalls 1/2/3/4/6 directly identified from codebase reading; Pitfall 5 from API code
- Test infrastructure: MEDIUM — `jest.config.ts` path confirmed; `__tests__/` dir and `e2e/` dir do not yet exist

**Research date:** 2026-03-21
**Valid until:** 2026-04-20 (stable stack)
