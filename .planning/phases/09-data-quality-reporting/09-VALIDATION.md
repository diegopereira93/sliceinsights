---
phase: 9
slug: data-quality-reporting
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing — all phases use it) |
| **Config file** | none — runs with `pytest tests/` |
| **Quick run command** | `pytest tests/test_quality_aggregator.py tests/test_quality_dashboard.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_quality_aggregator.py tests/test_quality_dashboard.py tests/test_quality_report.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | QC-03 | unit | `pytest tests/test_quality_aggregator.py::test_persist_metrics -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | QC-02 | unit | `pytest tests/test_quality_aggregator.py -x` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | QC-04 | unit | `pytest tests/test_quality_dashboard.py -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | QC-01 | manual | n/a — GitHub Actions workflow trigger | N/A | ⬜ pending |
| 09-03-01 | 03 | 3 | QC-05 | unit | `pytest tests/test_quality_report.py -x` | ❌ W0 | ⬜ pending |
| 09-03-02 | 03 | 3 | QC-06 | unit | `pytest tests/test_quality_report.py::test_anomaly_detection -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_quality_aggregator.py` — stubs for QC-02, QC-03
- [ ] `tests/test_quality_dashboard.py` — stubs for QC-04
- [ ] `tests/test_quality_report.py` — stubs for QC-05, QC-06

*Existing infrastructure (pytest, conftest.py) covers all phase requirements — no new framework installation needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| quality-audit.yml triggers and runs all 11 scrapers on schedule | QC-01 | GitHub Actions cron — cannot be triggered locally | Trigger via workflow_dispatch in GitHub UI; verify matrix jobs complete with status=pass in workflow summary |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
