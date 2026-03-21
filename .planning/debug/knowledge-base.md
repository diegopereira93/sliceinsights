# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## vercel-build-typescript-error — TypeScript type annotation operator precedence bug
- **Date:** 2026-03-21
- **Error patterns:** TypeScript, keyof, array type, not assignable
- **Root cause:** Type annotation `keyof CatalogFilters[]` parsed as `keyof (CatalogFilters[])` (accessing property on array type) instead of `(keyof CatalogFilters)[]` (array of keys). Operator precedence requires parentheses.
- **Fix:** Changed `clear?: keyof CatalogFilters[]` to `clear?: (keyof CatalogFilters)[]`
- **Files changed:** frontend/components/catalog/catalog-filter-bar.tsx
---
