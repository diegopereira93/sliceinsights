---
phase: 15
slug: ai-recommendation-assistant
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `backend/pytest.ini` (or `pyproject.toml`) |
| **Quick run command** | `cd backend && pytest tests/api/test_api_recommendations.py -x -q` |
| **Full suite command** | `cd backend && pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/api/test_api_recommendations.py -x -q`
- **After every plan wave:** Run `cd backend && pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 0 | REC-01 | unit | `pytest tests/api/test_api_recommendations.py -x -q` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | REC-01 | integration | `pytest tests/api/test_api_recommendations.py::test_recommend_returns_results -x -q` | ❌ W0 | ⬜ pending |
| 15-01-03 | 01 | 1 | REC-02 | integration | `pytest tests/api/test_api_recommendations.py::test_recommend_includes_market_offers -x -q` | ❌ W0 | ⬜ pending |
| 15-01-04 | 01 | 1 | REC-03 | integration | `pytest tests/api/test_api_recommendations.py::test_recommend_no_match -x -q` | ❌ W0 | ⬜ pending |
| 15-02-01 | 02 | 2 | REC-01 | e2e-manual | Manual: submit quiz in browser, verify cards render | N/A | ⬜ pending |
| 15-02-02 | 02 | 2 | REC-02 | e2e-manual | Manual: verify justification text appears in cards | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/api/test_api_recommendations.py` — update plural→singular endpoint, add no-match test, market_offers test, chat endpoint stub
- [ ] `backend/tests/api/conftest.py` — ensure fixtures include mock `RecommendationEngine` and `LLMService`

*Existing infrastructure (pytest, FastAPI TestClient) covers all phase requirements. No new framework installs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Recommendation cards render with image, specs, justification, and buy link | REC-01, REC-02 | UI rendering requires browser | Open `/catalog`, submit quiz, verify at least one card appears with all fields |
| "No match" graceful message shown | REC-03 | UI state requires interaction | Submit profile that yields no catalog match, verify friendly message (not empty/error) |
| Chat follow-up messages respond correctly | REC-02 | Conversational flow requires live LLM | Send follow-up question after recommendations, verify LLM responds in context |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
