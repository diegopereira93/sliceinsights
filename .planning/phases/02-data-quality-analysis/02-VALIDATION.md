---
phase: 02
slug: data-quality-analysis
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-19
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + smoke_test_quality.py (standalone) |
| **Config file** | none detected at project root |
| **Quick run command** | `docker compose exec -T backend_v3 python scripts/smoke_test_quality.py` |
| **Full suite command** | `docker compose exec -T backend_v3 pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec -T backend_v3 python scripts/smoke_test_quality.py`
- **After every plan wave:** Full audit re-run + smoke test
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-00-01 | 00 | 1 | AUDIT-05 | smoke | `docker compose exec -T backend_v3 python scripts/measure_freshness.py` | ❌ W0 | ⬜ pending |
| 02-00-02 | 00 | 1 | QUAL-05 | smoke | `docker compose exec -T backend_v3 python scripts/measure_coverage.py` | ❌ W0 | ⬜ pending |
| 02-01-01 | 01 | 1 | QUAL-02 | smoke | `docker compose exec -T backend_v3 python scripts/audit_data_quality.py` | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | QUAL-02 | smoke | `docker compose exec -T backend_v3 python scripts/smoke_test_quality.py` | ✅ | ⬜ pending |
| 02-01-03 | 01 | 1 | AUDIT-05 | smoke | `docker compose exec -T backend_v3 python scripts/measure_freshness.py` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | QUAL-05 | smoke | `docker compose exec -T backend_v3 python scripts/measure_coverage.py` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | QUAL-01 | manual | Review DATA_QUALITY.md for metrics definitions | N/A | ⬜ pending |
| 02-02-02 | 02 | 2 | QUAL-03 | manual | Review incomplete_records section in DATA_QUALITY.md | N/A | ⬜ pending |
| 02-02-03 | 02 | 2 | QUAL-04 | manual | Review VALIDATION_RULES.md | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/measure_freshness.py` — covers AUDIT-05 (per-source data freshness)
- [ ] `scripts/measure_coverage.py` — covers QUAL-05 (per-scraper coverage counts)
- [ ] `.planning/phases/02-data-quality-analysis/artifacts/` directory creation

*Wave 0 scripts are created in Plan 02-00.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Quality metrics defined | QUAL-01 | Document deliverable | Review DATA_QUALITY.md "Quality Metrics" section |
| Incomplete records listed | QUAL-03 | Requires domain judgment | Verify each listed record has identifiable issues |
| Validation rules documented | QUAL-04 | Document deliverable | Review VALIDATION_RULES.md against paddle.py source |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
