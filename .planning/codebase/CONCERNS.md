# Codebase Concerns

**Analysis Date:** 2026-03-19

## Tech Debt

**Hardcoded Backend URL in Frontend:**
- Issue: Production Render backend URL is hardcoded as fallback in `frontend/lib/api.ts` (line 3: `https://sliceinsights-4rmf.onrender.com/api/v1`)
- Files: `frontend/lib/api.ts`
- Impact: Production URL baked into bundle; difficult to switch backends without rebuilding. Vercel deployment treats env vars differently at SSR time, forcing this workaround.
- Fix approach: Implement backend URL resolution at build time or use dynamic header rewrites in Vercel config; document the SSR env var limitation clearly.

**Synthetic Data Generation Without User Awareness:**
- Issue: When real specs are missing, paddle data is synthesized from string hashes (`frontend/lib/api.ts` lines 213-269). UI shows "ESTIMATED SPECS" badge for some paddles, but the synthetic generation logic is non-obvious.
- Files: `frontend/lib/api.ts` (mapBackendToFrontendPaddle function)
- Impact: Users may not realize data quality varies significantly; hidden calculation logic makes debugging difficult; calculations use string hashing which is deterministic but arbitrary.
- Fix approach: Clarify synthetic data rationale in comments; consider adding data quality score display; validate backend data requirements upstream.

**Unsafe Type Casting in Home Page:**
- Issue: Line 17 in `frontend/app/page.tsx` casts brand data with `any` type: `typeof b === 'string' ? b : b.name`
- Files: `frontend/app/page.tsx`
- Impact: Silent failures if brand shape changes; no type safety; makes refactoring risky.
- Fix approach: Define strict TypeScript interface for Brand; validate at API layer; add runtime type guards.

**Minimal ESLint Configuration:**
- Issue: `.eslintrc.json` only extends "next/core-web-vitals" with no custom rules
- Files: `frontend/.eslintrc.json`
- Impact: No enforcement of naming conventions, import order, or custom code patterns; console logs not caught; `any` types permitted.
- Fix approach: Add rules for no-console, no-explicit-any, import ordering; consider adopting stricter preset (next/recommended).

**Console Logging in Production:**
- Issue: Multiple `console.error()` and `console.log()` calls in API layer (`frontend/lib/api.ts` lines 115, 128, 132, 135, 157, 174, 178) logged at SSR time
- Files: `frontend/lib/api.ts`
- Impact: Verbose logs on every page load; no structured logging; unclear if errors should alert monitoring systems.
- Fix approach: Replace with structured logging service (e.g., Sentry, Pino); use conditional logging only in development; implement centralized error tracking.

**API Error Handling is Silent:**
- Issue: API calls throw generic errors ("Failed to fetch paddles") without context about retry strategy or user impact
- Files: `frontend/lib/api.ts` (lines 102, 129, 146, 171, 189, 195, 201, 207, 320)
- Impact: Frontend can't distinguish network timeout from 404 from 5xx; no retry logic; catch blocks in server components log but don't re-throw for proper error boundaries.
- Fix approach: Create custom error classes (NetworkError, NotFoundError, ServerError); implement retry with exponential backoff for transient failures; propagate to error boundaries.

**Timeout Durations Hardcoded:**
- Issue: 30-second timeout for paddle/brand fetches hardcoded in `frontend/lib/api.ts` (lines 119, 161)
- Files: `frontend/lib/api.ts`
- Impact: Not configurable per environment; may be too aggressive for cold starts on free tier Render.
- Fix approach: Move to config; environment-specific timeouts.

## Known Bugs

**JavaScript void Link in Coach Chat:**
- Symptoms: Coach chat interface contains `javascript:void(0)` link for paddles without affiliate URLs
- Files: `frontend/components/paddle/coach-chat-interface.tsx` (line 68)
- Trigger: When coach recommends a paddle that hasn't been assigned an affiliate link
- Workaround: onPaddleClick handler executes instead of navigation; prevents XSS but bad UX (non-functional link)
- Fix approach: Render as button or span instead of link; hide link element if no URL; provide fallback action.

**Weight Filter Logic Flawed:**
- Symptoms: Weight filter in home page assumes `paddle.weight` is numeric string, but it's always set to 'N/A'
- Files: `frontend/components/home-client.tsx` (lines 56-61)
- Trigger: Apply weight filter on home page
- Workaround: Filter silently returns no results for "light" or "heavy" selections
- Fix approach: Remove weight filter until weight data is populated; or store numeric weight field separately.

**Synthetic Data Prevents Accurate Filtering:**
- Symptoms: When specs are missing, deterministic synthetic values are generated; different paddles with similar names get same synthetic values
- Files: `frontend/lib/api.ts` (mapBackendToFrontendPaddle)
- Trigger: Browse paddles without real specs
- Workaround: Show "ESTIMATED SPECS" badge; users may not realize filtering is on fake data
- Fix approach: Add real data collection upstream; add clear "data incomplete" state to filters.

## Security Considerations

**Affiliate URL Handling in Chat:**
- Risk: User-provided text in chat output is parsed to find paddle names and convert to links; could allow injection if paddle names are user-controllable
- Files: `frontend/components/paddle/coach-chat-interface.tsx` (lines 37-80)
- Current mitigation: Paddle names come from backend; no user input in matching logic; affiliate URLs are from paddle object only
- Recommendations: Validate affiliate URLs are HTTPS before rendering; sanitize coach AI responses if model is adversarial; add CSP headers.

**API URL Fallback to External Service:**
- Risk: If env vars are missing, all API requests route to hardcoded Render URL; in compromised environment, this could leak data
- Files: `frontend/lib/api.ts` (lines 3, 24)
- Current mitigation: Hardcoded URL is legitimate backend; no secrets embedded
- Recommendations: Add validation that API base URL matches expected domain; implement request signing for authentication.

**SSR Data Exposure:**
- Risk: Initial page data fetched server-side and baked into HTML; if backend is compromised, data reaches browser in initial response
- Files: `frontend/app/page.tsx`, `frontend/app/statistics/page.tsx`
- Current mitigation: Data is public product info; no PII or secrets
- Recommendations: Monitor for unexpected API responses; validate response schema; implement rate limiting on API tier.

## Performance Bottlenecks

**Synchronous Promise.all() for Page Load:**
- Problem: Home page waits for both `getPaddles()` and `getBrands()` to complete before rendering (frontend/app/page.tsx line 11)
- Files: `frontend/app/page.tsx`
- Cause: Sequential dependency not enforced, but catch block hides failures; if one request hangs, entire page stalls
- Improvement path: Implement request.timeout with fallback values; render early with empty state; load brands from cache or secondary source.

**No Pagination or Virtualization:**
- Problem: Statistics page fetches up to 100 paddles; if list grows, renders all cards in DOM
- Files: `frontend/app/statistics/page.tsx` (line 19)
- Cause: No limit enforced; browser must render 100+ cards even if only 10 visible
- Improvement path: Implement virtual scrolling (react-window); paginate API response; lazy load chart data.

**Repeated String Hashing for Synthetic Data:**
- Problem: `stringHash()` function called for every paddle without memoization; O(n*m) where n=paddles, m=string length
- Files: `frontend/lib/api.ts` (lines 214-222)
- Cause: Called inside mapBackendToFrontendPaddle() which is called for every paddle on every page render
- Improvement path: Memoize hash results; move to backend; cache synthetic data.

**Image Loading Not Optimized:**
- Problem: PaddleCard uses Next.js Image with sizes prop but no priority or lazy loading hints
- Files: `frontend/components/paddle/paddle-card.tsx` (lines 35-41)
- Cause: Paddle cards are not above-the-fold on home page but images are eager-loaded
- Improvement path: Add lazy loading to off-screen cards; use smaller thumbnails for grid view.

## Fragile Areas

**Coach Chat Message Parsing:**
- Files: `frontend/components/paddle/coach-chat-interface.tsx` (lines 37-80)
- Why fragile: Regex-based splitting on markdown bold (`**text**`) and whitespace assumes exact formatting; AI model output may vary; paddle name matching is substring-based and could incorrectly link unrelated text
- Safe modification: Add unit tests for findPaddleByName with edge cases (e.g., "XYZ Paddle" vs "Paddle XYZ"); add end-to-end tests with recorded coach responses; consider fuzzy matching with min threshold
- Test coverage: No visible tests for message parsing logic

**API Response Mapping (mapBackendToFrontendPaddle):**
- Files: `frontend/lib/api.ts` (lines 212-301)
- Why fragile: Complex conditional logic for data quality detection (lines 230-231 check `swing_weight > 0` as proxy); synthetic data generation uses arbitrary offsets (1-6); multiple fallback chains make it unclear which values are real; if backend schema changes, detection breaks silently
- Safe modification: Add explicit "data_source" field from backend instead of inferring; write unit tests for each branch (real specs, real ratings, synthetic); validate all numeric fields before use; add debug mode to log which branch was taken
- Test coverage: No unit tests found

**Error Boundary Implementation:**
- Files: `frontend/components/ui/error-boundary.tsx`
- Why fragile: Only catches synchronous errors in render; doesn't catch async errors from useEffect or event handlers; componentDidCatch logs to console but doesn't report to monitoring service; error message exposed in dev mode could leak structure
- Safe modification: Wrap async operations with try-catch at component level; add error reporting service (Sentry); sanitize error messages for production; add test for error recovery
- Test coverage: Not visible in codebase

**TypeScript Config with skipLibCheck:**
- Files: `frontend/tsconfig.json` (line 10)
- Why fragile: skipLibCheck=true hides type errors in dependencies; `allowJs=true` allows untyped JS files; `strict=true` but paths are broad (`@/*` = any file)
- Safe modification: Remove skipLibCheck; gradually migrate JS to TS; use specific path aliases; run type-check in CI
- Test coverage: No CI validation visible

## Scaling Limits

**Static Revalidation Interval:**
- Current capacity: Home page cached for 1 hour (revalidate=3600)
- Limit: If 10 new paddles added per hour, users see stale data for 59 minutes
- Scaling path: Implement ISR (Incremental Static Regeneration) with on-demand revalidation; add Stripe webhook to invalidate on price changes; switch to client-side polling for real-time data.

**Backend URL Hardcoded to Single Service:**
- Current capacity: Render backend at https://sliceinsights-4rmf.onrender.com
- Limit: Single point of failure; if backend is down, entire app fails; cold starts on free tier cause timeouts
- Scaling path: Add load balancer; implement backend fallover; migrate to containerized solution with auto-scaling.

**No Caching Layer:**
- Current capacity: Every page request fetches from backend
- Limit: Backend load increases linearly with traffic; no burst handling
- Scaling path: Add Redis cache for paddles list; implement SWR with fallback values; use CDN for image proxying.

## Dependencies at Risk

**next-pwa (PWA Support):**
- Risk: Adds service worker that caches assets; if cache isn't invalidated properly, users see stale UI/data after updates
- Impact: Users stuck on old version; data inconsistencies if API schema changes
- Migration plan: Test service worker updates thoroughly; implement cache busting strategy; consider removing if PWA is not critical feature.

**recharts (Charts Library):**
- Risk: Large dependency; complex rendering of distribution/scatter charts; no performance monitoring for slow renders
- Impact: Statistics page may slow down as dataset grows (currently hardcoded 100 paddles)
- Migration plan: Benchmark chart performance; consider simpler chart library or server-side rendering; implement virtual scrolling.

**framer-motion (Animation Library):**
- Risk: Smooth animations add CPU load on low-end devices; no performance profiling
- Impact: Janky UX on mobile devices; battery drain
- Migration plan: Profile animations with DevTools; remove non-essential animations; use CSS animations for simple transitions.

## Missing Critical Features

**Error Reporting Service:**
- Problem: console.error() logs are not sent to monitoring system; errors silently fail in production
- Blocks: Can't diagnose why pages fail to load in production; no alerting for API outages

**Request Retry Logic:**
- Problem: Network timeouts and transient 5xx errors cause immediate page failures
- Blocks: Unreliable on slow networks or during backend cold starts

**Type Safety for Backend Data:**
- Problem: Brands are cast with `any` type; no validation that API responses match expected schema
- Blocks: Upgrading backend API is risky; can't refactor frontend with confidence

**Tests for Core Flows:**
- Problem: No test files found in codebase
- Blocks: Can't verify quiz recommendations work; can't test chat message parsing; can't catch regressions

## Test Coverage Gaps

**API Layer (lib/api.ts):**
- What's not tested: getPaddles, getBrands, getRecommendations, chatWithCoach, mapBackendToFrontendPaddle
- Files: `frontend/lib/api.ts`
- Risk: Synthetic data generation logic could break; type mapping could fail silently; API error handling not verified
- Priority: High - affects every page load

**Coach Chat Message Parsing:**
- What's not tested: findPaddleByName(), renderMessageWithLinks(), regex splitting, affiliate link generation
- Files: `frontend/components/paddle/coach-chat-interface.tsx`
- Risk: Paddle name matching could incorrectly link words; markdown parsing could fail on edge cases
- Priority: High - visible user-facing feature

**Quiz Recommendation Flow:**
- What's not tested: Quiz step progression, form submission, recommendation API call, recommendation result rendering
- Files: `frontend/components/paddle/racket-finder-quiz.tsx`
- Risk: Quiz could submit invalid data; API errors not handled; results could be empty
- Priority: Medium - critical user flow but graceful degradation

**Filter Logic:**
- What's not tested: Brand filter, price range, weight, thickness filters, filter clearing
- Files: `frontend/components/home-client.tsx`
- Risk: Filters could return no results; weight filter is broken; price range edge cases not validated
- Priority: Medium - core feature but not customer-facing API

**Error Boundary:**
- What's not tested: Error catching, fallback rendering, recovery mechanism, console error in dev mode
- Files: `frontend/components/ui/error-boundary.tsx`
- Risk: Errors could propagate unhandled; fallback not triggering; recovery not working
- Priority: Medium - affects user experience during failures

---

*Concerns audit: 2026-03-19*
