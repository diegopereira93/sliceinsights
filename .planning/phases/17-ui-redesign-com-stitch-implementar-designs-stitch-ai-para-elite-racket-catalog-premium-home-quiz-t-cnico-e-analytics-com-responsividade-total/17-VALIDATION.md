---
phase: 17
slug: ui-redesign-vite-spa-migration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 17 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright (E2E) |
| **Config file** | `frontend-vite/playwright.config.ts` (Wave 0 cria) |
| **Quick run command** | `cd frontend-vite && npx playwright test --project=desktop --reporter=dot` |
| **Full suite command** | `cd frontend-vite && npx playwright test --project=desktop,mobile,tablet` |
| **Estimated runtime** | ~60 seconds |

## Sampling Rate

- **After every task commit:** Quick run command
- **After every plan wave:** Full suite
- **Before `/gsd:verify-work`:** Full suite verde
- **Max feedback latency:** 60 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | UI-01 | e2e | `cd frontend-vite && npx playwright test e2e/pages.spec.ts --project=desktop` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 1 | UI-03 | e2e | `cd frontend-vite && npx playwright test e2e/api-compat.spec.ts` | ❌ W0 | ⬜ pending |
| 17-03-01 | 03 | 2 | UI-04 | e2e | `cd frontend-vite && npx playwright test e2e/pages.spec.ts --project=desktop` | ❌ W0 | ⬜ pending |
| 17-04-01 | 04 | 2 | UI-05 | e2e | `cd frontend-vite && npx playwright test e2e/responsiveness.spec.ts --project=mobile` | ❌ W0 | ⬜ pending |

## Wave 0 Requirements

- [ ] `frontend-vite/playwright.config.ts` — viewport projects (desktop 1280px, tablet 768px, mobile 375px)
- [ ] `frontend-vite/e2e/pages.spec.ts` — 4 rotas carregam sem erro (/, /recommend, /statistics, /chat)
- [ ] `frontend-vite/e2e/api-compat.spec.ts` — chamadas ao FastAPI retornam 200
- [ ] `frontend-vite/e2e/responsiveness.spec.ts` — sem overflow horizontal em 375px/768px/1280px

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fidelidade visual vs redesign-slice | UI-01 | Comparação visual | Abrir localhost:5173 e comparar com screenshots do Replit |
| Chat AI response quality | UI-03 | Qualidade LLM subjetiva | Enviar mensagem em /chat e verificar resposta coerente |

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
