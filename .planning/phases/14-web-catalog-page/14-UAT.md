---
status: complete
phase: 14-web-catalog-page
source: [14-01-SUMMARY.md, 14-02-SUMMARY.md]
started: 2026-03-21T18:15:00Z
updated: 2026-03-21T18:35:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state. Start the application from scratch. Server boots without errors, and the /catalog page loads successfully with live paddle data.
result: pass

### 2. Catalog Grid Visuals
expected: Visit /catalog. While loading, you should see 6 skeleton shimmer cards. Once loaded, cards show paddle image, brand/surface badges, price, and "Ver na [Store]" CTA button.
result: issue
reported: "FAIL / NOT VISIBLE. Since no paddle data is currently being returned/displayed, I could not verify the paddle cards, images, badges, prices, or CTA buttons."
severity: major

### 3. Pagination Controls
expected: Scroll to the bottom of the catalog. Pagination should show "Anterior" and "Próxima". Click "Próxima". URL should update, and the next page of results should load. "Anterior" should be disabled on page 1.
result: issue
reported: "FAIL / NOT VISIBLE. Pagination controls are not visible at the bottom of the page because the catalog is empty or failing to load data."
severity: major

### 4. Interactive Filters
expected: Open the filter drawer on the catalog page. You should see "Surface Material" (Carbon/Fiberglass) and "Store" filter options available alongside other filters.
result: issue
reported: "PARTIAL PASS. I opened the filter drawer. I found the 'Material da Face' filter... However, the 'Store' (or Loja) filter is missing from the side drawer."
severity: major

### 5. Filter & URL Synchronization
expected: Apply a filter (e.g., set Brand to a specific brand). Wait 400ms. The results should update automatically. The URL query params should update to reflect the filter. An active filter chip should appear in the filter bar at the top.
result: pass

### 6. Active Filter Chip Dismissal
expected: Click the "X" on the active filter chip. The chip should disappear, URL should clean up, and catalog results should update to remove that filter.
result: pass

### 7. Bottom Navigation Link
expected: Check the global bottom navigation bar on mobile or desktop view. There should be a "Catálogo" link with a ShoppingBag icon that routes you to the catalog page.
result: pass

## Summary

total: 7
passed: 4
issues: 3
pending: 0
skipped: 0

## Gaps

- truth: "Paddle cards display correctly and pagination controls appear"
  status: failed
  reason: "User reported: FAIL / NOT VISIBLE. Catalog is empty so features never render."
  severity: major
  test: 2
  root_cause: "Development database is completely empty without paddle data. The API returns 0 items. Alembic migrations and seed data ingestion failed due to local database schema conflicts."
  artifacts: ["seed_test_data.py"]
  missing: ["Database seed strategy for development"]

- truth: "Store filter appears in the filter drawer"
  status: failed
  reason: "User reported: PARTIAL PASS. The 'Store' filter is missing from the side drawer."
  severity: major
  test: 4
  root_cause: "Store records are missing in the database. The frontend requires at least one store in the database to render the Store filter widget gracefully (stores.length > 0). The `add_stores_table` Alembic migration failed to run because earlier migrations crashed due to `app.db.database.init_db()` auto-creating tables out of order."
  artifacts: ["14-UAT.md"]
  missing: ["Resolution for Alembic/SQLModel.metadata.create_all() conflict during local startup"]
