# Deploy & Release Guide

**Phase:** 8 — Deploy & Release Strategy
**Last Updated:** 2026-03-20
**Owner:** Data Engineering

---

## Overview

This guide documents the SliceInsights nightly batch deployment pipeline. It covers:

- How deploys are triggered and what pipeline stages run
- CLI reference for all operator commands
- Step-by-step rollback procedure
- Troubleshooting table for common failures
- GitHub Actions setup and secret requirements
- Requirements traceability

**Design principle:** Deployments are event-driven, not cron-based. The scraper CI pipeline fires a `repository_dispatch` webhook when all scrapers complete. The deploy workflow then runs the full aggregate → validate → publish → prune pipeline. No manual deploys are needed under normal operation.

---

## Architecture

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Nightly Batch Deploy Pipeline                      │
│                                                                       │
│  Scrapers run                                                         │
│       │                                                               │
│       ↓                                                               │
│  market_offers + slo_logs                                             │
│       │                                                               │
│       ↓                                                               │
│  Scraper CI fires repository_dispatch (scrapers-complete)             │
│       │                                                               │
│       ↓                                                               │
│  GitHub Actions: deploy-nightly.yml                                   │
│       │                                                               │
│       ↓                                                               │
│  deploy_worker.py --run                                               │
│       │                                                               │
│       ├─→ 1. check_slo_gate()        Query slo_logs for calendar day  │
│       │         └─→ Abort if 0 scrapers passed SLO gate               │
│       │                                                               │
│       ├─→ 2. aggregate_batch()       Copy passing scrapers' data      │
│       │         └─→ market_offers → market_offers_staging             │
│       │                                                               │
│       ├─→ 3. run_pre_deploy_validation()                              │
│       │         ├─→ SLO re-check on staged data                       │
│       │         └─→ Corruption audit (NULL price_brl, NULL url)       │
│       │                                                               │
│       ├─→ 4. publish_batch()         Atomic upsert staging → production│
│       │         └─→ market_offers rows tagged with version_id         │
│       │                                                               │
│       └─→ 5. prune_old_versions()    Keep current + 1 previous version│
│                                                                       │
│  On failure: notify job fires alert_worker.py --all                   │
│              (Telegram + GitHub Issue + Email)                        │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Tables

| Table | Role |
|-------|------|
| `market_offers` | Production data served to API. Tagged with `version_id` + `is_active` |
| `market_offers_staging` | Intermediate buffer — staging area before publish |
| `deploy_logs` | Audit log of every deploy attempt (batch_id, version_id, status, metrics) |
| `slo_logs` | SLO check results queried by `check_slo_gate()` and `run_pre_deploy_validation()` |

### Version Schema

`market_offers` rows carry two versioning columns:
- `version_id` (INTEGER): sequential version counter per batch deploy
- `is_active` (BOOLEAN): `true` for the live version, `false` for rolled-back or pruned versions

Rollback is a flag-flip: set `is_active = false` on current version, `is_active = true` on previous. Zero downtime.

---

## CLI Reference

All commands run from the project root. Set `DATABASE_URL_SYNC` before running locally:

```bash
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch
```

---

### `--run` — Full nightly deploy

```bash
python scripts/deploy_worker.py --run [--batch-date YYYY-MM-DD]
```

**Purpose:** Runs the complete deploy pipeline: SLO gate check → aggregate → validate → publish → prune.

**When to use:** Normally triggered automatically by GitHub Actions. Run manually to force a deploy outside the scheduled window, or to re-run after fixing a scraper failure.

**Options:**
- `--batch-date YYYY-MM-DD` — Override the batch date (default: today UTC). Useful to re-deploy a specific day's data.

**Example output:**
```
[deploy] Starting nightly deploy for batch_20260320_a1b2c
[deploy] SLO gate: 9/11 scrapers passed
[deploy] Aggregating batch batch_20260320_a1b2c (9 scrapers, ~4200 rows)
[deploy] Pre-deploy validation: PASS
[deploy] Publishing batch batch_20260320_a1b2c as version_id=42
[deploy] Pruning old versions (keeping current + 1 previous)
[deploy] Deploy complete. 4183 products published.
```

**Exit codes:**
- `0` — Deploy succeeded
- `1` — Deploy failed (SLO gate blocked, validation failed, or DB error)

---

### `--validate-batch` — Re-validate a specific batch

```bash
python scripts/deploy_worker.py --validate-batch BATCH_ID [--batch-date YYYY-MM-DD]
```

**Purpose:** Runs pre-deploy validation against an existing batch in `market_offers_staging` without publishing. Useful to check whether staged data is clean before forcing a publish.

**When to use:** After a validation failure. Fix the upstream issue, then re-validate to confirm the data is now clean before using `--force-publish`.

**Example:**
```bash
python scripts/deploy_worker.py --validate-batch batch_20260320_a1b2c
```

**Example output:**
```
[validator] SLO re-check: PASS (9/11 scrapers)
[validator] Corruption audit: PASS (0 NULL price_brl, 0 NULL url)
[validator] Batch batch_20260320_a1b2c is valid for publish.
```

**Exit codes:**
- `0` — Validation passed
- `1` — Validation failed (details logged)

---

### `--force-publish` — Force publish (bypass validation)

```bash
python scripts/deploy_worker.py --force-publish BATCH_ID --operator-id YOUR_NAME
```

**Purpose:** Publishes a batch directly, skipping validation. Requires `--operator-id` for audit trail.

**When to use:** Use with caution. Only when you have manually verified the data is acceptable and a false positive validation failure is blocking production. The operator name is recorded in `deploy_logs.forced_by` for audit.

**Example:**
```bash
python scripts/deploy_worker.py --force-publish batch_20260320_a1b2c --operator-id diego
```

**Example output:**
```
[deploy] FORCE PUBLISH requested by operator: diego
[deploy] Publishing batch batch_20260320_a1b2c as version_id=42 (forced)
[deploy] Force-publish complete. Logged to deploy_logs.
```

**Exit codes:**
- `0` — Force publish succeeded
- `1` — DB error during publish

---

### `--rollback` — Rollback a deployed batch

```bash
python scripts/deploy_worker.py --rollback BATCH_ID
```

**Purpose:** Rolls back a deployed batch by flipping `is_active` flags. The current version becomes inactive; the previous version becomes active. Zero downtime.

**When to use:** When a published batch caused data quality issues or complaints. See full procedure in the Rollback Procedure section below.

**Example:**
```bash
python scripts/deploy_worker.py --rollback batch_20260320_a1b2c
```

**Example output:**
```
[rollback] Rolling back batch_20260320_a1b2c (version_id=42)
[rollback] Previous version: version_id=41
[rollback] Activating version_id=41, deactivating version_id=42
[rollback] Rollback complete. API now serving version_id=41.
```

**Exit codes:**
- `0` — Rollback succeeded
- `1` — Rollback failed (no previous version found, or DB error)

---

## Rollback Procedure

Follow these steps in order when rolling back a deploy.

**Rollback window:** Guaranteed within 24 hours of deploy. After 24 hours, version N-2 may be pruned by `prune_old_versions()`.

---

**Step 1: Identify the batch to rollback**

Query the deploy log to find the batch_id of the problematic deploy:

```sql
SELECT batch_id, version_id, status, scrapers_passed, products_published, created_at
FROM deploy_logs
ORDER BY created_at DESC
LIMIT 5;
```

Note the `batch_id` of the row you want to roll back.

---

**Step 2: Run rollback**

```bash
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch
python scripts/deploy_worker.py --rollback batch_20260320_a1b2c
```

Replace `batch_20260320_a1b2c` with your batch_id from Step 1.

---

**Step 3: Verify rollback**

Confirm the active row count returned to its pre-deploy level:

```sql
SELECT COUNT(*) FROM market_offers WHERE is_active = true;
```

This should match the count from before the failed deploy. Cross-reference with `products_published` from the previous deploy row in `deploy_logs`.

Also confirm the version flip:

```sql
SELECT version_id, is_active, COUNT(*) as row_count
FROM market_offers
GROUP BY version_id, is_active
ORDER BY version_id DESC;
```

The rolled-back version should show `is_active = false`. The previous version should show `is_active = true`.

---

**Step 4: Confirm the API is serving the previous version**

Rollback does NOT delete rows. The new version rows remain with `is_active = false` for audit purposes. Queries filtering on `is_active = true` will automatically return the previous version.

---

**Step 5: Investigate and re-deploy when ready**

After rollback, investigate the root cause (bad scraper data, validator false positive, etc.) before triggering a new deploy. Use `--validate-batch` to confirm data is clean before the next `--run`.

---

**Important notes:**
- Rollback is instantaneous (flag-flip in a single transaction)
- The rolled-back version rows are preserved with `is_active = false` (audit trail)
- After 24 hours, `prune_old_versions()` may remove version N-2, leaving only current and N-1. Act within 24 hours.
- If version N-1 was already pruned, see the "Rollback fails: no previous version" row in the Troubleshooting table.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Deploy aborted: 0 scrapers passed | All scrapers have SLO breaches | Check slo_logs: `SELECT scraper_name, status, value_hours FROM slo_logs WHERE checked_at > NOW() - INTERVAL '24h' AND status = 'fail' ORDER BY checked_at DESC`. Fix failing scrapers, then re-trigger deploy. |
| Validation failed: NULL corruption | Staging data has NULL price_brl or url | Investigate source scraper. Run `SELECT scraper_name, COUNT(*) FROM market_offers_staging WHERE batch_id = 'X' AND price_brl IS NULL GROUP BY scraper_name`. Re-validate after fix. |
| Validation failed: SLO breach | Data quality degraded between aggregation and validation | Retry: `python scripts/deploy_worker.py --validate-batch BATCH_ID`. If confident it is a false positive, use `--force-publish` with your operator ID. |
| Rollback fails: no previous version | Version N-1 was already pruned (more than 24h since deploy) | Manual recovery: restore from database backup. Prevention: always rollback within the 24h window. |
| Deploy timeout (150 min exceeded) | Scraper suite or publish took too long | Check GitHub Actions logs for the slow step. If publish is slow (large dataset), increase `timeout-minutes` in `.github/workflows/deploy-nightly.yml`. |
| Webhook not firing | GH_DEPLOY_PAT expired or missing repo scope | Regenerate PAT with `repo` scope at GitHub Settings > Developer settings > Personal access tokens. Update the `GH_DEPLOY_PAT` secret in GitHub repository settings. |
| Deploy ran but no products published | SLO gate passed but aggregate_batch found 0 qualifying rows | Check `deploy_logs` for `scrapers_passed` count and `products_published`. If 0, check `market_offers_staging` is populated: `SELECT COUNT(*), batch_id FROM market_offers_staging GROUP BY batch_id ORDER BY batch_id DESC LIMIT 3`. |
| Force-publish not audited | --operator-id not provided | `--operator-id` is required for `--force-publish`. The command will fail with a usage error if omitted. This is intentional for audit compliance. |

---

## Deploy Logs

### `deploy_logs` Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial PK | Auto-increment primary key |
| `batch_id` | varchar | Unique batch identifier (e.g. `batch_20260320_a1b2c`) |
| `version_id` | integer | Version number assigned to this publish |
| `status` | varchar | `success`, `failed`, or `aborted` |
| `scrapers_passed` | integer | Number of scrapers that passed SLO gate |
| `scrapers_total` | integer | Total scrapers evaluated |
| `products_published` | integer | Number of rows upserted to market_offers |
| `forced` | boolean | `true` if published via `--force-publish` |
| `forced_by` | varchar | Operator name (set when `forced = true`) |
| `abort_reason` | varchar | Reason string when `status = 'aborted'` |
| `created_at` | timestamptz | UTC timestamp when the deploy log row was created |
| `completed_at` | timestamptz | UTC timestamp when the deploy completed (or failed) |

---

### Example Queries

**Last 5 deploys:**

```sql
SELECT batch_id, version_id, status, scrapers_passed, products_published, created_at
FROM deploy_logs
ORDER BY created_at DESC
LIMIT 5;
```

**Failed deploys:**

```sql
SELECT batch_id, version_id, status, abort_reason, created_at
FROM deploy_logs
WHERE status IN ('failed', 'aborted')
ORDER BY created_at DESC;
```

**Force-published batches (audit):**

```sql
SELECT batch_id, version_id, forced_by, products_published, created_at
FROM deploy_logs
WHERE forced = true
ORDER BY created_at DESC;
```

**Active version in production:**

```sql
SELECT version_id, COUNT(*) as active_products
FROM market_offers
WHERE is_active = true
GROUP BY version_id;
```

---

## GitHub Actions Setup

### Manual Trigger

1. Go to the GitHub repository page
2. Click the **Actions** tab
3. Select **Nightly Batch Deploy** from the workflow list
4. Click **Run workflow** → select branch → click **Run workflow**

### Automatic Trigger (from Scraper Pipeline)

The deploy workflow fires when the scraper CI pipeline sends a `repository_dispatch` event with `event_type = scrapers-complete`. Add this step to the scraper CI's "all done" job:

```yaml
- name: Trigger deploy
  run: |
    gh api repos/${{ github.repository }}/dispatches \
      -f event_type=scrapers-complete
  env:
    GH_TOKEN: ${{ secrets.GH_DEPLOY_PAT }}
```

**Why a PAT is required:** `GITHUB_TOKEN` cannot trigger new workflow runs in other workflows (GitHub security restriction). `GH_DEPLOY_PAT` must be a Personal Access Token with `repo` scope.

### Required Secrets

Add all of the following in **GitHub repo > Settings > Secrets and variables > Actions**:

| Secret | Required For | Notes |
|--------|-------------|-------|
| `DATABASE_URL_SYNC` | Deploy job | Production PostgreSQL connection string |
| `GH_DEPLOY_PAT` | Scraper CI webhook trigger | PAT with `repo` scope. Not used by deploy-nightly.yml itself. |
| `TELEGRAM_BOT_TOKEN` | Failure notifications | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Failure notifications | Telegram chat/group ID |
| `ADMIN_EMAIL_GROUP` | Failure notifications | Comma-separated email addresses |
| `EMAIL_HOST` | Failure notifications | SMTP host |
| `EMAIL_PORT` | Failure notifications | SMTP port |
| `EMAIL_USER` | Failure notifications | SMTP username |
| `EMAIL_PASSWORD` | Failure notifications | SMTP password |

### Workflow File Reference

**File:** `.github/workflows/deploy-nightly.yml`

Key settings and where to adjust them:

| Setting | Location | Default | Notes |
|---------|----------|---------|-------|
| Deploy timeout | `jobs.deploy.timeout-minutes` | 150 | Increase if large datasets cause timeouts |
| Trigger event type | `on.repository_dispatch.types` | `scrapers-complete` | Must match what the scraper CI sends |
| Alert condition | `if: needs.deploy.result == 'failure'` | failure only | Change to `'always'` to alert on success too |

---

## Requirements Traceability

| Requirement | Description | Implementation | Verified By |
|-------------|-------------|----------------|-------------|
| DEP-01 | Nightly batch aggregation from scraper outputs | `deploy_worker.py aggregate_batch()` | `tests/test_deploy_worker.py::test_aggregate_batch` |
| DEP-02 | Pre-deploy validation (SLO re-check + corruption audit) | `deploy_validator.py run_pre_deploy_validation()` | `tests/test_deploy_validator.py` |
| DEP-03 | Atomic publish with version tagging | `deploy_worker.py publish_batch()` with ON CONFLICT upsert | `tests/test_deploy_worker.py::test_publish_atomic` |
| DEP-04 | Zero-downtime rollback by version flag-flip | `deploy_worker.py rollback_batch()` sets `is_active` flags | `tests/test_deploy_worker.py::test_rollback` |
| DEP-05 | Full audit log of every deploy | `DeployLog` model + `deploy_worker.py` logging to `deploy_logs` | `tests/test_deploy_worker.py::test_deploy_log_written` |

---

*Guide created as part of Phase 8 (Deploy & Release Strategy) — 2026-03-20*
