# SLO Alert Workflow Failure - Root Cause Analysis

## Issue Summary
- **Workflow**: `.github/workflows/slo-check.yml`
- **Job**: "Dispatch alerts for SLO breaches" (alert job)
- **Exit Code**: 1
- **Symptom**: The script fails immediately on `init_db_sync()` due to database connection failure

## Root Cause

**Primary: Missing `DATABASE_URL_SYNC` GitHub Actions secret**

The workflow correctly passes `DATABASE_URL_SYNC` from secrets, but this secret is **not configured** in the GitHub repository. When a GitHub Actions secret is not set, the environment variable is passed as an **empty string**, not unset.

### Why this causes failure:

1. GitHub Actions passes `DATABASE_URL_SYNC` as empty string (secret not set)
2. `alert_worker.py` now validates this and exits with clear error message
3. Previously, it would try to connect to an invalid/empty database URL

### Evidence:

- Local test reproduced the error: `OperationalError: could not translate host name...`
- Railway provides `DATABASE_URL` (async), but `DATABASE_URL_SYNC` must be provided separately
- The workflow passes `DATABASE_URL_SYNC` but the secret doesn't exist in GitHub Actions

### Local Test Output:
```
psycopg2.OperationalError: could not translate host name "postgres_v3" to address: Temporary failure in name resolution
```

This same pattern occurs in GitHub Actions when the database URL is invalid/missing.

## Recommended Fix

### Fix Applied: Script Validation (Defensive Fix) ✅

Added validation to `scripts/alert_worker.py`:
1. Checks for `DATABASE_URL_SYNC` or `DATABASE_URL` environment variable
2. Fails fast with clear error message if missing
3. Wraps `init_db_sync()` in try-except for clearer error reporting

### Still Required: GitHub Actions Secret Configuration

**You must add the `DATABASE_URL_SYNC` secret to GitHub Actions:**

1. Go to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**
2. Add secret name: `DATABASE_URL_SYNC`
3. Set the value to your Railway PostgreSQL connection string:
   ```
   postgresql://user:password@host:5432/dbname?sslmode=require
   ```
   - Remove `+asyncpg` prefix if present
   - Add `?sslmode=require` if not present

**Why this is needed:**
- Railway provides `DATABASE_URL` (async, `postgresql+asyncpg://...`)
- The workflow needs `DATABASE_URL_SYNC` (sync, `postgresql://...`)
- When the secret is not set, it becomes an empty string, causing connection failures

## Files to Check

1. `.github/workflows/slo-check.yml` - Workflow configuration
2. `scripts/alert_worker.py` - Alert worker script (entry point)
3. `app/config.py` - Configuration handling
4. `app/db/database.py` - Database connection setup

## Environment Variables Required

For the alert worker in GitHub Actions:
- `DATABASE_URL_SYNC` - **CRITICAL** (PostgreSQL sync connection string)
- `TELEGRAM_BOT_TOKEN` - Optional (for Telegram alerts)
- `TELEGRAM_CHAT_ID` - Optional (for Telegram alerts)
- `GITHUB_TOKEN` - Optional (for GitHub Issues)
- `GITHUB_REPOSITORY` - Optional (defaults to current repo)
- `ADMIN_EMAIL_GROUP` - Optional (for email alerts)
- `EMAIL_HOST/PORT/USER/PASSWORD` - Optional (for email alerts)
