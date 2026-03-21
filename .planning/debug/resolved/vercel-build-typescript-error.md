---
status: resolved
trigger: "TypeScript type error in catalog-filter-bar.tsx causing build to fail"
created: 2026-03-21T00:00:00.000Z
updated: 2026-03-21T00:00:00.000Z
---

## Current Focus
hypothesis: Type annotation `keyof CatalogFilters[]` is malformed - should be `(keyof CatalogFilters)[]`
test: Fix type annotation on line 22
expecting: Build passes
next_action: Apply fix and verify with npm run build

## Symptoms
expected: Vercel build completes successfully
actual: Build fails with TypeScript error
errors:
  - "Type 'string[]' is not assignable to type 'keyof CatalogFilters[] | undefined' at line 42"
reproduction: Run npm run build locally
started: Recent changes introduced this failure

## Evidence
- timestamp: 2026-03-21
  checked: catalog-filter-bar.tsx line 22
  found: "clear?: keyof CatalogFilters[]" - type is malformed
  implication: "(keyof CatalogFilters)[]" is correct; "keyof CatalogFilters[]" means something else entirely
- timestamp: 2026-03-21
  checked: types/catalog.ts CatalogFilters interface
  found: "keyof CatalogFilters" would be union type of valid filter keys
  implication: Array of those keys should be "(keyof CatalogFilters)[]"

## Eliminated
-

## Resolution
root_cause: Type annotation `keyof CatalogFilters[]` is parsed as `(keyof (CatalogFilters[]))` - looking up property on array type - instead of `(keyof CatalogFilters)[]` - an array of keys. Parentheses required for correct interpretation.
fix: Change `clear?: keyof CatalogFilters[]` to `clear?: (keyof CatalogFilters)[]`
verification: npm run build passes
files_changed:
  - frontend/components/catalog/catalog-filter-bar.tsx
