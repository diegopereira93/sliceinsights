# Coding Conventions

**Analysis Date:** 2026-03-19

## Naming Patterns

**Files:**
- Frontend components: PascalCase with `.tsx` extension (e.g., `home-client.tsx`, `paddle-card.tsx`)
- Utility files: camelCase (e.g., `api.ts`, `utils.ts`, `import-utils.ts`)
- Python modules: snake_case (e.g., `recommendation_engine.py`, `affiliate_service.py`)
- Test files: descriptive names ending in `.spec.ts` (e.g., `sliceinsights.spec.ts`)

**Functions:**
- TypeScript/JavaScript: camelCase (e.g., `getApiBaseUrl`, `mapBackendToFrontendPaddle`, `handleToggleBrand`)
- Python: snake_case (e.g., `get_recommendations`, `calculate_paddle_ratings`, `assemble_async_db_url`)
- React hooks: camelCase with `use` prefix (e.g., `useState`, `useMemo`, `useEffect`)
- Async functions: clearly marked as async (e.g., `async def health_check()`)

**Variables:**
- React state: camelCase (e.g., `selectedPaddle`, `priceRange`, `isComparatorOpen`)
- Type annotations: always used in TypeScript
- Constants: UPPER_SNAKE_CASE in Python (e.g., `API_BASE_URL`, `RENDER_BACKEND_URL`)
- Private/internal: no special prefix, rely on module scope

**Types:**
- TypeScript interfaces: PascalCase with leading capital (e.g., `HomeClientProps`, `BackendPaddle`, `RecommendationRequest`)
- Pydantic models: PascalCase (e.g., `Settings`, `UserProfile`, `RecommendationResult`)
- Enum-like values: PascalCase (e.g., `PlayStyle`, `MarketOffer`)

## Code Style

**Formatting:**
- Frontend: Follows `next/core-web-vitals` ESLint config
- No explicit `.prettierrc` found—use ESLint defaults
- Indentation: 4 spaces in Python, 2 spaces in TypeScript (evident from code)
- Line length: No hard limit observed, but generally kept under 120 characters

**Linting:**
- Frontend: ESLint v8.57.0 with `eslint-config-next`
- Config: `frontend/.eslintrc.json` extends `next/core-web-vitals`
- Python: No explicit linter config found; follows PEP 8 style
- Type checking: TypeScript strict mode enabled (`strict: true` in `tsconfig.json`)

**Imports:**
- TypeScript: Use path aliases (`@/*` maps to project root in `frontend/`)
- Python: Relative imports within app, absolute imports for external libraries
- Group imports in TypeScript: external libraries first, then local modules

**Import Organization:**
1. External libraries (React, FastAPI, third-party packages)
2. Internal app modules (models, services, schemas, components)
3. Type/interface imports
4. Relative local imports (utils, types)

**Path Aliases:**
- Frontend: `@/*` resolves to `frontend/` root—used consistently (e.g., `@/components/ui/button`, `@/types/paddle`, `@/lib/api`)

## Error Handling

**Patterns:**
- TypeScript/React: Try-catch with `throw new Error()` for HTTP failures
  - Example: `if (!response.ok) throw new Error('Failed to fetch paddles')`
- Python: Use FastAPI's `HTTPException` for API errors
  - Example: `raise HTTPException(status_code=400, detail="Invalid profile")`
- Async operations: AbortController with timeouts (30s for cold starts in SSR)
- Graceful degradation: Health checks return 503 if database unavailable, not total failure

## Logging

**Framework:**
- Frontend: `console.log` and `console.error` with prefixes (e.g., `[SSR]`, `[API]`)
- Python: `structlog` for structured JSON logging in production

**Patterns:**
- Structured logging: Use context binding (e.g., `logger.bind(method=..., path=..., status_code=...)`)
- Log levels: DEBUG, INFO, WARNING, ERROR (configured via `log_level` setting)
- Include relevant context: request paths, status codes, timing, error messages
- Development vs. production: ConsoleRenderer in dev, JSONRenderer in production

## Comments

**When to Comment:**
- Above docstrings for non-obvious async behavior (e.g., SSR backend URL logic)
- Clarify workarounds or browser-specific quirks (e.g., "window is undefined on server")
- Document integration-specific details (e.g., "asyncpg driver required for async operations")
- Flag temporary solutions or hacks with `// TODO:` or inline notes

**JSDoc/TSDoc:**
- Python docstrings: Triple quotes with description at module/function level
  - Example: `"""FastAPI main application entry point."""`
- TypeScript: No explicit JSDoc observed; rely on TypeScript types for documentation
- API route docs: FastAPI's auto-generated OpenAPI (Swagger) via description parameters

## Function Design

**Size:**
- Generally compact (50–100 lines typical for complex logic)
- Recommendation engine method: ~60 lines with clear step comments (1–5. numbered sections)
- React component render: substantial but broken into logical sections with comments

**Parameters:**
- Explicit typing required (TypeScript interfaces, Pydantic models)
- Default values common in Python settings/config
- Use kwargs or object destructuring for multiple optional parameters
- React props: always define interface (e.g., `HomeClientProps`)

**Return Values:**
- Async functions always return promises/awaitable objects
- HTTP endpoints return JSON-serializable objects or HTTPException
- Utility functions return typed values (no implicit any)

**Async/Await:**
- Consistently used in FastAPI routes and async database queries
- Client-side: used for fetch calls with proper error handling
- Database: `AsyncSession` with sqlmodel for all async ORM operations

## Module Design

**Exports:**
- Python: `from app.services import RecommendationEngine` (class imports)
- TypeScript: Named exports for utilities and interfaces, default exports for components
  - Example: `export default function HomeClient()` for React components
  - Example: `export function cn()` for utilities

**Barrel Files:**
- Frontend uses index.ts files in component directories (e.g., `components/import-calculator/index.ts`)
- Pattern: `export { ImportCalculator } from './import-calculator'` style re-exports

**Module Organization:**
- Backend: Layers by concern (models/, services/, schemas/, api/endpoints/)
- Frontend: By feature or component type (components/, lib/, types/)
- Services: Encapsulate business logic (RecommendationEngine, LLMService, AffiliateService)

## TypeScript Configuration

**Compiler Options:**
- Target: ES2017
- Strict mode: enabled
- `resolveJsonModule`: true (allows JSON imports)
- `isolatedModules`: true (each file independently compilable)
- JSX: preserve (handled by Next.js)
- Module resolution: bundler (Next.js)

**Strict Checks:**
- No implicit any
- Null/undefined checks enforced
- Strict property initialization

## Python Configuration

**Base Settings Class:**
- Pydantic `BaseSettings` with env file loading (`.env`)
- Field validators for transformation (e.g., `assemble_async_db_url`, `parse_allowed_origins`)
- Properties for computed values (e.g., `sync_database_url`)
- Default values provided for all fields

---

*Convention analysis: 2026-03-19*
