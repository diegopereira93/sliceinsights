---
phase: 17
slug: ui-redesign-com-stitch
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright E2E |
| **Config file** | `playwright.config.ts` |
| **Quick run command** | `npx playwright test --reporter=line` |
| **Full suite command** | `npx playwright test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npx playwright test --reporter=line`
- **After every plan wave:** Run `npx playwright test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-W0-01 | 01 | 0 | baseline | e2e | `npx playwright test` | ✅ | ⬜ pending |
| 17-W1-01 | 01 | 1 | /recommend redesign | e2e | `npx playwright test --grep recommend` | ✅ | ⬜ pending |
| 17-W2-01 | 02 | 2 | /home redesign | e2e | `npx playwright test --grep home` | ✅ | ⬜ pending |
| 17-W2-02 | 02 | 2 | /statistics redesign | e2e | `npx playwright test --grep statistics` | ✅ | ⬜ pending |
| 17-W3-01 | 03 | 3 | responsividade mobile | e2e | `npx playwright test --project=mobile` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Document baseline screenshot E2E (26/26 testes passando antes do redesign)
- [ ] Adicionar projeto mobile ao `playwright.config.ts` para testes de responsividade
- [ ] Adicionar testes de screenshot visual para as 4 páginas alvo
- [ ] Configurar Stitch MCP no projeto antes de iniciar redesign

*Wave 0 bloqueia todos os outros waves.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Qualidade visual do design Stitch | UI Redesign | Julgamento estético não automatizável | Revisar cada página redesenhada no browser com viewport 375px, 768px, 1280px |
| Fidelidade ao design system | Design tokens | Inspeção visual de cores e tipografia | Verificar que nenhuma cor hex hardcoded aparece em `/recommend/page.tsx` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
