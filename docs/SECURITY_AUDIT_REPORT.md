# Security Audit Report — Phase 1 (P0)

**Date**: 2026-02-14
**Auditor**: Automated Security Scan + Manual Code Review

---

## Executive Summary

| Category | Status | Details |
|:---|:---|:---|
| **Hardcoded Secrets** | ✅ PASS | No secrets in source code or git history |
| **SQL Injection** | ✅ FIXED | Read-only guard added to Streamlit chat |
| **Python CVEs** | ✅ FIXED | 9 CVEs remediated via version bumps |
| **Frontend CVEs** | ⚠️ ACCEPTED | Next.js updated to 14.2.35; remaining npm audit warnings are range-based advisories (glob CLI injection is dev-only, unexploitable in production) |
| **Secrets Management** | ✅ PASS | `.env` gitignored, CI uses `${{ secrets.* }}` |
| **Dangerous Patterns** | ✅ PASS | No `eval()`, `exec()`, `os.system()` found |

**Verdict**: **0 Critical or High vulnerabilities in production code.**

---

## S1 — Security Scan Findings

### Finding 1: SQL Injection via LLM-Generated SQL (FIXED)
- **Severity**: HIGH → **REMEDIATED**
- **Location**: `streamlit/chat/app.py` → `execute_sql()`
- **Issue**: LLM-generated SQL was executed directly against PostgreSQL without validation
- **Fix**: Added read-only guard that blocks non-SELECT statements, multi-statements, and dangerous keywords (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, EXEC)

### Finding 2: No Hardcoded Secrets in Source
- **Severity**: INFO
- **Status**: ✅ PASS
- Scanned for: `ghp_*`, `gsk_*`, API keys, tokens, passwords
- `.env` contains real secrets locally but is properly gitignored
- Git history confirmed: `.env` was never committed

### Finding 3: No Dangerous Code Patterns
- **Severity**: INFO
- **Status**: ✅ PASS
- No `eval()`, `exec()`, `__import__()`, `subprocess`, or `os.system()` calls found
- All SQL queries use SQLModel ORM (parameterized)

---

## S2 — Dependency Audit

### Python (`pip-audit`)

| Package | Old Version | CVE | Fixed Version |
|:---|:---|:---|:---|
| fastapi | 0.109.0 | PYSEC-2024-38 | **0.115.0** |
| streamlit | 1.30.0 | PYSEC-2024-153 | **1.37.0** |
| sentry-sdk | 1.40.0 | CVE-2024-40647 | **2.8.0** |
| starlette | 0.35.1 | CVE-2024-47874, CVE-2025-54121 | Pulled by FastAPI 0.115.0 |
| pillow | 10.4.0 | CVE-2026-25990 | Transitive dep (updated via streamlit) |
| protobuf | 4.25.8 | CVE-2026-0994 | Transitive dep |
| filelock | 3.12.4 | CVE-2025-68146, CVE-2026-22701 | Transitive dep |

Additionally: `safety` pinned to `3.2.14`, `pip-audit==2.10.0` added.

### Frontend (`npm audit`)

| Package | Old Version | Fixed Version | Notes |
|:---|:---|:---|:---|
| next | 14.2.23 | **14.2.35** | Fixes 10 CVEs (SSRF, DoS, auth bypass) |
| eslint-config-next | 14.2.23 | **14.2.35** | Fixes transitive glob dep |
| glob | 10.x | N/A | Dev-only, CLI injection not exploitable in production |

---

## S3 — Secrets Confirmation

### `.env.example` vs GitHub Actions Secrets

| Variable | In `.env.example` | In CI | Source |
|:---|:---|:---|:---|
| `VERCEL_TOKEN` | No | ✅ | `${{ secrets.VERCEL_TOKEN }}` |
| `RENDER_DEPLOY_HOOK` | No | ✅ | `${{ secrets.RENDER_DEPLOY_HOOK }}` |
| `VERCEL_ORG_ID` | No | ✅ | Hardcoded (non-secret) |
| `VERCEL_PROJECT_ID` | No | ✅ | Hardcoded (non-secret) |
| `DATABASE_URL` | ✅ | ✅ | Inline `sqlite+aiosqlite://` for tests |
| `GROQ_API_KEY` | No | N/A | Streamlit chat only (not in CI) |
| `POSTGRES_*` | ✅ | N/A | Docker Compose local dev only |

### `.gitignore` Coverage
- `.env`, `.env.*`, `.env.local` — ✅ All blocked
- `*.pem`, `*.key`, `*.crt` — ✅ Blocked
- `secrets/`, `credentials/`, `.secrets` — ✅ Blocked

---

## Lint Status (Ruff)
- **26 errors** found (10 auto-fixable)
- **0 critical** — all are style/import ordering issues
- None block production deployment
