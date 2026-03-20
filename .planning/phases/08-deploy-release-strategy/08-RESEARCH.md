# Phase 8: Deploy & Release Strategy - Research

**Researched:** 2026-03-19
**Domain:** Nightly batch deployment — staging aggregation, atomic publish, flag-based versioning, rollback, GitHub Actions webhook orchestration
**Confidence:** HIGH (all patterns verified against existing project code; no speculative external libraries)

---

## Summary

Phase 8 builds a nightly batch deployment pipeline on top of existing infrastructure: SLO logs (Phase 6), alert channels (Phase 7), sync SQLAlchemy engine (`database.py`), and GitHub Actions workflows (`.github/workflows/slo-check.yml`). Every pattern needed already exists in the codebase. The deploy system is event-driven — triggered by a webhook from the GitHub Actions CI pipeline after the final scraper completes — not cron-based.

The core architectural challenge is staging isolation + atomic publish. All aggregated rows for a batch land in `market_offers_staging` first. A two-gate validation (SLO re-check + corruption audit) guards the publish. The publish itself is a single `sync_engine.begin()` transaction (the same pattern used in `database.py:init_db_sync`). Versioning uses `version_id INTEGER` + `is_active BOOLEAN` columns on `market_offers` and `paddle_master`, enabling instant flag-flip rollback with no downtime.

**Primary recommendation:** Reuse `sync_engine` for all batch operations (no async), follow `alert_worker.py` CLI argument structure for the operator tool, and follow `slo-check.yml` job structure for `deploy-nightly.yml`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data Aggregation Scope**
- SLO-gated publishing: Only data from scrapers that pass SLO checks (freshness 24h, completeness 7d) are included in the nightly batch. Scrapers with breached SLOs are held for the next batch/manual intervention.
- Fixed calendar window: Aggregate data updated between 12 AM and 12 AM UTC (calendar day), not rolling 24h.
- Partial batches accepted: If 5 of 11 scrapers pass SLO, publish those 5. Do not block all 11 waiting for broken scrapers.
- Upsert semantics: Duplicate paddles (same ID across batches) use last-write-wins upsert. Most recent data overwrites previous.
- Deploy log detail: Log both summary (X scrapers passed, Y products published) AND detailed per-scraper table (scraper name, SLO status, product count, timestamp).

**Pre-Deploy Validation Strategy**
- Dual validation: Before publishing to prod, run both SLO re-validation (freshness/completeness check) AND corruption audit (schema integrity, NULL validation, record count sanity).
- Validation gates deployment: If validation fails, deployment is blocked. Data remains in staging table.
- Staging table retention: Failed batches sit in staging for operator action. Not discarded.
- Operator-controlled retry: `deploy --validate-batch <batch_id>` re-runs validation and reports.
- Force-publish override: `--force-publish <batch_id>` is available. Forces publish, logged with timestamp and operator ID, triggers alert to team.

**Rollback & Safe Publishing**
- Atomic transaction: Publish via single ACID transaction: SELECT FROM staging, INSERT/UPDATE prod, COMMIT. All-or-nothing atomicity.
- Version-based rollback: New data marked `version_id=N`, old `version_id=N-1` marked inactive. Rollback = flip flags back (instant).
- Schema migration: Add `version_id INTEGER` and `is_active BOOLEAN` columns to `market_offers` and `paddle_master` tables in Phase 8.
- Version retention: Keep current + 1 previous version only. After new batch succeeds, delete old versions.
- Rollback mechanics: `deploy --rollback <batch_id>` flips flags, instant recovery, no downtime.

**Deployment Timing & Orchestration**
- Event-driven, not cron: Deploy triggered by webhook after scraper suite completes.
- Webhook trigger: POST /deploy/trigger fires after all GitHub Actions CI jobs finish.
- Strict scraper requirement: Deploy waits for ALL 11 active scrapers to have completed and passed SLO validation.
- Configurable timeout: Max wait 2-3 hours (configurable per environment). If timeout expires, abort and alert operator via Telegram/Slack.
- Failure scenario: If a scraper hangs/fails within timeout, deploy aborts. Can retry via webhook re-trigger or manual CLI.

### Claude's Discretion
- Exact alarm/timeout thresholds in deploy logic (within 2-3h window)
- Webhook retry logic (how many retries if scraper webhook fires but data incomplete)
- Batch aggregation query optimization (indexes, query plan)
- Staging table cleanup (TTL for old staging batches)

### Deferred Ideas (OUT OF SCOPE)
- Multi-environment deployments (staging → prod): Approval gates, promote-on-success. Deferred to v2.1.
- Automated retry of failed batches: Currently manual operator retries. Auto-retry with exponential backoff could be Phase 9 enhancement.
- Metrics and dashboard for deploy history: Phase 9 (Quality & Reporting) may include this.
- Canary deployments: Too complex for v2.0; keep nightly batch all-or-nothing.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEP-01 | Nightly batch job aggregates all successful scraper runs | SLO logs (`slo_logs` table) are the source of truth for "passed". Aggregate into `market_offers_staging`. |
| DEP-02 | Pre-deploy validation runs (freshness check, corruption audit) | Reuse `slo_validator.check_freshness` + `check_completeness`; add NULL/schema audit layer. |
| DEP-03 | Data published to production database after validation passes | Single `sync_engine.begin()` ACID transaction: staging → `market_offers` upsert + version tagging. |
| DEP-04 | Deploy workflow includes rollback capability if validation fails | Flag-flip on `version_id`/`is_active` columns via `deploy --rollback <batch_id>`. |
| DEP-05 | Deploy log recorded with timestamp, scraper count, data records published | New `deploy_logs` table: batch_id, timestamp, scraper_count, product_count, status, forced, operator. |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy (sync) | 2.x (already installed) | Atomic transactions, DDL migrations | `sync_engine` already in `app/db/database.py`; batch jobs are sync context |
| SQLModel | 0.x (already installed) | ORM models (SLOLog, new DeployLog) | Project standard; all existing models use it |
| Alembic | 1.x (already installed) | Schema migration for version columns | Existing migration chain in `alembic/versions/` |
| argparse | stdlib | CLI operator tool argument parsing | Used in `alert_worker.py`; same pattern |
| GitHub Actions | N/A | Workflow orchestration, webhook dispatch | Used in `slo-check.yml`; deploy follows same structure |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `app.services.slo_alerts.SLOAlertService` | (project) | Telegram/GitHub/Email notifications | Deploy abort, force-publish, and batch summary notifications |
| `scripts.slo_validator` | (project) | `check_freshness`, `check_completeness` | Reused inside pre-deploy dual validation |
| `hashlib` / `uuid` | stdlib | Batch ID generation (timestamp + hash) | Unique batch identifier: `batch_20260319_2f4a8` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sync_engine + begin() | async SQLModel sessions | Async has no benefit in single-process batch context; sync is simpler, already proven in `init_db_sync` |
| Flag-flip versioning | Physical delete + re-insert | Flag-flip is instant (no I/O); physical delete risks data loss during rollback window |
| argparse CLI | Click/Typer | argparse already used in alert_worker; no new dependency needed |

**Installation:** No new packages required. All libraries are already in `requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

```
scripts/
├── deploy_worker.py         # Main batch aggregation + publish entry point
├── deploy_validator.py      # Dual validation: SLO re-check + corruption audit
├── slo_validator.py         # (existing) reused for freshness/completeness
├── alert_worker.py          # (existing) reused for deploy notifications
app/
├── models/
│   ├── deploy_log.py        # DeployLog ORM model (deploy_logs table)
│   ├── market_offer.py      # (existing) + version_id, is_active columns
│   └── paddle.py            # (existing) + version_id, is_active columns
├── db/
│   └── database.py          # (existing) sync_engine reused
alembic/
└── versions/
    └── XXXX_add_deploy_versioning.py  # version_id + is_active + staging table
.github/workflows/
└── deploy-nightly.yml       # Webhook-triggered deploy workflow
```

### Pattern 1: Sync Atomic Transaction (Publish Gate)

**What:** Single `sync_engine.begin()` context manager wraps staging SELECT + prod INSERT/UPDATE + version tag. All-or-nothing.
**When to use:** The publish step (DEP-03). Never split into multiple commits.

```python
# Source: app/db/database.py (init_db_sync pattern)
from app.db.database import sync_engine
from sqlalchemy import text

def publish_batch(batch_id: str, version_id: int) -> int:
    with sync_engine.begin() as conn:
        # 1. Mark previous version inactive
        conn.execute(text(
            "UPDATE market_offers SET is_active = false WHERE version_id = :prev"
        ), {"prev": version_id - 1})
        # 2. Upsert from staging → prod with new version tag
        conn.execute(text("""
            INSERT INTO market_offers (paddle_id, store_name, price_brl, url,
                                       last_updated, is_active, version_id)
            SELECT paddle_id, store_name, price_brl, url,
                   last_updated, true, :version_id
            FROM market_offers_staging
            WHERE batch_id = :batch_id
            ON CONFLICT (paddle_id, store_name)
            DO UPDATE SET
                price_brl = EXCLUDED.price_brl,
                last_updated = EXCLUDED.last_updated,
                version_id = EXCLUDED.version_id,
                is_active = true
        """), {"batch_id": batch_id, "version_id": version_id})
        # 3. Log deploy result
        # conn.execute(insert deploy_logs ...)
        # COMMIT is automatic on context manager exit
```

### Pattern 2: Flag-Flip Rollback

**What:** Rollback = two UPDATE statements in one transaction. No data moved. Zero downtime.
**When to use:** `deploy --rollback <batch_id>` operator command.

```python
# Source: derived from database.py begin() pattern
def rollback_batch(batch_id: str, version_id: int) -> None:
    with sync_engine.begin() as conn:
        conn.execute(text(
            "UPDATE market_offers SET is_active = false WHERE version_id = :curr"
        ), {"curr": version_id})
        conn.execute(text(
            "UPDATE market_offers SET is_active = true WHERE version_id = :prev"
        ), {"prev": version_id - 1})
        # Audit: log rollback in deploy_logs, keep new version rows for audit
```

### Pattern 3: CLI Operator Tool (follows alert_worker.py)

**What:** argparse-based CLI with mutually exclusive action group. Same structure as `alert_worker.py`.
**When to use:** `deploy_worker.py` operator interface.

```python
# Source: scripts/alert_worker.py _build_parser() pattern
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deploy operator tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true", help="Run nightly batch deploy")
    group.add_argument("--validate-batch", metavar="BATCH_ID")
    group.add_argument("--force-publish", metavar="BATCH_ID")
    group.add_argument("--rollback", metavar="BATCH_ID")
    return parser
```

### Pattern 4: GitHub Actions Webhook-Triggered Workflow

**What:** `workflow_dispatch` + `repository_dispatch` event type `scrapers-complete`. Scraper CI jobs call `gh api` to fire the event when all 11 scrapers finish.
**When to use:** `deploy-nightly.yml` trigger.

```yaml
# Source: .github/workflows/slo-check.yml (pattern base)
on:
  repository_dispatch:
    types: [scrapers-complete]
  workflow_dispatch: {}  # Manual re-trigger for operator

jobs:
  deploy:
    name: Nightly Batch Deploy
    runs-on: ubuntu-latest
    timeout-minutes: 150  # 2.5h configurable timeout
    env:
      DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
```

### Anti-Patterns to Avoid

- **Separate transactions for staging load vs. prod publish:** Splits atomicity. Any failure between the two leaves prod in a partial state.
- **Deleting staging rows immediately after publish:** Failed rollback has no staging to reference. Keep staging with TTL (e.g., 7 days).
- **Running deploy on cron:** User locked this decision. Webhook-triggered only. No cron.
- **Blocking all scrapers if one fails SLO:** Partial batches are accepted (5 of 11 is valid).
- **Storing version state only in application memory:** Version ID must be persisted in `deploy_logs` for cross-process rollback commands.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ACID publish | Custom commit/rollback logic | `sync_engine.begin()` context manager | SQLAlchemy handles SAVEPOINT, rollback on exception automatically |
| SLO validation | Duplicate freshness/completeness checks | `slo_validator.check_freshness`, `check_completeness` | Already tested and used in slo-check.yml; exact same logic needed |
| Notifications | New alert code | `SLOAlertService` from Phase 7 | Telegram/GitHub/Email channels already wired; just call with deploy context |
| CLI argument parsing | Custom `sys.argv` parsing | argparse (stdlib), same pattern as `alert_worker.py` | Consistent operator experience; no new dependency |
| Batch ID | UUID4 only | `f"batch_{date}_{hash[:6]}"` (timestamp + hash prefix) | Human-readable in logs and operator commands |

**Key insight:** Phase 8 is an orchestration layer — it composes existing validated components (SLO validator, alert service, sync engine) rather than building new infrastructure.

---

## Common Pitfalls

### Pitfall 1: version_id / is_active Column Conflict

**What goes wrong:** `is_active` already exists on `MarketOffer` (field `is_active: bool = True` in `MarketOfferBase`). Adding a second `is_active` for versioning reuses the same column but changes its semantics — it now means "active version" not "active listing."
**Why it happens:** The existing `is_active` was a soft-delete flag; Phase 8 repurposes it for version control.
**How to avoid:** Confirm in Alembic migration whether the existing `is_active` column can be reused (if so, no new column needed), and update application code that queries `is_active=true` to also filter `version_id = current_version`.
**Warning signs:** Queries returning 0 offers after deploy because old rows have `is_active=false` from the previous version cycle.

### Pitfall 2: Staging Table Not Cleared Between Batches

**What goes wrong:** If `market_offers_staging` is not partitioned by `batch_id`, a new deploy aggregates on top of stale rows from a failed previous batch, publishing duplicate or stale data.
**Why it happens:** Forgetting to scope all staging queries by `batch_id`.
**How to avoid:** Always include `WHERE batch_id = :batch_id` in staging INSERT and SELECT. Never truncate staging — retain for audit (7-day TTL on old batches is Claude's discretion).

### Pitfall 3: GitHub Actions `repository_dispatch` Token Scope

**What goes wrong:** `repository_dispatch` requires a Personal Access Token (PAT) with `repo` scope — the default `GITHUB_TOKEN` cannot trigger `repository_dispatch` events in other workflows (Actions security restriction).
**Why it happens:** GitHub prevents `GITHUB_TOKEN` from triggering new workflows to avoid infinite loops.
**How to avoid:** Store a dedicated `GH_DEPLOY_PAT` secret with `repo` scope. The scraper-completion job calls `gh api repos/$REPO/dispatches` using this PAT. This is separate from the `GITHUB_TOKEN` used in slo-check.yml.

### Pitfall 4: Rollback After Version Pruning

**What goes wrong:** User runs `deploy --rollback <old_batch_id>` but the previous version rows were already pruned (version retention policy: current + 1 previous). No rows exist to flip back to.
**Why it happens:** Version pruning ran too aggressively after a successful new deploy.
**How to avoid:** Prune old versions only after the rollback window passes (e.g., keep version N-1 for 24h after version N is confirmed). Document in RUNBOOK that rollback is only guaranteed within 24h of deploy.

### Pitfall 5: Webhook Fires Before All 11 Scrapers Complete

**What goes wrong:** One scraper's CI job fires the webhook early (race condition). Deploy starts with 10/11 scrapers' data in slo_logs.
**Why it happens:** Each scraper is a separate GitHub Actions job that runs to completion independently.
**How to avoid:** The webhook must be fired by a dedicated "all done" job that `needs: [scraper1, scraper2, ..., scraper11]` in the workflow. Only this job fires `repository_dispatch`. Strict `needs` DAG enforces ordering.

---

## Code Examples

### Dual Validation Pattern

```python
# Source: scripts/slo_validator.py (existing) — reuse for pre-deploy gate
from scripts.slo_validator import check_freshness, check_completeness

def run_pre_deploy_validation(batch_id: str) -> tuple[bool, list[str]]:
    """Returns (passed, list_of_failure_reasons)."""
    failures = []

    # Gate 1: SLO re-validation
    freshness_ok = check_freshness(store_name=None)   # all stores
    completeness_ok = check_completeness()
    if not freshness_ok:
        failures.append("SLO freshness check failed")
    if not completeness_ok:
        failures.append("SLO completeness check failed")

    # Gate 2: Corruption audit
    with sync_engine.connect() as conn:
        null_count = conn.execute(text(
            "SELECT COUNT(*) FROM market_offers_staging "
            "WHERE batch_id = :bid AND (price_brl IS NULL OR url IS NULL)"
        ), {"bid": batch_id}).scalar()
        if null_count > 0:
            failures.append(f"Corruption: {null_count} rows with NULL price/url")

    return len(failures) == 0, failures
```

### DeployLog Model (new)

```python
# File: app/models/deploy_log.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class DeployLog(SQLModel, table=True):
    __tablename__ = "deploy_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    batch_id: str = Field(index=True)           # e.g. batch_20260319_2f4a8
    version_id: int
    status: str                                  # pending|validated|published|failed|rolled_back
    scrapers_passed: int
    scrapers_total: int = 11
    products_published: int
    forced: bool = False
    operator_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
```

### Alembic Migration Skeleton

```python
# alembic/versions/XXXX_add_deploy_versioning.py
def upgrade() -> None:
    # version_id and is_active already exists on market_offers (is_active=bool)
    # Add version_id column
    op.add_column("market_offers", sa.Column("version_id", sa.Integer(), nullable=True))
    op.add_column("paddle_master", sa.Column("version_id", sa.Integer(), nullable=True))
    # Create staging table
    op.create_table(
        "market_offers_staging",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.String(), nullable=False, index=True),
        sa.Column("paddle_id", postgresql.UUID(), nullable=False),
        sa.Column("store_name", sa.String(), nullable=False),
        sa.Column("price_brl", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    # deploy_logs table (from DeployLog model)
    op.create_table("deploy_logs", ...)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cron-based deploy | Webhook/event-driven (`repository_dispatch`) | GitHub Actions maturity (2021+) | No time-based drift; deploy fires exactly when data is ready |
| Physical delete for rollback | Flag-flip versioning (`is_active`, `version_id`) | Standard OLTP pattern | Zero downtime; audit trail preserved |
| Monolithic deploy script | CLI tool with subcommands (`--validate-batch`, `--rollback`) | Project evolution (Phase 7 established pattern) | Operators can surgically retry without full re-run |

**Deprecated/outdated:**
- Fixed-time cron for nightly deploys: Replaced by event-driven webhook (locked decision). Don't add cron to `deploy-nightly.yml`.

---

## Open Questions

1. **`is_active` column semantic conflict**
   - What we know: `MarketOffer.is_active` already exists as a soft-delete flag (value: `True` for active listings).
   - What's unclear: Does Phase 8 reuse this column for versioning, or add a separate `version_active` column?
   - Recommendation: Reuse `is_active` for versioning (column already exists, no migration cost) and update API query filters to add `AND version_id = (SELECT MAX(version_id) FROM deploy_logs WHERE status='published')`. Document the semantic change in migration comments.

2. **Webhook endpoint implementation**
   - What we know: The trigger is `POST /deploy/trigger` or `repository_dispatch`. No FastAPI endpoint currently exists for this.
   - What's unclear: Is the webhook a new FastAPI route on the existing app, or purely a GitHub Actions `repository_dispatch` call (no HTTP server needed)?
   - Recommendation: Use `repository_dispatch` only — GitHub Actions can call it via `gh api`. No new FastAPI endpoint needed. Simpler, no auth surface.

3. **Staging table TTL cleanup**
   - What we know: Failed batches are retained for operator action (locked). Old successful batches need cleanup.
   - What's unclear: How long to retain old staging batches (Claude's discretion).
   - Recommendation: 7-day TTL on staging rows. Add a cleanup step at the start of each deploy run: `DELETE FROM market_offers_staging WHERE created_at < NOW() - INTERVAL '7 days'`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, `tests/` directory) |
| Config file | `conftest.py` (existing shared fixtures) |
| Quick run command | `pytest tests/test_deploy_worker.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-01 | Batch aggregation queries slo_logs and loads staging | unit | `pytest tests/test_deploy_worker.py::test_aggregate_batch -x` | Wave 0 |
| DEP-02 | Pre-deploy validation blocks on SLO breach or NULL corruption | unit | `pytest tests/test_deploy_validator.py::test_validation_blocks -x` | Wave 0 |
| DEP-03 | Atomic publish upserts market_offers with correct version_id | unit | `pytest tests/test_deploy_worker.py::test_publish_atomic -x` | Wave 0 |
| DEP-04 | Rollback flips is_active flags correctly | unit | `pytest tests/test_deploy_worker.py::test_rollback -x` | Wave 0 |
| DEP-05 | DeployLog written with correct summary fields | unit | `pytest tests/test_deploy_worker.py::test_deploy_log_written -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_deploy_worker.py tests/test_deploy_validator.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_deploy_worker.py` — covers DEP-01, DEP-03, DEP-04, DEP-05
- [ ] `tests/test_deploy_validator.py` — covers DEP-02
- [ ] `app/models/deploy_log.py` — DeployLog ORM model
- [ ] Alembic migration: `alembic/versions/XXXX_add_deploy_versioning.py`

---

## Sources

### Primary (HIGH confidence)

- `app/db/database.py` — sync_engine, `begin()` transaction pattern, `init_db_sync` for migration pattern
- `app/models/market_offer.py` — existing `is_active` column semantic; `version_id` migration impact
- `.github/workflows/slo-check.yml` — GitHub Actions workflow structure (jobs, `needs`, `if: always()`, secrets pattern)
- `scripts/alert_worker.py` — CLI argparse pattern, `SLOAlertService` reuse
- `scripts/slo_validator.py` — `check_freshness`, `check_completeness` reuse for pre-deploy gate
- `.planning/phases/08-deploy-release-strategy/08-CONTEXT.md` — All locked decisions

### Secondary (MEDIUM confidence)

- GitHub Actions `repository_dispatch` docs — webhook-triggered workflow trigger (verified against existing project CI knowledge and GitHub Actions documentation)

### Tertiary (LOW confidence)

- None — all findings verified against existing project code.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and used
- Architecture: HIGH — all patterns present in existing code files
- Pitfalls: HIGH — `is_active` conflict and `repository_dispatch` PAT scope verified directly from source; version pruning and staging batch ID scoping are standard SQL hygiene
- Test map: HIGH — pytest already used across 10 test files in `tests/`

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable patterns; no fast-moving dependencies)
