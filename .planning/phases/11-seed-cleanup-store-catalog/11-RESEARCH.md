# Phase 11: Seed Cleanup & Store Catalog - Research

**Researched:** 2026-03-20
**Domain:** Alembic data migrations, SQLModel FK relationships, scraper DB-write refactor
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Bootstrap do catálogo de lojas:** Migration Alembic cria a tabela `stores` e insere os 10 registros diretamente como data migration (Python list hardcoded na migration). Rastreável no git, idempotente, sem dependência de arquivo externo.
- **10 lojas confirmadas:** Brazil Pickleball Store (`www.brazilpickleballstore.com.br`), Joola Brasil (`joola.com.br`), yoSports (`yosports.com.br`), Loja Supremo (`www.lojasupremo.com.br`), Shark (`sharkbeachtennis.com.br`), ProSpin (`www.prospin.com.br`), Drop Shot Brasil (`www.dropshot.com.br`), PCKL House (`www.pcklhouse.com.br`), ProPadel (`www.lojapropadel.com.br`), Just Paddles (`www.justpaddles.com`).
- **Campos da tabela stores:** `id`, `name`, `base_url`, `is_active` (bool), `available_brands` (lista/JSONB ou texto separado) — conforme STORE-01.
- **Vinculação market_offer → store:** Migration Alembic adiciona coluna `store_id` (FK → `stores.id`) como nullable inicialmente. Data migration UPDATE mapeando os 9 valores de `store_name` existentes para o `store_id` correspondente. Após mapeamento, tornar `store_id` NOT NULL. Preservar dados existentes (não fazer clean slate).
- **Remoção de seeds e arquitetura do pipeline:** `app/db/seed_brazil_catalog.py` é removido completamente. Os 10 scrapers são adaptados para escrever diretamente no DB (via SQLModel/SQLAlchemy session), sem passar por arquivos CSV intermediários. `data/raw/` passa a ser debug-only (gitignored para CSVs, manter `.gitkeep`). CSVs de ofertas em `app/data/` são removidos; verificar se JSONs de specs ainda são necessários antes de deletar.
- **Filtro de produto:** Apenas paddles (raquetes de pickleball) entram no `paddle_master` e `market_offers`. Lógica de filtragem aplicada na ingestão no DB, não no scraper.
- **Segurança dos testes:** Auditar todos os testes que leem de `data/raw/` ou `app/data/` CSVs. Converter para fixtures de DB. Adicionar smoke test que confirma: com `data/raw/` vazio, o pipeline roda sem erros.

### Claude's Discretion

- Schema exato de `available_brands` na tabela `stores` (JSONB array vs. tabela N:M vs. texto separado por vírgula).
- Se manter ou remover a coluna `store_name` em `market_offers` após a migration.
- Estratégia de retry/upsert dos scrapers ao escrever no DB (evitar duplicatas).
- Nomenclatura dos métodos de DB session nos scrapers adaptados.

### Deferred Ideas (OUT OF SCOPE)

- Nenhuma ideia fora desta fase foi identificada — discussão manteve-se dentro dos limites de Phase 11.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-01 | Sistema remove todos os CSVs de seed (`app/data/`, `data/raw/`) e opera 100% via scraping | Migration removes seed dependency; scrapers adapted to write directly to DB; CSV files deleted |
| STORE-01 | Sistema mantém catálogo de lojas especializadas com nome, URL base, status ativo e marcas disponíveis | New `Store` SQLModel + Alembic migration with 10 hardcoded stores |
| STORE-02 | Cada oferta de mercado está associada à sua loja de origem com URL direta do produto | `market_offers.store_id` FK migration + data migration mapping existing `store_name` values |
</phase_requirements>

---

## Summary

Phase 11 is a refactoring phase: it removes the CSV-based seed pipeline and replaces it with a scraping-only architecture backed by a proper `stores` catalog table. All three requirements (SCRP-01, STORE-01, STORE-02) are addressed through two Alembic migrations and modifications to 10 scraper scripts.

The existing codebase provides strong foundations. The `seed_brazil_catalog.py` script already contains the exact brand/model deduplication logic and DB-write patterns that the adapted scrapers will replicate. The Alembic migration chain is well-established: all migrations use `op.create_table`, `op.add_column`, and `op.execute()` for data operations. The test suite uses mock-based fixtures (not real DB) so no SQLite-in-memory infrastructure needs to be built from scratch — but `test_scrapers.py` does reference `save_to_csv` directly and will need updating.

The key architectural decision is the separation of concerns: scrapers remain HTTP-only (returning list[dict]), and a new `ingest_to_db()` helper (extracted from `seed_brazil_catalog.py`) handles deduplication, paddle filtering, and DB writes. This keeps scrapers testable without a live DB.

**Primary recommendation:** Two migrations (one schema + data for `stores`, one schema + data for `market_offers.store_id`), a shared `app/db/ingestor.py` module extracted from the seed script, and 10 minimal scraper adaptations that call `ingestor.ingest_rows(rows, store_id)`.

---

## Standard Stack

### Core (already in project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLModel | current | ORM + model definition | Project standard; all existing models use it |
| Alembic | current | Schema migrations + data migrations | All 6 existing migrations use it |
| SQLAlchemy | current | Low-level DB ops in migrations (`op.execute`) | Alembic dependency; used in data migrations |
| pytest | current | Test framework | All 19 existing test files use it |

### Supporting (already in project)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `app.db.database` | — | `sync_engine`, `Session`, `init_db_sync` | Scrapers and ingestor use sync session |
| `scripts.scraper_utils` | — | HTTP fetch utilities (`fetch_shopify_products`, etc.) | All scraper HTTP work stays here |
| `unittest.mock` | stdlib | Mock DB sessions in tests | Existing scraper test pattern |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSONB for `available_brands` | Separate N:M join table | N:M is correct long-term but overkill for v3; JSONB is simpler, sufficient for Phase 11; Phase 13 (STORE-03 API) can evolve it |
| JSONB for `available_brands` | Comma-separated text | Text is simplest but not queryable; JSONB preferred since PostgreSQL is the DB |

**Recommendation for `available_brands`:** Use PostgreSQL `ARRAY` type (SQLAlchemy `ARRAY(String)`) — simpler than JSONB for a list of strings, directly supported by SQLModel via `sa_column`, and queryable with `@>` operator in Phase 13.

**Installation:** No new packages required. All needed libraries are already in the project.

---

## Architecture Patterns

### Recommended Project Structure Changes

```
app/
├── models/
│   ├── store.py          # NEW: Store SQLModel (table=True)
│   └── market_offer.py   # MODIFIED: add store_id FK field
├── db/
│   ├── database.py       # UNCHANGED
│   ├── ingestor.py       # NEW: extracted from seed_brazil_catalog.py
│   └── seed_brazil_catalog.py  # DELETED

alembic/versions/
├── ...existing migrations...
├── {hash}_add_stores_table.py         # NEW: creates stores + inserts 10 rows
└── {hash}_add_store_id_to_market_offers.py  # NEW: adds FK, data migration, NOT NULL

scripts/
├── scraper_utils.py      # MODIFIED: remove/deprecate save_to_csv (or keep for debug)
├── scrape_*.py (×10)     # MODIFIED: call ingestor instead of save_to_csv
└── run_scraper.py        # UNCHANGED (already calls main() per scraper)

data/
└── raw/
    └── .gitkeep          # CSVs gitignored; directory preserved

app/data/
├── brazil_pickleball_store.csv  # DELETED
├── joola_brazil.csv             # DELETED
├── paddle_stats_dump.csv        # DELETED
├── manual_specs.json            # VERIFY before deleting (specs data)
└── scraped_product_specs.json   # VERIFY before deleting (specs data)
```

### Pattern 1: Two-Migration Sequence

**What:** Split into two Alembic migrations for clarity and rollback safety.

Migration 1 (`add_stores_table`):
- `op.create_table('stores', ...)` with all columns
- `op.execute()` inserting 10 store rows (hardcoded Python list in the migration file)
- `downgrade()`: `op.drop_table('stores')`

Migration 2 (`add_store_id_to_market_offers`):
- `op.add_column('market_offers', sa.Column('store_id', sa.Integer(), nullable=True))`
- `op.create_foreign_key(...)` referencing `stores.id`
- Data migration via `op.execute()`: UPDATE market_offers SET store_id = (SELECT id FROM stores WHERE name = ...) WHERE store_name = ...
- `op.alter_column('market_offers', 'store_id', nullable=False)`
- `op.drop_column('market_offers', 'store_name')` — recommended: remove it after mapping (see Claude's Discretion below)
- `downgrade()`: re-add `store_name`, nullify `store_id`, drop FK, drop column

**Example (Migration 1 data insert pattern):**
```python
# Source: alembic/versions/e68bd0ed63d5_add_ai_knowledge_base.py pattern + project convention
from alembic import op
import sqlalchemy as sa

STORES = [
    ("Brazil Pickleball Store", "www.brazilpickleballstore.com.br", True, ["Selkirk", "Joola"]),
    ("Joola Brasil", "joola.com.br", True, ["Joola"]),
    # ... 8 more
]

def upgrade() -> None:
    op.create_table(
        'stores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('base_url', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('available_brands', sa.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # Data insert — idempotent because table is freshly created
    stores_table = sa.table('stores',
        sa.column('name', sa.String()),
        sa.column('base_url', sa.String()),
        sa.column('is_active', sa.Boolean()),
        sa.column('available_brands', sa.ARRAY(sa.String())),
    )
    op.bulk_insert(stores_table, [
        {"name": name, "base_url": url, "is_active": active, "available_brands": brands}
        for name, url, active, brands in STORES
    ])
```

### Pattern 2: Shared Ingestor Module

**What:** Extract deduplication + DB-write logic from `seed_brazil_catalog.py` into `app/db/ingestor.py`.

**Why:** All 10 scrapers need identical logic to deduplicate brands/paddles and create market_offers. Centralizing avoids copy-paste and makes the logic testable.

**Interface:**
```python
# app/db/ingestor.py
def ingest_rows(rows: list[dict], store_id: int, session: Session) -> dict:
    """
    Ingest scraped rows into DB.
    rows: list of dicts with keys: brand_name, model_name, price_brl, product_url, image_url
    store_id: FK to stores.id
    Returns: {"created": int, "updated": int, "skipped": int}
    """
```

**Paddle filter logic** (extracted from `seed_brazil_catalog.py` lines 114–126):
```python
SKIP_KEYWORDS = [
    "mala", "mochila", "bolsa", "capa", "rede", "kit", "bola", "ball",
    "tshirt", "camiseta", "raqueteira", "tênis", "tenis", "short", "meia",
    "grip", "overgrip", "munhequeira", "acessório", "acessorio",
    "vestuário", "vestuario", "boné", "bone", "viseira"
]

def is_paddle(row: dict) -> bool:
    model = row.get("model_name", "").lower()
    brand = row.get("brand_name", "").lower()
    return not any(kw in model for kw in SKIP_KEYWORDS) and "overgrip" not in brand
```

**Upsert strategy for market_offers** (Claude's Discretion resolved):
- Query existing offer by `(paddle_id, store_id)` — if exists, update `price_brl`, `url`, `last_updated`, `is_active=True`
- If not exists, insert new row
- This avoids duplicate offers per paddle per store

### Pattern 3: Adapted Scraper Structure

**What:** Each scraper's `main()` changes from `save_to_csv(rows, OUTPUT)` to `ingest_to_db(rows, store_name=STORE)`.

**Example (yoSports before → after):**
```python
# BEFORE (scrape_yosports.py)
def main():
    products = fetch_shopify_products(DOMAIN, CATEGORY_FILTER)
    rows = [...]
    save_to_csv(rows, OUTPUT)

# AFTER
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from sqlmodel import Session

STORE_NAME = "yoSports"  # matches stores.name in DB

def main():
    init_db_sync()
    products = fetch_shopify_products(DOMAIN, CATEGORY_FILTER)
    rows = [build_row(p) for p in products if ...]
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Done: {result}")
```

### Anti-Patterns to Avoid

- **Do not pass `store_name` string to ingestor:** Use `store_id` (int FK). String matching across 10 scrapers is fragile; the `stores` table is the source of truth.
- **Do not call `init_db_sync()` inside `ingest_rows()`:** The caller (scraper `main()`) controls engine initialization. `ingest_rows()` receives an already-open `Session`.
- **Do not delete `data/raw/` directory:** Keep it with `.gitkeep`. Some scrapers may still write debug CSVs locally; the directory must exist to prevent path errors.
- **Do not make `store_id` NOT NULL in the same `ALTER` that adds the column:** Add nullable first, run UPDATE, then add NOT NULL constraint. This is the safe Alembic pattern for existing data.
- **Do not remove `store_name` column before the data migration completes:** The UPDATE uses `store_name` to find the correct `store_id`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Brand/paddle deduplication | Custom string matching per scraper | Extract from `seed_brazil_catalog.py` into `ingestor.py` | Logic already written and battle-tested; normalize() function handles edge cases |
| Alembic data migration | Raw SQL scripts | `op.bulk_insert()` or `op.execute()` inside `upgrade()` | Tracked in version history, rollback supported |
| Store lookup in scraper | Hardcode `store_id = 1` | `session.exec(select(Store).where(Store.name == STORE_NAME)).one()` | IDs are assigned by DB autoincrement; hardcoding breaks portability |
| Paddle filter per scraper | Duplicate keyword list in each script | `ingestor.is_paddle(row)` | 10 identical copies = maintenance nightmare |

---

## Common Pitfalls

### Pitfall 1: NOT NULL Constraint on store_id Before Data Migration

**What goes wrong:** Migration adds `store_id INTEGER NOT NULL` in one step — fails because existing rows have no value.
**Why it happens:** Forgetting that `market_offers` has existing rows in production.
**How to avoid:** Three-step migration: (1) add as nullable, (2) UPDATE all rows, (3) ALTER to NOT NULL.
**Warning signs:** `psycopg2.errors.NotNullViolation` during `alembic upgrade head`.

### Pitfall 2: store_name Mapping Gaps

**What goes wrong:** The UPDATE data migration uses `WHERE store_name = 'X'` but a scraper used a slightly different string (e.g., `"PCKL House"` vs `"PCKLHouse"`).
**Why it happens:** `store_name` was a free-text field written by each scraper independently.
**How to avoid:** Before writing the migration, audit all distinct `store_name` values in the DB with `SELECT DISTINCT store_name FROM market_offers`. Cross-reference with the 9 SOURCES entries in `seed_brazil_catalog.py` (lines 29–38) — these are the canonical strings.
**Warning signs:** After data migration, `SELECT COUNT(*) FROM market_offers WHERE store_id IS NULL` returns > 0.

### Pitfall 3: test_scrapers.py Breaking After save_to_csv Removal

**What goes wrong:** `test_scrapers.py` imports `save_to_csv` from `scraper_utils` and tests it directly (line 22, 303–345). After refactoring, this import fails.
**Why it happens:** Tests were written for the CSV-output architecture.
**How to avoid:** Keep `save_to_csv` in `scraper_utils.py` (just mark it debug-only) OR update the import in `test_scrapers.py`. Do not delete the function until all references are removed.
**Warning signs:** `ImportError: cannot import name 'save_to_csv'` in test run.

### Pitfall 4: Just Paddles Scraper Architecture

**What goes wrong:** Just Paddles (`www.justpaddles.com`) uses a search-query approach (not category-browse like the BR stores). Adapting it to write to DB must preserve this logic.
**Why it happens:** It's a US store; products are found by search term, not by pickleball category page.
**How to avoid:** Read `scrape_justpaddles.py` before adapting. The DB-write layer is additive — just replace `save_to_csv` with `ingest_rows`. The HTTP fetch logic stays unchanged.

### Pitfall 5: JSON Spec Files Deleted Prematurely

**What goes wrong:** `app/data/manual_specs.json` and `scraped_product_specs.json` are deleted as part of CSV cleanup, but some code path still reads them.
**Why it happens:** CONTEXT.md says "verificar se JSONs de specs ainda são necessários antes de deletar" — this verification must happen before deleting.
**How to avoid:** Search all Python files for references to these filenames before deleting. If referenced, preserve them (they are out of scope for Phase 11).

---

## Code Examples

### Alembic Data Migration — store_id UPDATE

```python
# Source: established pattern from alembic/versions/*.py in this project
def upgrade() -> None:
    # Step 1: add nullable
    op.add_column('market_offers',
        sa.Column('store_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_market_offers_store_id', 'market_offers', 'stores',
        ['store_id'], ['id']
    )
    # Step 2: data migration — map store_name → store_id
    store_name_map = {
        "Brazil Pickleball Store": "Brazil Pickleball Store",
        "PCKL House": "PCKL House",
        "Drop Shot Brasil": "Drop Shot Brasil",
        "ProPadel": "ProPadel",
        "ProSpin": "ProSpin",
        "Joola Brasil": "Joola Brasil",
        "yoSports": "yoSports",
        "Loja Supremo": "Loja Supremo",
        "Shark": "Shark",
    }
    for store_name in store_name_map:
        op.execute(f"""
            UPDATE market_offers
            SET store_id = (SELECT id FROM stores WHERE name = '{store_name}')
            WHERE store_name = '{store_name}'
        """)
    # Step 3: enforce NOT NULL
    op.alter_column('market_offers', 'store_id', nullable=False)
    # Optional: drop store_name
    op.drop_column('market_offers', 'store_name')
```

### Store SQLModel Definition

```python
# app/models/store.py — follows project SQLModel pattern (table=True)
from typing import Optional, List
from sqlalchemy import ARRAY, String
from sqlmodel import SQLModel, Field
from sqlalchemy import Column

class Store(SQLModel, table=True):
    __tablename__ = "stores"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    base_url: str
    is_active: bool = True
    available_brands: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String()))
    )
```

### Verification Query After Migration

```sql
-- Run after alembic upgrade head to verify STORE-02 success criteria
SELECT COUNT(*) FROM market_offers WHERE store_id IS NULL;
-- Expected: 0

SELECT s.name, COUNT(mo.id) as offer_count
FROM stores s
LEFT JOIN market_offers mo ON mo.store_id = s.id
GROUP BY s.name ORDER BY s.name;
-- Expected: 9 stores with offer_count > 0; Just Paddles may have 0 (no CSV history)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scrapers write CSV → seed script reads CSV → DB | Scrapers write directly to DB via ingestor | Phase 11 | Eliminates CSV as intermediate format; pipeline is self-contained |
| `store_name` as free text in `market_offers` | `store_id` FK to `stores` table | Phase 11 | Referential integrity; enables Phase 13 store API (STORE-03) |
| No store catalog | `stores` table with 10 managed records | Phase 11 | Foundation for STORE-03 (filter by store) in Phase 13 |

---

## Open Questions

1. **Distinct store_name values in production DB**
   - What we know: SOURCES list in `seed_brazil_catalog.py` defines 9 canonical strings
   - What's unclear: Whether any rows in production have non-canonical strings (e.g., from earlier scraper versions)
   - Recommendation: First task of Wave 1 — run `SELECT DISTINCT store_name FROM market_offers` on staging/dev DB and verify all 9 names match exactly before writing the migration

2. **manual_specs.json and scraped_product_specs.json usage**
   - What we know: CONTEXT.md says to verify before deleting; they are in `app/data/`
   - What's unclear: Whether any active code path reads these files
   - Recommendation: grep all Python files for both filenames; if no references, delete them as part of Phase 11 CSV cleanup

3. **store_name column removal**
   - What we know: CONTEXT.md marks this as Claude's Discretion
   - Recommendation: Remove it in Migration 2 (after NOT NULL is set). Keeping it creates drift — two sources of truth for the same fact. The `stores` table is authoritative. Downgrade() re-adds it if needed.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, all 19 test files) |
| Config file | `pytest.ini` or `pyproject.toml` (check project root) |
| Quick run command | `pytest tests/test_scrapers.py tests/test_domain_logic.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-01 | Pipeline runs with empty `data/raw/` without error | smoke | `pytest tests/test_pipeline_no_csv.py -x` | Wave 0 |
| SCRP-01 | Deleting seed CSVs does not break any existing test | regression | `pytest tests/ -x -q` after deleting CSVs | existing |
| STORE-01 | `Store` model has required fields (name, base_url, is_active, available_brands) | unit | `pytest tests/test_store_model.py -x` | Wave 0 |
| STORE-01 | 10 store records exist in DB after migration | integration | `pytest tests/test_store_migration.py -x` | Wave 0 |
| STORE-02 | All market_offers have non-null store_id after migration | integration | `pytest tests/test_store_migration.py::test_no_null_store_id -x` | Wave 0 |
| STORE-02 | Ingestor creates MarketOffer with correct store_id | unit | `pytest tests/test_ingestor.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_scrapers.py tests/test_domain_logic.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_store_model.py` — unit tests for Store SQLModel fields; covers STORE-01
- [ ] `tests/test_ingestor.py` — unit tests for `ingest_rows()` with mock session; covers STORE-02
- [ ] `tests/test_store_migration.py` — integration test verifying 10 stores exist + no null store_ids; covers STORE-01, STORE-02
- [ ] `tests/test_pipeline_no_csv.py` — smoke test: empty `data/raw/`, call scraper main() with mocked HTTP, assert no FileNotFoundError; covers SCRP-01

Note: Existing `tests/test_scrapers.py` references `save_to_csv` — must be audited and updated as part of Wave 0 before implementation begins.

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `app/db/seed_brazil_catalog.py` — canonical store_name strings, deduplication logic, SOURCES list
- Direct code inspection: `alembic/versions/e68bd0ed63d5_add_ai_knowledge_base.py` — established migration pattern
- Direct code inspection: `app/models/market_offer.py` — current schema (store_name: str, no store_id)
- Direct code inspection: `scripts/scraper_utils.py` — full HTTP utilities, save_to_csv, finish_run
- Direct code inspection: `scripts/scrape_yosports.py` — representative scraper structure
- Direct code inspection: `tests/conftest.py` + `tests/test_scrapers.py` — test patterns, CSV references
- `.planning/phases/11-seed-cleanup-store-catalog/11-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)

- SQLModel documentation pattern for `ARRAY(String())` via `sa_column` — consistent with SQLAlchemy docs
- Alembic `op.bulk_insert()` pattern — standard Alembic data migration approach

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use in the project
- Architecture: HIGH — derived directly from existing code patterns (seed script, migrations)
- Pitfalls: HIGH — identified from direct code inspection (test_scrapers imports, migration ordering)
- Test gaps: HIGH — identified by reading existing test files

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable domain — SQLModel/Alembic patterns don't change rapidly)
