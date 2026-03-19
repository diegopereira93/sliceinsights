---
phase: 4
slug: audit-report-recommendations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash / grep (document validation — no test runner needed) |
| **Config file** | none |
| **Quick run command** | `bash .planning/phases/04-audit-report-\&-recommendations/validate.sh` |
| **Full suite command** | `bash .planning/phases/04-audit-report-\&-recommendations/validate.sh --full` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick validation (grep checks on output files)
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 04-A-01 | A | 1 | ART-01 | file-exists + grep | `test -f docs/AUDIT_REPORT.md && grep -q "Health Score" docs/AUDIT_REPORT.md` | ⬜ pending |
| 04-A-02 | A | 1 | ART-01 | grep | `grep -q "54.5\|6/11" docs/AUDIT_REPORT.md` | ⬜ pending |
| 04-A-03 | A | 1 | ART-03 | grep | `grep -q "Invisible\|invisible" docs/AUDIT_REPORT.md` | ⬜ pending |
| 04-A-04 | A | 1 | ART-04 | grep | `grep -q "Refactoring Roadmap\|Priority 1" docs/AUDIT_REPORT.md` | ⬜ pending |
| 04-B-01 | B | 1 | ART-02 | file-exists + grep | `test -f docs/DATA_QUALITY.md && grep -q "86 paddles\|86 Paddles" docs/DATA_QUALITY.md` | ⬜ pending |
| 04-C-01 | C | 2 | ART-05 | file-exists + grep | `test -f docs/operations/RUNBOOK_SCRAPERS.md && grep -q "scrape_joola.py" docs/operations/RUNBOOK_SCRAPERS.md` | ⬜ pending |
| 04-C-02 | C | 2 | ART-05 | grep | `grep -q "playwright install chromium" docs/operations/RUNBOOK_SCRAPERS.md` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Not applicable — this phase creates new markdown documents from existing data artifacts. No test infrastructure setup needed.

*Existing Phase 1-3 artifacts contain all source data. No stubs or fixtures needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AUDIT_REPORT.md is 40+ pages | ART-01 | Page count requires human review | `wc -l docs/AUDIT_REPORT.md` → should be ≥ 400 lines (proxy for ~40 pages) |
| Report narrative is coherent | ART-01, ART-03 | Coherence is subjective | Read Executive Summary + Part 5 Recommendations for editorial quality |
| Runbook commands are executable | ART-05 | Requires Docker environment | Run one scraper command from RUNBOOK_SCRAPERS.md manually in the environment |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
