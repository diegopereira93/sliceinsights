# Phase 2: Data Quality Analysis - Research

**Researched:** 2026-03-19
**Domain:** PostgreSQL data quality auditing — Python/SQLModel/pandas against existing production DB
**Confidence:** HIGH

---

## Summary

Phase 2 audits data already in the `picklematch` PostgreSQL database. The primary tools are **already built**: `scripts/audit_data_quality.py` (field coverage, US-dump matching, non-paddle detection, duplicate detection, market offer checks, specs_confidence recalculation) and `scripts/smoke_test_quality.py` (CI-style invariant checks with exit codes). The work is to **run these tools, capture and interpret their output, and produce structured deliverables** — not to build new analysis infrastructure from scratch.

The data model has two core tables: `paddle_master` (PaddleMaster) and `market_offers` (MarketOffer). Quality is governed by 9 `REQUIRED_FIELDS` and a `specs_confidence` float (1.0 = ready, 0.5 = partial). `MarketOffer.last_updated` is the freshness timestamp. Per-scraper coverage requires grouping `market_offers` by `store_name` joined to `paddle_master`.

Phase 1 established that 6 of 11 scrapers pass (producing data), 5 fail. The 6 passing scrapers have known `store_name` values in `market_offers`. Data freshness (AUDIT-05) means comparing `MarketOffer.last_updated` to today's date — the oldest record per store reveals freshness gaps.

**Primary recommendation:** Run `audit_data_quality.py` and `smoke_test_quality.py` via `docker compose exec backend_v3`, capture JSON/text output, then write structured analysis documents. Write a supplemental freshness SQL query since the existing tool does not report per-source freshness directly.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUDIT-05 | Measure data freshness (how old is the oldest product record?) | `MarketOffer.last_updated` field exists; supplemental SQL needed since `audit_data_quality.py` does not surface per-source min(last_updated) |
| QUAL-01 | Define data quality metrics (completeness %, duplicates, missing fields) | Metrics already implemented in `audit_data_quality.py`: field coverage per REQUIRED_FIELDS, duplicate detection, non-paddle detection, offer presence |
| QUAL-02 | Run audit_data_quality.py and capture results | Script fully functional; run via `docker compose exec -T backend_v3 python scripts/audit_data_quality.py` |
| QUAL-03 | Identify incomplete or corrupted records in production DB | Script section 1 (field coverage) and section 4 (duplicates) + non-paddle detection cover this; output lists specific paddle IDs with missing fields |
| QUAL-04 | Document validation rules (required fields, value ranges, constraints) | REQUIRED_FIELDS list in `app/models/paddle.py`; validators on `power_rating` (0-10) and `twist_weight` (>0) already defined |
| QUAL-05 | Measure coverage per scraper (how many products per source?) | `market_offers.store_name` maps to scraper source; SQL GROUP BY store_name gives per-scraper product counts |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLModel | already in requirements.txt | ORM querying against PostgreSQL | Already used throughout project |
| sqlalchemy | already in requirements.txt | `func.count`, `func.min` aggregations | Required by SQLModel |
| pandas | already in requirements.txt | CSV cross-reference (US dump) | Used in audit_data_quality.py |
| psycopg2/asyncpg | already in requirements.txt | PostgreSQL driver | Configured via DATABASE_URL_SYNC |

### No New Dependencies Required
All tools needed for Phase 2 are already installed inside the `backend_v3` container. No `pip install` needed.

**Execution pattern (established in Phase 1):**
```bash
docker compose exec -T backend_v3 python scripts/audit_data_quality.py
docker compose exec -T backend_v3 python scripts/smoke_test_quality.py
```

The `-T` flag (non-interactive) is the established pattern from Phase 1 for capturing output cleanly.

---

## Architecture Patterns

### Recommended Deliverable Structure
```
.planning/phases/02-data-quality-analysis/
├── 02-RESEARCH.md           # this file
├── 02-PLAN.md               # planner creates
└── artifacts/
    ├── audit_output.txt     # raw stdout from audit_data_quality.py
    ├── smoke_test_output.txt # raw stdout from smoke_test_quality.py
    ├── freshness_report.json # per-source min(last_updated) results
    ├── coverage_report.json  # per-store product counts
    └── DATA_QUALITY.md      # human-readable summary document
```

### Pattern 1: Run-and-Capture
**What:** Execute existing scripts via docker compose exec, redirect stdout to artifact files, then parse/summarize.
**When to use:** For QUAL-02 (run audit tool) and QUAL-03 (identify corrupt records).
```bash
# Source: established Phase 1 pattern
docker compose exec -T backend_v3 python scripts/audit_data_quality.py \
  > .planning/phases/02-data-quality-analysis/artifacts/audit_output.txt 2>&1
```

### Pattern 2: Supplemental SQL for Freshness (AUDIT-05)
**What:** `audit_data_quality.py` does not report per-source data freshness. A supplemental Python script queries `min(last_updated)` and `max(last_updated)` grouped by `store_name`.
**When to use:** AUDIT-05 requirement — freshness is not covered by existing tools.
```python
# Supplemental query pattern (uses existing SQLModel/sync_engine)
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer

with Session(sync_engine) as session:
    rows = session.exec(
        select(
            MarketOffer.store_name,
            func.count(MarketOffer.id).label("offer_count"),
            func.min(MarketOffer.last_updated).label("oldest_record"),
            func.max(MarketOffer.last_updated).label("newest_record"),
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.store_name)
        .order_by(func.min(MarketOffer.last_updated))
    ).all()
```

### Pattern 3: Coverage Per Scraper (QUAL-05)
**What:** Group `market_offers` by `store_name` to count products per source, then cross-reference against Phase 1 scraper health data.
**When to use:** QUAL-05 — per-scraper coverage measurement.
```python
# Coverage query
rows = session.exec(
    select(
        MarketOffer.store_name,
        func.count(MarketOffer.paddle_id.distinct()).label("unique_paddles"),
        func.count(MarketOffer.id).label("total_offers"),
    )
    .group_by(MarketOffer.store_name)
    .order_by(func.count(MarketOffer.id).desc())
).all()
```

### Anti-Patterns to Avoid
- **Running with `--fix` in production audit:** The `--fix` flag recalculates and commits `specs_confidence`. Run audit-only first; only apply fixes after review.
- **Querying asyncpg engine synchronously:** Always use `sync_engine` / `DATABASE_URL_SYNC`. The async engine will deadlock in synchronous scripts.
- **Treating `store_name` as scraper identity without normalization:** `store_name` values in `market_offers` may not exactly match scraper file names. Map manually during analysis.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Field completeness audit | Custom completeness scanner | `audit_data_quality.py` section 1 | Already built, tested, prints formatted output |
| Duplicate detection | Custom dedup logic | `audit_data_quality.py` section 4 | Handles normalized fuzzy matching |
| Non-paddle detection | Keyword filter | `audit_data_quality.py` section 3 | 30+ keywords already enumerated |
| Invariant gate | Custom assertions | `smoke_test_quality.py` | Exit-code CI-compatible, 4 checks already implemented |
| specs_confidence recalc | Manual update SQL | `audit_data_quality.py --fix` | Handles edge cases (validation_sources count) |

**Key insight:** The audit infrastructure was built in Phase 1 in anticipation of Phase 2. The planner should structure tasks to run, capture, and interpret — not to build new analysis tools.

---

## Common Pitfalls

### Pitfall 1: Database Not Accessible from Host
**What goes wrong:** Running Python scripts directly on host fails — `DATABASE_URL_SYNC` points to `postgres_v3` which is a Docker internal hostname.
**Why it happens:** `docker-compose.yml` uses `postgres_v3` as the DB host, only resolvable inside the Docker network.
**How to avoid:** Always run via `docker compose exec -T backend_v3 python scripts/...`
**Warning signs:** `connection refused` or `could not translate host name "postgres_v3"`

### Pitfall 2: Empty Database in Test Environment
**What goes wrong:** `audit_data_quality.py` prints "No paddles found in database. Audit skipped." — yields no useful output.
**Why it happens:** Test/dev DB may not have production data loaded.
**How to avoid:** Confirm production DB has data before running audit. The STATE.md says "Production DB must not be corrupted — run audit in test environment" — verify test environment has a data snapshot.
**Warning signs:** Script exits early with the warning message above.

### Pitfall 3: `store_name` to Scraper Mapping Not Documented
**What goes wrong:** QUAL-05 (coverage per scraper) requires knowing which `store_name` value each scraper writes. This is not centrally documented.
**Why it happens:** Each scraper sets `store_name` independently; no registry exists.
**How to avoid:** Extract distinct `store_name` values from DB during audit, then manually map to scraper files.
**Warning signs:** Coverage report lists store names that don't match any known scraper.

### Pitfall 4: Freshness Gap for Failing Scrapers
**What goes wrong:** Scrapers that failed in Phase 1 (PLAYWRIGHT, FILE, NETWORK failures) may have stale or zero data in `market_offers`. Reporting min(last_updated) will show very old dates.
**Why it happens:** 5 of 11 scrapers are broken. Their data hasn't been refreshed.
**How to avoid:** Cross-reference freshness report with Phase 1 health status. Stale data from broken scrapers is expected, not a new finding — document the causal link.

---

## Code Examples

### Running the Full Audit
```bash
# Source: established Phase 1 pattern, docker-compose.yml
docker compose exec -T backend_v3 python scripts/audit_data_quality.py \
  2>&1 | tee .planning/phases/02-data-quality-analysis/artifacts/audit_output.txt

docker compose exec -T backend_v3 python scripts/smoke_test_quality.py \
  2>&1 | tee .planning/phases/02-data-quality-analysis/artifacts/smoke_test_output.txt
```

### Freshness Script (new — AUDIT-05)
```python
# scripts/measure_freshness.py — new script needed for AUDIT-05
# Run: docker compose exec -T backend_v3 python scripts/measure_freshness.py
import sys, json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db.database import sync_engine, init_db_sync
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer

init_db_sync()
with Session(sync_engine) as session:
    rows = session.exec(
        select(
            MarketOffer.store_name,
            func.count(MarketOffer.id).label("offer_count"),
            func.min(MarketOffer.last_updated).label("oldest_record"),
            func.max(MarketOffer.last_updated).label("newest_record"),
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.store_name)
        .order_by(func.min(MarketOffer.last_updated))
    ).all()

now = datetime.now(timezone.utc)
results = []
for r in rows:
    oldest = r.oldest_record
    if oldest and oldest.tzinfo is None:
        oldest = oldest.replace(tzinfo=timezone.utc)
    age_days = (now - oldest).days if oldest else None
    results.append({
        "store_name": r.store_name,
        "offer_count": r.offer_count,
        "oldest_record": str(r.oldest_record),
        "newest_record": str(r.newest_record),
        "age_days": age_days,
    })

print(json.dumps(results, indent=2, default=str))
```

### Coverage Per Scraper (QUAL-05)
```python
# scripts/measure_coverage.py — new script needed for QUAL-05
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db.database import sync_engine, init_db_sync
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer

init_db_sync()
with Session(sync_engine) as session:
    rows = session.exec(
        select(
            MarketOffer.store_name,
            func.count(MarketOffer.paddle_id.distinct()).label("unique_paddles"),
            func.count(MarketOffer.id).label("total_offers"),
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.store_name)
        .order_by(func.count(MarketOffer.id).desc())
    ).all()
    print(json.dumps([dict(r._mapping) for r in rows], indent=2, default=str))
```

---

## What Phase 2 Needs to Produce

Based on ROADMAP.md deliverables:

| Deliverable | Source | Format |
|-------------|--------|--------|
| Data quality dashboard/document | audit_data_quality.py output + smoke_test output | DATA_QUALITY.md |
| List of corrupt records + cleanup SQL | audit_data_quality.py incomplete_paddles list | SQL file + markdown |
| Quality metrics baseline | audit_data_quality.py summary section | JSON + markdown table |
| Schema validation rules | app/models/paddle.py REQUIRED_FIELDS + validators | VALIDATION_RULES.md |
| Data freshness per source | New measure_freshness.py script | JSON + markdown |
| Per-scraper coverage | New measure_coverage.py script | JSON + markdown |

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (requirements-dev.txt) + smoke_test_quality.py (standalone) |
| Config file | none detected at project root |
| Quick run command | `docker compose exec -T backend_v3 python scripts/smoke_test_quality.py` |
| Full suite command | `docker compose exec -T backend_v3 pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-05 | measure_freshness.py runs and returns per-store age data | smoke | `docker compose exec -T backend_v3 python scripts/measure_freshness.py` | Wave 0 (script to be created) |
| QUAL-01 | Quality metrics defined and documented | manual | n/a — document review | N/A |
| QUAL-02 | audit_data_quality.py exits without error | smoke | `docker compose exec -T backend_v3 python scripts/audit_data_quality.py` | Exists |
| QUAL-03 | Incomplete records listed with specific IDs | manual | audit_output.txt review | N/A |
| QUAL-04 | Validation rules document created | manual | n/a — document review | N/A |
| QUAL-05 | measure_coverage.py runs and returns store counts | smoke | `docker compose exec -T backend_v3 python scripts/measure_coverage.py` | Wave 0 (script to be created) |

### Sampling Rate
- **Per task commit:** `docker compose exec -T backend_v3 python scripts/smoke_test_quality.py`
- **Per wave merge:** Full audit re-run + smoke test
- **Phase gate:** smoke_test_quality.py exits 0 before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/measure_freshness.py` — covers AUDIT-05
- [ ] `scripts/measure_coverage.py` — covers QUAL-05
- [ ] `.planning/phases/02-data-quality-analysis/artifacts/` directory creation

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Manual SQL queries for quality checks | `audit_data_quality.py` with formatted output | Already built |
| Ad hoc checks | `smoke_test_quality.py` with exit codes for CI | Already built |
| No freshness tracking | `MarketOffer.last_updated` per row | Queryable; no aggregation script yet |

**Gaps identified:**
- No per-source freshness aggregation script (needed for AUDIT-05)
- No per-scraper coverage script (needed for QUAL-05)
- No `artifacts/` output directory for capturing results

---

## Open Questions

1. **Does the test environment have production data loaded?**
   - What we know: STATE.md says audit must run in test env; DB is `picklematch` in Docker
   - What's unclear: Whether the test DB has a current snapshot of production data
   - Recommendation: First task in Wave 1 should verify DB has rows before running full audit

2. **What `store_name` values exist in `market_offers`?**
   - What we know: Each scraper sets its own `store_name` string; no registry
   - What's unclear: Exact values — may differ from scraper file names
   - Recommendation: Run `SELECT DISTINCT store_name FROM market_offers` early in Wave 1

3. **Is `--fix` mode safe to run?**
   - What we know: `--fix` recalculates `specs_confidence` and commits to DB
   - What's unclear: Whether this is safe to run during audit (modifies DB)
   - Recommendation: Run audit-only first; only use `--fix` if specs_confidence values look wrong

---

## Sources

### Primary (HIGH confidence)
- `/home/diego/Documentos/projetos/data-products/sliceinsights/scripts/audit_data_quality.py` — full audit tool implementation, REQUIRED_FIELDS, all 6 check sections
- `/home/diego/Documentos/projetos/data-products/sliceinsights/scripts/smoke_test_quality.py` — invariant checks, CI exit codes
- `/home/diego/Documentos/projetos/data-products/sliceinsights/app/models/paddle.py` — PaddleMaster schema, REQUIRED_FIELDS, validators, specs_confidence logic
- `/home/diego/Documentos/projetos/data-products/sliceinsights/app/models/market_offer.py` — MarketOffer schema, `last_updated`, `store_name`, `is_active`
- `/home/diego/Documentos/projetos/data-products/sliceinsights/.audit/scraper_health_summary.json` — Phase 1 results: 6 pass, 5 fail

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — requirement IDs and descriptions
- `.planning/ROADMAP.md` — Phase 2 deliverables and success criteria
- `.planning/STATE.md` — decisions, constraints (test-env only, no production corruption)
- `docker-compose.yml` — service names, DATABASE_URL_SYNC pattern, `-T` flag pattern

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — tools already exist in codebase, verified by reading source
- Architecture: HIGH — execution pattern established in Phase 1, docker-compose confirmed
- Pitfalls: HIGH — derived from reading actual code (empty DB guard, sync_engine requirement)
- Freshness/coverage gaps: HIGH — confirmed by reading audit_data_quality.py (no freshness section exists)

**Research date:** 2026-03-19
**Valid until:** 2026-04-18 (stable codebase; only invalidated if schema changes)
