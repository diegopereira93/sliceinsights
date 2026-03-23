---
phase: 17-ui-redesign-com-stitch
plan: 03
subsystem: frontend-ui
tags: [visual-enhancement, glassmorphism, statistics, home, paddle-card]
dependency_graph:
  requires: [17-01]
  provides: [enhanced-home-hero, premium-paddle-card, refined-statistics-ui]
  affects: [frontend/components/home-client.tsx, frontend/components/statistics-client.tsx, frontend/components/paddle/paddle-card.tsx]
tech_stack:
  added: []
  patterns: [glassmorphism, framer-motion-entrance, tailwind-design-tokens, glass-card]
key_files:
  created: []
  modified:
    - frontend/components/paddle/paddle-card.tsx
    - frontend/components/home-client.tsx
    - frontend/components/statistics-client.tsx
decisions:
  - "KPI cards upgraded from bg-card to glass-card for consistent glassmorphism across Statistics"
  - "TabsTrigger active state uses bg-primary/text-primary-foreground per Stitch design map"
  - "PaddleCard price display replaced plain text with premium Badge (bg-primary/10 border-primary/20)"
  - "Hero gradient added as section-level class, not absolute overlay, to avoid z-index issues"
metrics:
  duration: ~20min
  completed: "2026-03-23"
  tasks_completed: 2
  files_modified: 3
---

# Phase 17 Plan 03: Home & Statistics Visual Enhancement Summary

**One-liner:** Premium glassmorphism hover effects on PaddleCard, hero gradient overlay on Home, and Stitch-inspired tab + card styling on Statistics — zero logic changes.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Enhance Home hero section and PaddleCard visual design | fd77728 | home-client.tsx, paddle-card.tsx |
| 2 | Refine Statistics page layout and data presentation | 0f052e1 | statistics-client.tsx |

## What Was Built

### Task 1 — PaddleCard + Home Hero

**PaddleCard (`frontend/components/paddle/paddle-card.tsx`):**
- Added `hover:shadow-glow` to the Card className — card now glows lime on hover
- Replaced plain price `<span>` with premium `<Badge className="bg-primary/10 text-primary border border-primary/20 font-black">` for a refined price display
- Existing `whileHover={{ y: -5 }}` framer-motion lift preserved (already present)
- Existing `glass-card`, `hover:ring-2 hover:ring-primary/30`, `transition-all` preserved

**Home Hero (`frontend/components/home-client.tsx`):**
- Added `bg-gradient-to-b from-primary/5 via-background to-background` to hero `<section>` for subtle lime-tinted gradient
- Added `<div className="h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />` divider between hero and catalog toolbar
- All existing: `motion`/`AnimatePresence` imports, `FilterDrawer`, `PaddleComparator`, filter logic — fully preserved

### Task 2 — Statistics Page

**TabsList/TabsTrigger:**
- Upgraded `bg-muted/50` → `bg-muted border border-border` for crisper tab container
- Active trigger: `data-[state=active]:bg-background` → `data-[state=active]:bg-primary data-[state=active]:text-primary-foreground` — lime accent matches Stitch design
- Added `font-black text-sm rounded-lg` to all four triggers

**KPI Cards (4 cards in Overview grid):**
- Replaced `bg-card border border-border/50 rounded-3xl` → `glass-card border-none rounded-2xl` for consistent glassmorphism

**Section Headers:**
- All three `<h2>` section headers upgraded from `font-bold` → `font-black`

**Motion entrance:**
- Wrapped Overview TabsContent contents in `motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}`
- `motion` import was already present from existing stagger animations

**Unchanged:**
- All Recharts components, chart types, data, axes — untouched
- All data fetching, state management, deduplication logic — untouched
- All `TabsList`/`TabsTrigger` Radix structure — preserved

## Verification

- `grep "hover:shadow-glow" paddle-card.tsx` → 1 match
- `grep "glass-card" paddle-card.tsx` → 1 match
- `grep "glass-card" statistics-client.tsx` → 5 matches
- `grep "bg-\[#" statistics-client.tsx` → 0 matches (no hardcoded hex)
- E2E smoke test: `14 passed` (desktop project)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `frontend/components/paddle/paddle-card.tsx` — modified (hover:shadow-glow, price Badge)
- [x] `frontend/components/home-client.tsx` — modified (hero gradient, divider)
- [x] `frontend/components/statistics-client.tsx` — modified (tabs, cards, headers, motion)
- [x] Commit fd77728 — Task 1
- [x] Commit 0f052e1 — Task 2
- [x] 14/14 E2E tests pass

## Self-Check: PASSED
