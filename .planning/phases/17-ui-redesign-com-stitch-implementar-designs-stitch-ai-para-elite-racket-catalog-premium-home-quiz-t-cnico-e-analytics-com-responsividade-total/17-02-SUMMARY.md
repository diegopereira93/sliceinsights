---
phase: 17-ui-redesign
plan: 02
subsystem: backend-api
tags: [orval, api-shim, fastapi, recommendations]
dependency_graph:
  requires:
    - 17-01
  provides:
    - /api/healthz
    - /api/paddles
    - /api/paddles/{id}
    - /api/quiz/recommend
    - /api/leads
    - /api/chat
    - /api/stats/market
    - /api/stats/brands
    - /api/stats/hidden-gems
  affects: [frontend-vite]
tech_stack:
  added: []
  patterns: [fastapi-router, sqlmodel-relationships, orval-schema-bridge]
key_files:
  created:
    - app/api/endpoints/orval_shim.py
  modified:
    - app/main.py
decisions:
  - Sequential integer ID mapping for /api/paddles/{id} using row_number() for frontend compatibility
  - Router has prefix /api internally (no /v1) to match Orval client paths exactly
  - Reused existing RecommendationEngine for quiz recommendations
  - CORS already configured for localhost:3002
---

# Phase 17 Plan 02: Orval-Compatible Shim Endpoints Summary

**One-liner:** Created 9 FastAPI endpoints in `orval_shim.py` that serve exact JSON schemas expected by the Vite frontend React Query hooks.

## Objective

Create Orval-compatible shim endpoints in FastAPI that serve the exact JSON schemas expected by the redesign-slice API client (paddle listing/detail, quiz recommendation, leads, chat, stats, healthz).

## Tasks

### Task 1: Create orval_shim.py with all Orval-compatible endpoints

| Attribute | Value |
|-----------|-------|
| Type | auto |
| Files | app/api/endpoints/orval_shim.py |
| Lines | 683 |
| Endpoints | 9 |

**Action:** Created `app/api/endpoints/orval_shim.py` with:

- `paddle_to_orval()` helper: Maps PaddleMaster SQLModel to Orval Paddle dict with sequential integer ID
- `budget_to_max()` helper: Converts quiz budget string to max price
- All 9 endpoints with correct paths and response schemas

**Endpoints implemented:**

| Path | Method | Description |
|------|--------|-------------|
| /api/healthz | GET | Health check |
| /api/paddles | GET | List paddles with filters (brand, minPrice, maxPrice, coreThickness, search) |
| /api/paddles/{id} | GET | Get single paddle by sequential ID |
| /api/quiz/recommend | POST | Get recommendations based on QuizAnswers |
| /api/leads | POST | Create lead |
| /api/chat | POST | Chat with LLM assistant |
| /api/stats/market | GET | Market statistics (distributions, power vs control) |
| /api/stats/brands | GET | Brand rankings |
| /api/stats/hidden-gems | GET | High rating, low price, not featured |

### Task 2: Mount orval_shim router in FastAPI main.py

| Attribute | Value |
|-----------|-------|
| Type | auto |
| Files | app/main.py |

**Action:** Added import and `app.include_router(orval_shim_router)` without prefix (router has `/api` internally).

## Verification

All acceptance criteria passed:

- File `app/api/endpoints/orval_shim.py` exists and is 683 lines (>= 200) ✅
- 9 `@router.` decorators (at least 9) ✅
- Router has `prefix="/api"` ✅
- Helper function `paddle_to_orval` exists ✅
- All 9 endpoint paths exist ✅
- main.py includes orval_shim (2 occurrences) ✅
- main.py has `include_router(orval_shim_router)` ✅

## Deviations from Plan

**None** - plan executed exactly as written.

## Metrics

| Metric | Value |
|--------|-------|
| Tasks completed | 2/2 |
| Files created | 1 |
| Files modified | 1 |
| Total lines added | 683 |
| Duration | ~5 min |

## Self-Check

- [x] File created: `app/api/endpoints/orval_shim.py` (683 lines)
- [x] Commit exists: `a269090`
- [x] main.py modified with orval_shim_router
- [x] All 9 endpoints implemented with correct paths
- [x] Response schemas match Orval client expectations
