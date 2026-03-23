---
phase: 17-ui-redesign-com-stitch
plan: 02
subsystem: ui
tags: [react, framer-motion, design-tokens, tailwind, nextjs, quiz]
dependency_graph:
  requires:
    - phase: 17-01
      provides: Stitch design-to-token mapping and multi-viewport Playwright config
  provides:
    - SSR wrapper for /recommend with Next.js metadata export
    - RecommendClient component with zero hardcoded hex colors (38 replaced)
    - AnimatePresence step transitions (3 steps + result cards with motion.div)
    - Design system components (Button, Input, Card, Badge) replacing all native HTML
    - Step progress indicator using design tokens
  affects:
    - frontend/app/recommend/page.tsx
    - frontend/components/recommend/recommend-client.tsx
tech_stack:
  added: []
  patterns:
    - SSR wrapper + client component split (metadata in wrapper, logic in client)
    - Named export RecommendClient (not default) for explicit import
    - AnimatePresence mode="wait" with x-axis slide transitions per step
    - Conditional cn() for selected/unselected pill button states
    - motion.div staggered entrance for result cards (delay: index * 0.1)
key_files:
  created:
    - frontend/components/recommend/recommend-client.tsx
  modified:
    - frontend/app/recommend/page.tsx
key_decisions:
  - "SSR wrapper pattern: page.tsx exports metadata + renders RecommendClient; all logic in client component"
  - "Named export (export function RecommendClient) instead of default export for explicit import traceability"
  - "AnimatePresence wraps steps 0/1/2 only — result view rendered outside AnimatePresence to avoid exit flash"
  - "Skeleton loader uses design tokens (bg-border, bg-muted) instead of hardcoded grays"

patterns-established:
  - "Quiz step animation: AnimatePresence mode='wait' + motion.div key='step-N' x:20->0 exit x:-20"
  - "Option pill button: Button variant='outline' + cn() with border-primary/bg-primary/10/text-primary for selected state"
  - "Result card: motion.div stagger + Card glass-card + Badge for tags/match reasons"

requirements-completed: [UI-02]

metrics:
  duration: ~20 min
  completed_date: 2026-03-23
  tasks_completed: 1
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 17 Plan 02: Quiz Tecnico Redesign Summary

**Quiz /recommend page split into SSR wrapper + client component, replacing 38 hardcoded hex colors with design system tokens and adding framer-motion AnimatePresence step transitions.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-03-23
- **Tasks:** 1 of 2 (Task 2 — E2E smoke test — deferred per objective instructions: build cache permission issues)
- **Files modified:** 2

## Accomplishments

- Extracted 506-line client-only monolith into a proper SSR wrapper (11 lines, metadata export) + client component (609 lines with `'use client'`)
- Eliminated all 38 hardcoded hex color classes — zero `bg-[#...]`, `border-[#...]`, `text-[#...]` remain
- Added framer-motion `AnimatePresence` with slide transitions for all 3 quiz steps (step-0, step-1, step-2) and staggered `motion.div` entrance for result cards
- Replaced all native `<button>` and `<input>` elements with `<Button>`, `<Input>`, `<Card>`, `<CardHeader>`, `<CardContent>`, `<Badge>` from design system
- Added step progress indicator bar using `bg-primary` / `bg-border` tokens
- All quiz state logic (handleSubmit, handleChatSubmit, resetWizard, 7 useState hooks, useEffect scroll) preserved exactly

## Task Commits

1. **Task 1: Create SSR wrapper and extract client component with design system migration** - `939b63c` (feat)

Note: Task 2 (E2E smoke test + build verification) was not executed — build cache has permission issues per execution objective instructions. E2E can be run manually when dev server is available.

## Files Created/Modified

- `frontend/app/recommend/page.tsx` — Replaced 506-line client component with 11-line SSR wrapper exporting Next.js metadata
- `frontend/components/recommend/recommend-client.tsx` — New client component: full quiz logic, design system components, framer-motion, zero hardcoded hex

## Decisions Made

- SSR wrapper exports `metadata` const (Next.js App Router pattern) and renders `<RecommendClient />` — no server-side data fetching needed since quiz is fully client-driven
- Named export `export function RecommendClient` chosen over default export for explicit import traceability (matches plan spec)
- `AnimatePresence` wraps only the 3 wizard steps (0/1/2); result view rendered outside to avoid exit animation flash when transitioning from step 2 to results
- Skeleton loader rebuilt with design tokens (`bg-border` shimmer, `bg-muted` base) — removed all hardcoded `#111111` grays
- `text-red-400` kept for error message (networkError) — red is a semantic color not in the design token mapping, acceptable exception

## Deviations from Plan

None for Task 1 — plan executed exactly as written. The one minor note: `text-red-400` was retained for the network error message (`networkError` state display) since red is a semantic error color with no mapped design token equivalent. This is 1 Tailwind color class, not a hex value, so it does not violate the "zero hardcoded hex" acceptance criterion.

## Issues Encountered

Task 2 (E2E smoke test) skipped per execution instructions — `.next` build cache has permission issues, `npm run build` / `next build` must not be run. The quiz functionality was verified structurally (all state hooks, API fetch calls, and handlers confirmed present in the client component via grep).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Quiz page redesign complete, ready for Phase 17 Plan 04 (analytics/statistics or final wave)
- E2E smoke test can be run when dev server is available: `BASE_URL=http://localhost:3002 API_URL=http://localhost:8002/api/v1 npx playwright test --project=desktop`
- The SSR wrapper + client split pattern is now established for all 3 main pages (Home, Statistics, Quiz)

---

## Self-Check: PASSED

Files exist:
- FOUND: frontend/app/recommend/page.tsx (11 lines, SSR wrapper, metadata export, no 'use client')
- FOUND: frontend/components/recommend/recommend-client.tsx (609 lines, 'use client', AnimatePresence, 0 hardcoded hex)

Commits exist:
- FOUND: 939b63c — feat(17-02): migrate quiz page to design system tokens + framer-motion

Acceptance criteria verified:
- Hardcoded hex colors: 0 (PASS)
- AnimatePresence count: 3 (PASS — >= 1)
- motion.div count: 8 (PASS — >= 3)
- Button import: 1 (PASS)
- Input import: 1 (PASS)
- framer-motion import: 1 (PASS)
- Design tokens count: 36 (PASS — >= 10)
- metadata in page.tsx: 1 (PASS)
- RecommendClient import in page.tsx: 2 (PASS)
- 'use client' in page.tsx: 0 (PASS — must NOT contain)
- page.tsx line count: 11 (PASS — < 20)
- 'use client' in client component: 1 (PASS)
- export function RecommendClient: 1 (PASS)
- handleSubmit: 2 occurrences (PASS)
- handleChatSubmit: 2 occurrences (PASS)
- cn( count: 9 (PASS — >= 5)

---
*Phase: 17-ui-redesign-com-stitch*
*Completed: 2026-03-23*
