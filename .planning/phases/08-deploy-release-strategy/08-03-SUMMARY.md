---
phase: 08-deploy-release-strategy
plan: 03
subsystem: infra
tags: [github-actions, deploy, workflow, documentation, webhook, repository-dispatch]

requires:
  - phase: 08-02
    provides: deploy_worker.py CLI with --run/--validate-batch/--force-publish/--rollback
  - phase: 07-02
    provides: alert_worker.py for failure notification channel

provides:
  - GitHub Actions webhook-triggered deploy workflow (deploy-nightly.yml)
  - Operator guide with full CLI reference, rollback procedure, troubleshooting, and requirements traceability

affects: [phase-09-data-quality, scraper-ci-pipeline]

tech-stack:
  added: []
  patterns:
    - "repository_dispatch for cross-workflow triggering (requires PAT with repo scope)"
    - "Separate notify job with if:always() + failure condition for alerting"
    - "Event-driven deploy (no cron) — locked architectural decision"

key-files:
  created:
    - .github/workflows/deploy-nightly.yml
    - docs/deploy-guide.md
  modified: []

key-decisions:
  - "No cron trigger on deploy workflow — event-driven only via repository_dispatch (scrapers-complete)"
  - "notify job uses if:always() + needs.deploy.result == 'failure' to send alerts only on deploy failure"
  - "GH_DEPLOY_PAT required in scraper CI (not in deploy workflow itself) — GITHUB_TOKEN cannot trigger new workflows"
  - "timeout-minutes: 150 (2.5h) — configurable in deploy-nightly.yml for large dataset scenarios"

patterns-established:
  - "Deploy notification pattern: separate notify job with needs dependency and failure condition"
  - "Operator guide structure: overview + architecture + CLI reference + rollback + troubleshooting + deploy logs + setup + traceability"

requirements-completed: [DEP-01, DEP-02, DEP-03, DEP-04, DEP-05]

duration: 10min
completed: 2026-03-20
---

# Phase 8 Plan 03: Deploy Workflow & Operator Guide Summary

**GitHub Actions webhook-triggered deploy workflow (repository_dispatch scrapers-complete) and 429-line operator guide covering all 4 CLI commands, step-by-step rollback, 8-row troubleshooting table, and DEP-01..DEP-05 traceability.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-20T01:26:10Z
- **Completed:** 2026-03-20T01:36:00Z
- **Tasks:** 3 of 3 complete
- **Files modified:** 2

## Accomplishments

- Created `.github/workflows/deploy-nightly.yml` with `repository_dispatch` (scrapers-complete) + `workflow_dispatch`, 150-min timeout, deploy job running `deploy_worker.py --run`, and notify job sending failure alerts via `alert_worker.py`
- Created `docs/deploy-guide.md` (429 lines) with architecture diagram, CLI reference for all 4 commands, step-by-step rollback procedure, 8-row troubleshooting table, deploy_logs schema, GitHub Actions setup guide, and DEP-01..DEP-05 requirements traceability
- Confirmed no `cron` or `schedule` trigger in deploy workflow (event-driven locked decision honored)

## Task Commits

Each task was committed atomically:

1. **Task 1: GitHub Actions deploy-nightly.yml workflow** - `607e623` (feat)
2. **Task 2: Operator guide (docs/deploy-guide.md)** - `a39119a` (feat)

3. **Task 3: Verify deploy system end-to-end** — checkpoint:human-verify APPROVED (31 tests passing, all 4 CLI subcommands working, no cron trigger, DeployLog model present, Alembic migration configured)

**Plan metadata:** (docs commit — see final commit below)

## Files Created/Modified

- `.github/workflows/deploy-nightly.yml` - Webhook-triggered GitHub Actions deploy workflow (70 lines)
- `docs/deploy-guide.md` - Complete operator guide with CLI reference, rollback, troubleshooting, traceability (429 lines)

## Decisions Made

- No cron trigger — deploy-nightly.yml uses only `repository_dispatch` + `workflow_dispatch` (event-driven architecture, locked in 08-CONTEXT)
- notify job uses `if: always()` with step-level `if: needs.deploy.result == 'failure'` — runs always but only alerts on actual failures
- `GH_DEPLOY_PAT` PAT is used in the scraper CI (not in deploy-nightly.yml itself) to trigger repository_dispatch; `GITHUB_TOKEN` cannot trigger new workflow runs
- `timeout-minutes: 150` (2.5h) as configurable upper bound documented in troubleshooting section

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration:**

- `GH_DEPLOY_PAT` — Personal Access Token with `repo` scope. Add to GitHub repo > Settings > Secrets and variables > Actions > New repository secret.
  - Generate at: GitHub Settings > Developer settings > Personal access tokens > Generate new token (classic) > check `repo` scope
  - This PAT is used in the scraper CI pipeline to fire the `repository_dispatch` event to trigger the deploy workflow.

All other secrets (`DATABASE_URL_SYNC`, `TELEGRAM_BOT_TOKEN`, etc.) were set up in earlier phases.

## Next Phase Readiness

- Phase 8 deploy system complete — all plans executed and human-verified
- Phase 9 (Data Quality & Reporting) can proceed immediately
- Scraper CI pipeline integration point documented: add `gh api repos/.../dispatches -f event_type=scrapers-complete` with `GH_DEPLOY_PAT` to scraper CI "all done" job

---
*Phase: 08-deploy-release-strategy*
*Completed: 2026-03-20*
