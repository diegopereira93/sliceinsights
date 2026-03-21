# Phase 11: Seed Cleanup & Store Catalog - Research

**Researched:** 2026-03-20 (updated with actual implementation state)
**Domain:** SQLModel/Alembic migrations, scraper DB-write adaptation, CSV removal
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Bootstrap do catálogo de lojas:** Migration Alembic cria a tabela `stores` e insere os 10 registros diretamente como data migration (Python list hardcoded na migration). Rastreável no git, idempotente, sem dependência de arquivo externo.
- **10 lojas confirmadas:** Brazil Pickleball Store (`www.brazilpickleballstore.com.br`), Joola Brasil (`joola.com.br`), yoSports (`yosports.com.br`), Loja Supremo (`www.lojasupremo.com.br`), Shark (`sharkbeachtennis.com.br`), ProSpin (`www.prospin.com.br`), Drop Shot Brasil (`www.dropshot.com.br`), PCKL House (`www.pcklhouse.com.br`), ProPadel (`www.lojapropadel.com.br`), Just Paddles (`www.justpaddles.com`).
- **Campos da tabela stores:** `id`, `name`, `base_url`, `is_active` (bool), `available_brands` (ARRAY(String)) — already implemented.
- **Vinculação market_offer → store:** Migration Alembic adiciona `store_id` FK nullable, data migration mapeia 9 `store_name` → `store_id`, torna NOT NULL, remove coluna `store_name` — already implemented.
- **Remoção de seeds:** `app/db/seed_brazil_catalog.py` removido — already done. Os 10 scrapers adaptados para escrever direto no DB — 9 of 10 done.
- **Filtro de produto:** Apenas paddles. Lógica na ingestão, não no scraper — implemented in `ingestor.py`.
- **Segurança dos testes:** Smoke test confirma pipeline roda sem CSVs — `test_pipeline_no_csv.py` exists.

### Claude's Discretion

- Schema exato de `available_brands`: resolved as `ARRAY(String)` (implemented).
- Se manter ou remover `store_name`: resolved — dropped in migration.
- Estratégia de upsert: resolved — upsert by `(paddle_id, store_id)` in `ingestor.py`.
- Nomenclatura dos métodos: resolved — `ingest_rows(rows, store_id=store.id, session=session)`.

### Deferred Ideas (OUT OF SCOPE)

- Nenhuma ideia fora desta fase foi identificada.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-01 | Remove all seed CSVs; operate 100% via scraping | `seed_brazil_catalog.py` gone; 9/10 scrapers adapted; 7 CSVs remain in `app/data/` to be deleted |
| STORE-01 | `stores` table with name, base_url, is_active, available_brands for 10 stores | `Store` model and migration `5e3dc97c03b0` exist — but `bulk_insert` call is buggy (wrong API) |
| STORE-02 | Every `market_offer` has non-null `store_id` and direct product URL | Migration `e27028b78fab` done; `scrape_justpaddles.py` is a spec-enricher, not a market-offer scraper |
</phase_requirements>

---

## Summary

Phase 11 is substantially implemented. The core infrastructure — `Store` model, `stores` table migration with 10 seed records, `store_id` FK on `market_offers`, shared `ingestor.py`, and 9 of 10 scrapers adapted to DB-write — already exists. Three focused issues remain.

**Issue 1 (STORE-01 blocker):** Migration `5e3dc97c03b0` uses `op.bulk_insert(op.get_bind(), 'stores', [...])` — an incorrect Alembic API call. `op.get_bind()` returns a connection object, not a table construct. `alembic upgrade head` will raise `TypeError`. The fix requires replacing with `op.bulk_insert(sa.table(...), rows)` or `op.execute()` INSERT statements.

**Issue 2 (SCRP-01):** Seven seed CSVs remain in `app/data/`: `brazil_pickleball_store.csv`, `dropshot_brasil_products.csv`, `joola_brazil.csv`, `loja_supremo.csv`, `pcklhouse_products.csv`, `propadel_products.csv`, `shark.csv`, `yosports.csv`. The `paddle_stats_dump.csv` file was already removed. JSON spec files (`manual_specs.json`, `scraped_product_specs.json`) must be preserved.

**Issue 3 (STORE-02 / SCRP-01):** `scrape_justpaddles.py` is a *spec-enrichment* scraper — it queries existing DB paddles and fetches swing/twist weight data from justpaddles.com using Playwright. It has no product-listing or pricing ingestion. For STORE-02 compliance (every market offer linked to a store with direct product URL), a market-offer ingestion path for Just Paddles is needed. This is distinct from the spec-enrichment work planned for Phase 12.

**Primary recommendation:** Fix the `bulk_insert` API bug in migration `5e3dc97c03b0`, delete the 7 remaining seed CSVs, add a market-offer `main()` to `scrape_justpaddles.py`, then run the full test suite to confirm green. The existing tests (`test_ingestor.py`, `test_pipeline_no_csv.py`) already cover the core verification.

---

## Standard Stack

### Core (all already in project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLModel | project-pinned | ORM models | All models use `table=True` pattern |
| Alembic | project-pinned | DB migrations | All schema/data changes go through `alembic/versions/` |
| SQLAlchemy | project-pinned | Low-level DB ops in migrations | Used via `sync_engine` and `op.execute()` |
| pytest | project-pinned | Test runner | All 21 test files use pytest |

**No new dependencies required** for this phase — all packages already installed.

---

## Architecture Patterns

### Established Scraper Pattern (DB-write) — already working in 9 scrapers

```python
# Source: scripts/scrape_brazil_store.py (existing, working)
from sqlmodel import Session, select
from scripts.scraper_utils import fetch_nuvemshop_products
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "www.brazilpickleballstore.com.br"
STORE_NAME = "Brazil Pickleball Store"
CATEGORY = "raquete"

def main():
    products = fetch_nuvemshop_products(DOMAIN, CATEGORY)
    rows = [
        {"brand_name": p["brand"], "model_name": p["model"],
         "price_brl": p["price_brl"], "product_url": p["product_url"],
         "image_url": p["image_url"]}
        for p in products
    ]
    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")
```

Key note: `fetch_nuvemshop_products()` returns dicts with keys `brand`/`model` (not `brand_name`/`model_name`). The scraper must remap them before calling `ingest_rows()`.

### Correct Alembic bulk_insert Pattern (fix for migration `5e3dc97c03b0`)

```python
# Source: Alembic standard API — op.bulk_insert requires a Table construct as first arg
import sqlalchemy as sa
from alembic import op

stores_table = sa.table(
    'stores',
    sa.column('name', sa.String),
    sa.column('base_url', sa.String),
    sa.column('is_active', sa.Boolean),
    sa.column('available_brands', sa.ARRAY(sa.String)),
)

op.bulk_insert(stores_table, [
    {'name': 'Brazil Pickleball Store', 'base_url': 'www.brazilpickleballstore.com.br',
     'is_active': True, 'available_brands': ['Selkirk', 'JOOLA', 'Diadem', 'Gearbox']},
    # ... remaining 9 stores
])
```

Alternative: replace with `op.execute()` INSERT statements (already used in `e27028b78fab`).

### Ingestor Interface (existing, working)

```python
# Source: app/db/ingestor.py (existing)
def ingest_rows(rows: list[dict], store_id: int, session: Session) -> dict:
    """
    rows: list of dicts with keys: brand_name, model_name, price_brl, product_url, image_url
    Filters non-paddles via is_paddle(), deduplicates Brand + PaddleMaster,
    upserts MarketOffer by (paddle_id, store_id).
    Returns: {"created": int, "updated": int, "skipped": int}
    """
```

### Anti-Patterns to Avoid

- **`op.bulk_insert(op.get_bind(), ...)` pattern:** Invalid Alembic API. `op.get_bind()` returns a connection, not a table construct.
- **Calling `save_to_csv()` in the market-offer pipeline path:** `scraper_utils.save_to_csv()` still exists for debug use — do not call it in `main()`.
- **Passing `store_name` in rows dict:** `ingest_rows()` takes `store_id` as a separate int arg; it does not use `store_name` from rows.
- **Hardcoding `store_id = N`:** IDs are assigned by DB autoincrement. Always look up via `session.exec(select(Store).where(Store.name == STORE_NAME)).one()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Paddle accessory filtering | Per-scraper keyword check | `ingestor.is_paddle(row)` | Already tested in `test_ingestor.py` |
| Brand/paddle deduplication | Custom dict-based merge | `ingestor.ingest_rows()` | Handles get-or-create with flush ordering |
| Market offer upsert | Manual select-then-insert | `ingestor.ingest_rows()` | Upserts by `(paddle_id, store_id)` |
| Store ID lookup | Hardcoded integer | `session.exec(select(Store).where(...)).one()` | DB autoincrement; portability |

---

## Current State: What's Done vs. What Remains

### Already Implemented (HIGH confidence — code confirmed by inspection)

| Component | File | Status |
|-----------|------|--------|
| `Store` SQLModel | `app/models/store.py` | Done — `StoreBase/Store/StoreRead/StoreCreate` with `ARRAY(String)` |
| `stores` table migration | `alembic/versions/5e3dc97c03b0` | Done structurally — **`bulk_insert` call is buggy** |
| 10 store seed records | inside `5e3dc97c03b0` | Done data-wise — API call broken, fix required |
| `store_id` FK migration | `alembic/versions/e27028b78fab` | Done — nullable add, data migration, NOT NULL, `store_name` drop |
| `ingestor.py` | `app/db/ingestor.py` | Done — full upsert + accessory filter + normalization |
| `seed_brazil_catalog.py` | `app/db/` | Done — file absent (deleted) |
| 9/10 scrapers adapted | `scripts/scrape_*.py` | Done for: brazil_store, dropshot_brasil, joola, pcklhouse, propadel, prospin, shark, supremo, yosports |
| `run_scraper.py` | `scripts/run_scraper.py` | Done — all 10 scraper names registered |
| `test_ingestor.py` | `tests/` | Done — 10 tests covering filter, normalize, upsert |
| `test_pipeline_no_csv.py` | `tests/` | Done — 7 assertions verifying CSV-free pipeline |

### Remaining Work

| Task | Detail | Req |
|------|--------|-----|
| Fix `bulk_insert` in migration `5e3dc97c03b0` | Replace `op.bulk_insert(op.get_bind(), ...)` with `op.bulk_insert(sa.table(...), rows)` | STORE-01 |
| Delete 7 seed CSVs from `app/data/` | `brazil_pickleball_store.csv`, `dropshot_brasil_products.csv`, `joola_brazil.csv`, `loja_supremo.csv`, `pcklhouse_products.csv`, `propadel_products.csv`, `shark.csv`, `yosports.csv` | SCRP-01 |
| Add market-offer ingestion to `scrape_justpaddles.py` | Current `main()` is spec-enrichment only; needs a product-listing + price scraping path | STORE-02, SCRP-01 |
| Verify `data/raw/.gitkeep` exists | `test_pipeline_no_csv.py` asserts `data/raw/.gitkeep` | SCRP-01 |
| Run full test suite after CSV deletion | Confirm all 21 test files pass | all |

---

## Common Pitfalls

### Pitfall 1: Alembic bulk_insert Wrong API (existing bug)
**What goes wrong:** `op.bulk_insert(op.get_bind(), 'stores', [...])` — `op.get_bind()` returns a `Connection`, not a `Table`. Alembic's `op.bulk_insert(table, rows)` requires `table` to be a `sa.table()` construct or SQLAlchemy `Table` object.
**How to avoid:** Use `sa.table('stores', sa.column('name'), ...)` as first argument, or replace entire block with `op.execute()` INSERT statements.
**Warning sign:** `TypeError` on `alembic upgrade head`.

### Pitfall 2: scrape_justpaddles.py Does Not Ingest Market Offers
**What goes wrong:** `run_scraper.py just_paddles` calls `scrape_justpaddles.main()`, which queries the local DB for existing paddles and scrapes swing/twist weights — no product listing, no pricing, no MarketOffer creation. Just Paddles store will have zero market_offer rows.
**Why it happens:** The file was written for Phase 12 spec-enrichment, not Phase 11 catalog ingestion.
**How to avoid:** Add a separate function that fetches Just Paddles product listings (search-based, using Playwright) and calls `ingest_rows()`. Preserve the existing spec-enrichment `run_scraper()` async function untouched.

### Pitfall 3: fetch_nuvemshop_products Key Names Mismatch
**What goes wrong:** `fetch_nuvemshop_products()` returns `{"brand": ..., "model": ..., "price_brl": ..., "product_url": ..., "image_url": ...}`. `ingest_rows()` expects `brand_name` and `model_name`. Passing raw output directly causes `ingest_rows()` to skip all rows as excluded.
**How to avoid:** Always remap in the scraper: `{"brand_name": p["brand"], "model_name": p["model"], ...}`. See `scrape_brazil_store.py` for the working pattern.

### Pitfall 4: JSON Spec Files Deleted Prematurely
**What goes wrong:** `app/data/manual_specs.json` and `scraped_product_specs.json` deleted as part of "CSV cleanup" — but `test_pipeline_no_csv.py` explicitly asserts they still exist (lines 37–42).
**How to avoid:** Only delete the 7 CSV files. JSON spec files must be preserved. `test_pipeline_no_csv.py::test_json_spec_files_preserved` will catch this.

---

## Code Examples

### scrape_justpaddles.py — market-offer main() pattern
The existing `async def run_scraper()` (spec enrichment) must not be modified. A new synchronous `main()` follows the same pattern as all other adapted scrapers:

```python
# Pattern to add to scrape_justpaddles.py (follows scrape_brazil_store.py pattern)
from sqlmodel import Session, select
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

STORE_NAME = "Just Paddles"
SEARCH_QUERIES = ["pickleball paddle"]  # search-based, not category-based

def main():
    # Fetch product listings via Playwright search
    # (use fetch_dynamic_products or custom Playwright logic)
    rows = []  # [{brand_name, model_name, price_brl, product_url, image_url}]
    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")
```

### Verification query after CSV deletion
```sql
-- Confirm no CSV reads possible
SELECT COUNT(*) FROM market_offers WHERE store_id IS NULL;  -- must be 0

-- Confirm 10 stores exist
SELECT COUNT(*) FROM stores;  -- must be 10

-- Confirm offers exist per store
SELECT s.name, COUNT(mo.id) as offers
FROM stores s LEFT JOIN market_offers mo ON mo.store_id = s.id
GROUP BY s.name ORDER BY offers DESC;
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (all 21 test files) |
| Config file | check `pytest.ini` / `pyproject.toml` at project root |
| Quick run command | `pytest tests/test_ingestor.py tests/test_pipeline_no_csv.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-01 | CSV files deleted, pipeline runs without them | smoke | `pytest tests/test_pipeline_no_csv.py -x` | Yes |
| SCRP-01 | seed_brazil_catalog.py absent | smoke | `pytest tests/test_pipeline_no_csv.py::TestPipelineWithoutCsv::test_seed_script_deleted -x` | Yes |
| SCRP-01 | JSON spec files preserved | smoke | `pytest tests/test_pipeline_no_csv.py::TestPipelineWithoutCsv::test_json_spec_files_preserved -x` | Yes |
| STORE-01 | ingestor creates Brand, Paddle, Offer correctly | unit | `pytest tests/test_ingestor.py -x` | Yes |
| STORE-02 | MarketOffer upserted by (paddle_id, store_id) | unit | `pytest tests/test_ingestor.py::TestIngestRows::test_updates_existing_offer -x` | Yes |
| STORE-02 | Accessory filter skips non-paddles | unit | `pytest tests/test_ingestor.py::TestIsPaddle -x` | Yes |

### Sampling Rate

- **Per task commit:** `pytest tests/test_ingestor.py tests/test_pipeline_no_csv.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all phase requirements. The smoke test (`test_pipeline_no_csv.py`) and ingestor unit tests (`test_ingestor.py`) already provide the required coverage. No new test files need to be created before implementation.

---

## Open Questions

1. **Just Paddles product listing approach**
   - What we know: The site uses search queries (not category pages). Playwright already used in the existing spec-enrichment function.
   - What's unclear: Whether Just Paddles prices are in USD or BRL, and whether the store lists Brazilian market products. CONTEXT.md confirms it as one of the 10 stores.
   - Recommendation: Scrape the product search results page for pickleball paddles. If prices are USD, flag the `is_active=True` store but create offers with USD prices converted, or simply ingest what's available and note in the store record.

2. **`app/models/__init__.py` — Store registration**
   - What we know: `scrape_brazil_store.py` imports `Store` directly from `app.models.store` (not `app.models`).
   - Recommendation: Verify Store is exported from `app/models/__init__.py` for relationship resolution at startup. If absent, add the export.

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `app/models/store.py`, `app/db/ingestor.py`, `alembic/versions/5e3dc97c03b0_add_stores_table.py`, `alembic/versions/e27028b78fab_add_store_id_to_market_offers.py`
- Direct code inspection: `scripts/run_scraper.py`, `scripts/scrape_brazil_store.py`, `scripts/scrape_justpaddles.py`, `scripts/scraper_utils.py`
- Direct code inspection: `tests/test_ingestor.py`, `tests/test_pipeline_no_csv.py`
- Direct filesystem check: `app/data/` contents (7 CSVs confirmed present), `app/db/seed_brazil_catalog.py` (confirmed absent)
- Scraper adaptation status: 9/10 scrapers confirmed using `ingest_rows()`, `scrape_justpaddles.py` confirmed spec-enrichment only
- `.planning/phases/11-seed-cleanup-store-catalog/11-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)

- Alembic `op.bulk_insert` API: standard pattern requires `sa.table()` construct, not a connection object — consistent with SQLAlchemy/Alembic documentation

---

## Metadata

**Confidence breakdown:**
- Implementation state (done/remaining): HIGH — all files directly inspected
- Migration bug identification: HIGH — incorrect API call confirmed by code inspection
- scrape_justpaddles gap: HIGH — no market-offer logic found in file
- Fix patterns: MEDIUM — based on standard Alembic docs pattern

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable domain)
