---
phase: 10
slug: slo-gate-fix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/test_slo_validator.py tests/test_deploy_validator.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_slo_validator.py tests/test_deploy_validator.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | SLO-03 | unit | `pytest tests/test_slo_validator.py -v -k "pass"` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | SLO-03 | unit | `pytest tests/test_slo_validator.py -v -k "completeness"` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 2 | DEP-01 | integration | `pytest tests/test_deploy_validator.py -v -k "slo_gate"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_slo_validator.py` — create from scratch with stubs for `check_freshness` pass branch and `check_completeness` per-scraper pass branch

*`tests/test_deploy_validator.py` already exists — no stub needed for deploy gate tests.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
