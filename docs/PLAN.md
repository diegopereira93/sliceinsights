# Production Readiness Implementation Plan

**Goal**: Remediate critical security findings and stabilize the development environment to meet production standards.

## User Review Required
> [!IMPORTANT]
> The security scan identified "Critical" SQL injections. Manual review confirms:
> 1. `scripts/update_paddle_specs.py`: Uses dynamic SQL construction with bound parameters (Safe-ish but flagged). **Proposal**: Refactor to full ORM usage.
> 2. `scripts/ingest_paddles.py`: Uses f-strings in `page.evaluate`. **Proposal**: Use Argument binding for Playwright.

## Proposed Changes

### 1. Security Remediation (Scripts)
#### [MODIFY] [scripts/update_paddle_specs.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/scripts/update_paddle_specs.py)
- **Current**: Raw SQL strings constructed via f-strings.
- **New**: Load `PaddleMaster` object via SQLModel, update attributes pythonically, `session.commit()`.
- **Benefit**: Removes `text()` usage, 100% safe, type-checked.

#### [MODIFY] [scripts/ingest_paddles.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/scripts/ingest_paddles.py)
- **Current**: `page.evaluate(f"document... {var}")`
- **New**: `page.evaluate("([var]) => document...", [var])`
- **Benefit**: Prevents any theoretical JS injection.

### 2. Environment & CI Stabilization
#### [MODIFY] [requirements.txt](file:///home/diego/Documentos/projetos/data-products/sliceinsights/requirements.txt)
- Pin specific versions for `ruff` and `pytest`.
- Ensure compatibility with current python version.

#### [NEW] [Makefile](file:///home/diego/Documentos/projetos/data-products/sliceinsights/Makefile)
- Standardize commands:
    - `make lint`: runs ruff
    - `make test`: runs pytest
    - `make security`: runs security_scan.py

## Verification Plan

### Automated Tests
1. **Security Scan**:
   ```bash
   python3 .agent/skills/vulnerability-scanner/scripts/security_scan.py .
   ```
   *Success Criteria*: 0 Critical issues in scripts.

2. **Linting**:
   ```bash
   ruff check .
   ```
   *Success Criteria*: Clean execution (or at least runnable).

3. **Unit Tests**:
   ```bash
   pytest
   ```
   *Success Criteria*: Tests collection works (even if some fail, the *runner* must work).

### Manual Verification
- Execute `python3 scripts/update_paddle_specs.py` (dry-run mode if possible or against dev db) to ensure logic remains correct.

---

## Phase 2: Data Integrity & Logic Validation (Orchestration)

**Objective**: Ensure the "Nature of Data" (Physics -> Ratings) is mathematically correct and robust.

### 1. Domain Logic Validation (Agent: `test-engineer`)
#### [NEW] [tests/test_domain_logic.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/tests/test_domain_logic.py)
- **Goal**: Verify `calculate_paddle_ratings` against edge cases.
- **Scenarios**:
    - Twist Weight < 100 (Small scale conversion).
    - Twist Weight > 150 (Large scale conversion).
    - Missing Spin RPM (Defaults).
    - Boundary checks (0-10 limits).

### 2. Script Refactoring (Agent: `backend-specialist`)
#### [MODIFY] [scripts/update_paddle_specs.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/scripts/update_paddle_specs.py)
- **Goal**: Migrate from Raw f-string SQL to SQLModel ORM.
- **Why**: Security (prevent injection) + Data Consistency (use model validation).

### 3. Database Constraints (Agent: `database-architect`)
#### [MODIFY] [app/models/paddle.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/app/models/paddle.py)
- **Goal**: Add validators/constraints to `PaddleMaster`.
- **Changes**:
    - `validator("power_rating")`: ensure 0-10.
    - `validator("twist_weight")`: warn on suspicious values.

### 4. Production Data Verification (Agent: `qa-automation-engineer` & `devops-engineer`)
#### [NEW] [frontend/e2e/data-integrity.spec.ts](file:///home/diego/Documentos/projetos/data-products/sliceinsights/frontend/e2e/data-integrity.spec.ts)
- **Goal**: Validate that data ingested in Backend actually appears in Frontend Catalog.
- **Action**: Create an E2E test that:
    1. Visits the Catalog page.
    2. Searches for a specific "Golden Record" (e.g., "Ben Johns Perseus").
    3. Verifies that the displayed specs (Power, Control) match the database values.
---

## Phase 3: Public Presence & Polish (Orchestration)

**Objective**: Maximize visibility and ensure a premium user experience for the Open Beta launch.

### 1. SEO & OpenGraph Optimization (Agent: `seo-specialist`)
#### [MODIFY] [frontend/app/layout.tsx](file:///home/diego/Documentos/projetos/data-products/sliceinsights/frontend/app/layout.tsx)
- **Goal**: Implement high-fidelity meta tags and social share images.
- **Changes**:
    - Add `metadata` object with descriptive title and summary.
    - Configure `openGraph` and `twitter` cards.
    - Ensure `robots.txt` allows indexing.

### 2. Performance & VBR (Agent: `performance-optimizer`)
#### [MODIFY] [frontend/next.config.mjs](file:///home/diego/Documentos/projetos/data-products/sliceinsights/frontend/next.config.mjs)
- **Goal**: Achieve Lighthouse Score > 80.
- **Action**: 
    - Enable image optimization and compression if not already present.
    - Identify and remove blocking scripts or heavy dependencies.
    - Verify with `npx lighthouse`.

### 3. E2E Stabilization (Agent: `test-engineer`)
#### [MODIFY] [frontend/e2e/verification.spec.ts](file:///home/diego/Documentos/projetos/data-products/sliceinsights/frontend/e2e/verification.spec.ts)
- **Goal**: Fix the 7th failing test case.
- **Action**: 
    - Analyze Playwright traces to identify the cause of failure.
    - Fix selectors or hydration issues.
    - Ensure 100% pass rate in the CI/CD pipeline.

---

## Phase 4: Scaling & Deployment Protocol (Orchestration)

**Objective**: Transition to a more robust branching strategy and trigger the production deployment.

### 1. New Branching Protocol (Agent: `project-planner`)
- **Policy**: All new features or adjustments MUST start with a branch off `main`.
- **Action**: 
    - Create a branch `feat/unified-protocol-and-deploy`.
    - Update [AUTONOMOUS_DEV.md](file:///home/diego/Documentos/projetos/data-products/sliceinsights/AUTONOMOUS_DEV.md) under "The Autonomous Cycle".
    - Update [README.md](file:///home/diego/Documentos/projetos/data-products/sliceinsights/README.md) development section.

### 2. Final Documentation Sweep (Agent: `documentation-writer`)
- **Goal**: Ensure all guidelines are clear for external agent contributors.
- **Action**: Add a "Git Workflow" section to the docs explicitly stating: `main` is protected; branch first.

### 3. Production Deployment (Agent: `devops-engineer`)
- **Goal**: Push certified changes to production and trigger Vercel/Render pipelines.
- **Action**: 
    - Checkout `main`, merge the feature branch after local verification.
    - Push to origin `main`.
    - Monitor GitHub Actions: [production-pipeline.yml](file:///home/diego/.github/workflows/production-pipeline.yml).

---

---

## Phase 6: GitHub Actions & CI Verification (Orchestration)

**Objective**: Ensure all CI/CD workflows are healthy after dependency fixes and structure changes.

### 1. Backend CI Local Simulation (Agent: `devops-engineer`)
- **Goal**: Verify that the "Backend Test" workflow steps run successfully locally.
- **Action**: 
    - Run dependency installation within Docker.
    - Run full test suite with SQLite (`python -m pytest tests/`).
    - Verify `safety` and `ruff` checks.

### 2. Frontend CI Local Simulation (Agent: `test-engineer`)
- **Goal**: Verify that the "Frontend Build Check" runs successfully locally.
- **Action**:
    - Run `npm run build` in the `frontend` directory.
    - Run smoke tests if applicable.

### 3. Pipeline Monitoring (Agent: `devops-engineer`)
- **Goal**: Monitor the real GitHub Actions run after push.
- **Action**:
    - Once changes are pushed, track the "Production Pipeline" progress.
    - Document any failure and remediate.

## Orchestration Summary
| Phase | Agents | Goal |
|-------|--------|------|
| **Phase 5** | `documentation-writer` | Mandatory Documentation Sync |
| **Phase 6** | `project-planner`, `devops-engineer`, `test-engineer` | GitHub Actions & CI Verification |
| **Phase 7** | `devops-engineer`, `backend-specialist`, `orchestrator` | Production Deployment & Health Sync |

---

## Phase 7: Production Deployment & Health Sync (Orchestration)

**Objective**: Force the deployment of the verified `main` branch to Render and verify full stack health.

### 1. Deployment Troubleshooting (`devops-engineer`)
- **Observation**: Commit `b201257` is live on GitHub/Vercel but Render is stuck on `bf06449`.
- **Root Cause**: `RENDER_DEPLOY_HOOK` secret is missing in GitHub repository settings.
- **Action**: 
    - Verify if Render auto-deploy can be re-triggered or if a manual webhook is necessary.
    - If auto-deploy is disabled, I will prepare the exact instructions for the user to add the secret.

### 2. Backend Health & Connectivity (`backend-specialist`)
- **Goal**: Ensure the backend isn't just "up" but actually serving data.
- **Problem**: Frontend current returns "Nenhuma raquete encontrada", suggesting DB or API issues.
- **Action**:
    - Check `/health` and `/api/v1/paddles` endpoints via browser or terminal.
    - Verify logs for any "migrations pending" or "connection refused" errors.

### 3. Orchestration Audit (`orchestrator`)
- **Goal**: Final sign-off on the 3+ agent requirement and verification scripts.
- **Action**:
    - Synthesize results from all 3 agents into a final report.
    - Run `security_scan.py` one last time on the `main` branch state.
---

## Phase 8: Ralph-Loop implementation for Database Consistency (Orchestration)

**Objective**: Ensure the database is NEVER empty in the UI by implementing the Ralph-Loop (RARV) cycle autonomously.

### 1. Data Hydration Sweep (`database-architect`)
- **Goal**: Verify production DB hydration.
- **Action**: Check `PaddleMaster` table and sync with `paddles.json` if count < 10.

### 2. Frontend Cache Purge & Propagation (`devops-engineer`)
- **Goal**: Ensure Vercel is not serving stale build.
- **Action**: Use Vercel CLI or manual deployment trigger to force a clean build.

### 3. Verification & Self-Healing (`test-engineer` & `orchestrator`)
- **Goal**: Continuous health monitoring.
- **Action**: Implement a periodic ping/check in GitHub Actions to keep Render awake.
