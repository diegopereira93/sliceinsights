# Phase 10: SLO Gate Fix - Research

**Researched:** 2026-03-20
**Domain:** Python bug fix — SLO validator status logic + deploy gate integration
**Confidence:** HIGH

## Summary

Phase 10 is a targeted bug fix with a clearly identified root cause. The `check_freshness()` function in `scripts/slo_validator.py` maps `age_hours < FRESHNESS_SLO_HOURS` to `status = "skip"` instead of `status = "pass"`. Since `deploy_validator.py:check_slo_gate()` queries `slo_logs` for `status = 'pass'`, the gate always returns zero passed scrapers and the nightly deploy always aborts.

The fix is surgical: two status-logic corrections in `slo_validator.py` and new test coverage for the `pass` branch in both test files. No schema changes, no new dependencies, no workflow changes required.

`check_completeness()` already emits `pass` for the `within_slo` branch (lines 182-184 of `slo_validator.py`), but it only writes a single `__all__` row, never per-scraper rows. `check_slo_gate()` explicitly excludes `scraper_name = '__all__'`, so completeness `pass` rows are also invisible to the deploy gate. The completeness fix requires either writing per-scraper rows or confirming the deploy gate only needs freshness passes.

**Primary recommendation:** Fix `check_freshness()` to emit `pass` when `age_hours < FRESHNESS_SLO_HOURS`, and confirm whether `check_completeness()` needs per-scraper rows or if freshness `pass` alone is sufficient for the deploy gate.

## Bug Analysis (HIGH confidence)

### Bug 1: check_freshness() missing `pass` branch

**File:** `scripts/slo_validator.py`, lines 113-118

**Current code:**
```python
if age_hours < FRESHNESS_SLO_HOURS:
    status = "skip"
    reason = "recently_updated"
else:
    status = "fail"
    reason = "stale_data"
```

**Problem:** When a scraper runs within the SLO window, it gets `status = "skip"`. The deploy gate queries `status = 'pass'` exclusively — `skip` rows are never matched.

**Fix:** Change `status = "skip"` / `reason = "recently_updated"` to `status = "pass"` / `reason = "within_slo"` in this branch. This mirrors the naming pattern already used in `check_completeness()` (line 183-184).

### Bug 2: check_completeness() writes only `__all__` row

**File:** `scripts/slo_validator.py`, lines 161, 196

**Current code:** `target = scraper_name if scraper_name is not None else "__all__"` — then a single `SLOLog` row is written with `scraper_name=target`.

**Problem:** When called from `main()` with `scraper_name=None`, `target = "__all__"`. `check_slo_gate()` filters `AND scraper_name != '__all__'`, so this row is never counted as a pass.

**Scope question for planner:** The phase deliverables say "writes per-scraper `pass` rows". The current `check_completeness()` design is intentionally global (paddle_master has no per-scraper partition — see STATE.md decision: "Completeness checks global paddle_master catalog"). The fix options are:
1. Write one `pass` row per known scraper name (requires a scraper list — either from config or from a MarketOffer query)
2. Change `check_slo_gate()` to accept `__all__` completeness passes as sufficient
3. Keep completeness as-is and rely only on freshness `pass` rows for the deploy gate

Option 2 or 3 is architecturally consistent with the existing design decision. Option 1 introduces coupling between completeness and the scraper list. **The planner should pick option 2 or 3 unless explicitly told otherwise.**

## Standard Stack

No new dependencies. All fixes use existing imports.

| Component | File | Role |
|-----------|------|------|
| `SLOLog` ORM model | `app/models/slo.py` | Written by validator, queried by deploy gate |
| `FRESHNESS_SLO_HOURS` | `scripts/slo_config.py` | Threshold constant (24) |
| `COMPLETENESS_SLO_HOURS` | `scripts/slo_config.py` | Threshold constant (168 = 7 days) |
| `check_slo_gate()` | `scripts/deploy_validator.py` lines 33-62 | Queries `status='pass'` — unchanged |
| `pytest` + `unittest.mock` | `tests/` | Test framework already in use |

## Architecture Patterns

### Existing test pattern (from `test_deploy_validator.py`)

Tests use `MagicMock` sessions with `side_effect` lists for sequential DB calls. New tests for `check_freshness()` pass branch must follow the same pattern used in `test_slo_validator.py` (file does not exist yet — must be created from scratch).

### SLOLog row structure
```python
SLOLog(
    scraper_name=store,      # e.g. "mercado_livre"
    metric_type="freshness",
    value_hours=age_hours,
    threshold_hours=float(FRESHNESS_SLO_HOURS),
    status="pass",           # was "skip"
    details={"reason": "within_slo", ...},
)
```

### check_freshness() corrected logic
```python
if age_hours < FRESHNESS_SLO_HOURS:
    status = "pass"
    reason = "within_slo"
else:
    status = "fail"
    reason = "stale_data"
```

### Test pattern for pass branch (to create in test_slo_validator.py)
```python
# Source: mirrors test_deploy_validator.py patterns
def test_check_freshness_pass_when_within_slo():
    """check_freshness writes status=pass when age_hours < FRESHNESS_SLO_HOURS."""
    from scripts.slo_validator import check_freshness
    from unittest.mock import MagicMock, patch
    from datetime import datetime, timezone, timedelta

    session = MagicMock()
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=2)  # 2h old — within 24h SLO

    row = MagicMock()
    row.store_name = "mercado_livre"
    row.newest = recent

    session.exec.return_value.all.return_value = [row]

    with patch("scripts.slo_validator._now_utc", return_value=now):
        logs = check_freshness(session, scraper_name="mercado_livre")

    assert len(logs) == 1
    assert logs[0].status == "pass"
    assert logs[0].scraper_name == "mercado_livre"
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| SLO threshold value | Hardcode 24 | `FRESHNESS_SLO_HOURS` from `scripts/slo_config.py` |
| UTC time | `datetime.now()` | `_now_utc()` helper already in `slo_validator.py` |
| Timezone handling | Manual `.replace(tzinfo=...)` | `_make_aware()` helper already in `slo_validator.py` |

## Common Pitfalls

### Pitfall 1: Changing `skip` semantics globally
**What goes wrong:** If `age_hours < FRESHNESS_SLO_HOURS` is changed to `pass`, the docstring and comment on lines 113-114 still say "SKIP". Tests may rely on the old string.
**How to avoid:** Update docstring, inline comment, and print statement in the same commit. Search for any test that asserts `status == "skip"` for the `recently_updated` case.

### Pitfall 2: test_slo_validator.py does not exist
**What goes wrong:** The deliverable says "Updated `tests/test_slo_validator.py`" but the file is absent. It must be created, not edited.
**How to avoid:** The plan task must `Write` the file from scratch, not `Edit` a missing file.

### Pitfall 3: `session.exec()` vs `session.execute()`
**What goes wrong:** `slo_validator.py` uses SQLModel's `session.exec()`. `deploy_validator.py` uses SQLAlchemy's `session.execute()`. Mock setup differs.
**How to avoid:** In tests for `slo_validator.py`, mock `session.exec().all()` not `session.execute().fetchall()`.

### Pitfall 4: completeness `pass` scope
**What goes wrong:** Writing per-scraper completeness rows requires a scraper list that doesn't exist in the function's current scope.
**How to avoid:** Decide the completeness fix strategy before writing code. The safest fix consistent with existing design: change `check_slo_gate()` to also accept `__all__` completeness passes, OR simply rely on freshness `pass` rows alone (which is the direct fix for the deploy gate blocking issue).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` or discovered from root |
| Quick run command | `pytest tests/test_slo_validator.py tests/test_deploy_validator.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Requirement | Behavior | Test Type | Automated Command | File Exists? |
|-------------|----------|-----------|-------------------|-------------|
| SLO-03 / Success 1 | `check_freshness()` emits `pass` when `age_hours < FRESHNESS_SLO_HOURS` | unit | `pytest tests/test_slo_validator.py -x -q` | No — Wave 0 |
| SLO-03 / Success 2 | `check_completeness()` writes per-scraper `pass` rows | unit | `pytest tests/test_slo_validator.py -x -q` | No — Wave 0 |
| DEP-01 / Success 3 | `check_slo_gate()` finds passed scrapers and deploy proceeds | unit | `pytest tests/test_deploy_validator.py -x -q` | Yes — needs new test method |
| All / Success 4 | `pass` branch covered for both checks | unit | `pytest tests/test_slo_validator.py tests/test_deploy_validator.py -x -q` | Partial |

### Wave 0 Gaps
- [ ] `tests/test_slo_validator.py` — file does not exist; must be created with `pass` branch tests for `check_freshness()` and `check_completeness()`
- [ ] New test method in `tests/test_deploy_validator.py` — `TestCheckSloGate` class exists but needs a test asserting that `pass` rows written by the fixed validator are found by the gate

## Sources

### Primary (HIGH confidence)
- Direct read of `scripts/slo_validator.py` — full function bodies, status logic
- Direct read of `scripts/deploy_validator.py` — `check_slo_gate()` SQL query confirmed
- Direct read of `tests/test_deploy_validator.py` — mock patterns, class structure
- `.planning/STATE.md` — decision "Completeness checks global paddle_master catalog"
- `.planning/ROADMAP.md` — Phase 10 deliverables and success criteria

## Metadata

**Confidence breakdown:**
- Bug identification: HIGH — source code read directly, logic is unambiguous
- Fix approach: HIGH — one-line change with clear precedent in `check_completeness()`
- Completeness fix scope: MEDIUM — design decision needed (option 2 vs 3)
- Test patterns: HIGH — existing test file read directly

**Research date:** 2026-03-20
**Valid until:** N/A — pure internal bug fix, no external dependencies
