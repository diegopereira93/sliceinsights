---
phase: 17-ui-redesign
plan: "01"
subsystem: frontend
tags: [vite, react-19, tailwind-4, standalone-spa, ui-redesign]
dependency_graph:
  requires: []
  provides: [frontend-vite-directory]
  affects: [docker-compose, backend-cors]
tech_stack:
  added: [vite-7.3, react-19.1.0, tailwind-4.1.14, wouter-3.3, @tanstack-react-query-5.90, framer-motion-12.35, recharts-2.15, lucide-react-0.545, sonner-2.0, zod-3.25]
key_files:
  created:
    - frontend-vite/package.json
    - frontend-vite/vite.config.ts
    - frontend-vite/tsconfig.json
    - frontend-vite/index.html
    - frontend-vite/.env.local
    - frontend-vite/nginx.conf
    - frontend-vite/src/main.tsx
    - frontend-vite/src/App.tsx
    - frontend-vite/src/index.css
    - frontend-vite/src/lib/utils.ts
    - frontend-vite/src/lib/api-client/custom-fetch.ts
    - frontend-vite/src/lib/api-client/generated/api.ts
    - frontend-vite/src/lib/api-client/generated/api.schemas.ts
    - frontend-vite/src/lib/api-client/index.ts
    - frontend-vite/src/pages/Home.tsx
    - frontend-vite/src/pages/Quiz.tsx
    - frontend-vite/src/pages/Chat.tsx
    - frontend-vite/src/pages/Stats.tsx
    - frontend-vite/src/pages/not-found.tsx
    - frontend-vite/src/components/BottomNav.tsx
    - frontend-vite/src/components/PaddleCard.tsx
    - frontend-vite/src/components/BattleContext.tsx
    - frontend-vite/src/components/BattleOverlay.tsx
    - frontend-vite/src/components/ui/*.tsx (55 files)
    - frontend-vite/src/hooks/use-mobile.tsx
    - frontend-vite/src/hooks/use-toast.ts
    - frontend-vite/public/images/*.png (4 files)
decisions:
  - "Standalone package.json without pnpm workspace references"
  - "Removed @replit/vite-plugin-cartographer, @replit/vite-plugin-dev-banner, @replit/vite-plugin-runtime-error-modal"
  - "Route changes: /quiz -> /recommend, /stats -> /statistics per product requirements"
  - "Added aria-labels to BottomNav: Inicio, Recomendacao, Analise"
  - "API client inlined (not workspace dependency) with setBaseUrl bootstrap"
metrics:
  duration: ~6 minutes
  completed_date: "2026-03-24"
  files_created: 84
  requirements: [UI-01, UI-02, UI-04]
---

# Phase 17 Plan 1: Vite SPA Frontend Scaffold Summary

## Objective
Scaffold the Vite SPA frontend by copying redesign-slice source into a standalone `frontend-vite/` directory, creating a clean package.json, adapting vite.config.ts (remove Replit plugins), copying the API client library inline, updating route paths from /quiz to /recommend and /stats to /statistics, and configuring setBaseUrl to point to the FastAPI backend.

## What Was Built
A complete standalone Vite + React 19 + Tailwind 4 frontend with:
- All 4 pages (Home, Quiz/Recommend, Statistics, Chat)
- 55+ shadcn/ui components
- API client with setBaseUrl bootstrap
- Public images (paddle images, hero backgrounds)
- nginx.conf for production SPA serving

## Key Changes
1. **Created frontend-vite/ directory** with standalone project structure
2. **package.json**: Removed @workspace and @replit references, pinned exact versions
3. **vite.config.ts**: Uses react() and tailwindcss() plugins only (no Replit)
4. **Routes updated**: /quiz → /recommend, /stats → /statistics
5. **BottomNav updated**: Links + aria-labels per UI-SPEC
6. **API imports fixed**: All @workspace references changed to relative paths
7. **main.tsx**: Added setBaseUrl bootstrap from VITE_API_URL env var

## Acceptance Criteria - All Passed
- `frontend-vite/package.json` has no @workspace/ or @replit/ references
- `frontend-vite/vite.config.ts` contains react() and tailwindcss() plugins
- `frontend-vite/src/main.tsx` imports setBaseUrl from ./lib/api-client/custom-fetch
- `frontend-vite/src/App.tsx` has routes /recommend and /statistics
- `frontend-vite/src/components/BottomNav.tsx` has correct nav links
- No @workspace imports remain in frontend-vite/src/
- Public images exist with non-zero file sizes
- .env.local contains VITE_API_URL=http://localhost:8002
- npm run build exits with code 0
- dist/index.html exists after build

## Deviation: None
Plan executed exactly as written.

## Auth Gates: None
No authentication required for this task.

## Known Stubs: None
All required functionality is wired up.

---

## Self-Check: PASSED
- All acceptance criteria verified
- Build completes successfully
- Commit 4464f55 contains 84 files