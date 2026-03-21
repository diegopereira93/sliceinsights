---
status: awaiting_human_verify
trigger: "db-schema-init-store-reference"
created: 2026-03-21T00:00:00Z
updated: 2026-03-21T00:00:00Z
---

## Current Focus
hypothesis: "stores model exists but isn't imported in database.py"
test: "Check if stores model exists in models/ and is imported in database.py"
expecting: "If stores is missing from imports, adding it should fix the issue"
next_action: "Awaiting CI verification"

## Symptoms
expected: Database schema should initialize successfully when `init_db_sync()` is called
actual: SQLAlchemy raises `NoReferencedTableError` during `SQLModel.metadata.create_all()`
errors: "sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'market_offers.store_id' could not find table 'stores' with which to generate a foreign key to target column 'id'"
reproduction: Running `python -c "from app.db.database import init_db_sync; init_db_sync()"` fails
started: First observed in CI run 23390664645 (Phase 15: ai-recommendation-assistant)

## Eliminated
<!-- None -->

## Evidence
- timestamp: 2026-03-21T00:00:00Z
  checked: "app/models/market_offer.py"
  found: "Line 14 defines `store_id: int = Field(foreign_key=\"stores.id\")` - FK references stores table"
  implication: "market_offers table requires stores table to exist"

- timestamp: 2026-03-21T00:00:00Z
  checked: "app/models/store.py"
  found: "Store model exists with __tablename__ = \"stores\""
  implication: "The stores table model is defined but was not imported"

- timestamp: 2026-03-21T00:00:00Z
  checked: "app/db/database.py imports (before fix)"
  found: "Only imports SLOLog, SLOAlert, DeployLog, QualityMetric. Store was NOT imported."
  implication: "Store model not registered with SQLModel.metadata, so stores table not created"

- timestamp: 2026-03-21T00:00:00Z
  checked: "ingestor.py imports"
  found: "Imports MarketOffer and PaddleMaster, but this doesn't affect schema creation in database.py"
  implication: "Only imports in database.py affect SQLModel.metadata.create_all()"

- timestamp: 2026-03-21T00:00:00Z
  checked: "app/db/database.py (after fix)"
  found: "Added `from app.models.store import Store` import"
  implication: "Store model will now be registered with SQLModel.metadata, stores table will be created"

## Resolution
root_cause: "Store model is not imported in database.py, so SQLModel.metadata.create_all() doesn't register the stores table. When SQLAlchemy tries to create market_offers with FK to stores.id, it can't find the stores table."
fix: "Added `from app.models.store import Store` import to database.py"
verification: "Fix applied - CI Phase 15 needs to verify"
files_changed: ["app/db/database.py"]
