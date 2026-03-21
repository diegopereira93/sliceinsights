---
phase: 14
slug: web-catalog-page
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | jest 29.x / Playwright |
| **Config file** | `frontend/jest.config.ts` / `playwright.config.ts` |
| **Quick run command** | `cd frontend && npm test -- --passWithNoTests` |
| **Full suite command** | `cd frontend && npm test && npx playwright test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --passWithNoTests`
- **After every plan wave:** Run `cd frontend && npm test && npx playwright test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | WEB-01 | unit | `cd frontend && npm test -- --testPathPattern=catalog` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | WEB-01 | unit | `cd frontend && npm test -- --testPathPattern=catalog` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | WEB-02 | unit | `cd frontend && npm test -- --testPathPattern=CatalogFilter` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 1 | WEB-02 | unit | `cd frontend && npm test -- --testPathPattern=CatalogFilter` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 2 | WEB-03 | e2e | `npx playwright test catalog` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/__tests__/catalog-page.test.tsx` — stubs for WEB-01 (catalog page renders paddle listing)
- [ ] `frontend/__tests__/catalog-filters.test.tsx` — stubs for WEB-02 (filter controls render and update listing)
- [ ] `e2e/catalog.spec.ts` — stubs for WEB-03 (paddle card link navigates to store)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Paddle images render correctly | WEB-01 | Visual check, no automated image assertion | Open catalog page, verify images load without broken icons |
| Filter UI is usable on mobile | WEB-02 | Responsive layout requires visual review | Resize browser to 375px, verify filter drawer opens and closes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
