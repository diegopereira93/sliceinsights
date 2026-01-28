# Plan: Complete Project Testing & Documentation Update

**Goal**: Execute a comprehensive testing suite (Unit, Lint, Security, E2E) and update project documentation to reflect the current state and maintain reliability.

## User Review Required
> [!IMPORTANT]
> - The script `scripts/test_recommendation_logic.py` is currently failing due to a `KeyError: 'ratings'`. I plan to have the `backend-specialist` fix this as part of the implementation.
> - I will use the internal security scanner at `.agent/skills/vulnerability-scanner/scripts/security_scan.py` instead of the command-line `safety` tool if the latter is unavailable.

## Proposed Changes

### Phase 1: Planning (Current)
- Created this plan to coordinate agents.

### Phase 2: Implementation (After Approval)

#### [TESTING] Execution (Agent: `test-engineer`)
- **Pytest**: Run all tests in `tests/` and ensure 100% pass rate.
- **Linting**: Run `ruff check .` to ensure code quality.
- **Security**: Run the vulnerability scanner script.
- **E2E (Local)**: Execute `scripts/test_e2e_loop.py` to verify local service connectivity.
- **Production Verification**: Execute `scripts/autonomous_health_check.py` to verify the live environment (Render and Vercel).

#### [CORE] Fixes (Agent: `backend-specialist`)
- **Fix Test Script**: Update `scripts/test_recommendation_logic.py` to match the current data structure (fixing 'ratings' KeyError).
- **Logic Validation**: Ensure the recommendation engine logic is verified by the fixed script.

#### [DOCS] Documentation Update (Agent: `documentation-writer`)
- **README.md**: Update with the latest test status and verification instructions.
- **API Spec**: Verify `docs/technical/api_specification.md` matches the current FastAPI implementation.
- **Orchestration Report**: Generate a final `docs/ORCHESTRATION_REPORT.md` summarizing all test results.

### Phase 3: CI/CD Revision (Agent: `devops-engineer`)
- **Audit Workflows**: Review `.github/workflows/production-pipeline.yml` and `ralph-loop.yml` for health and security.
- **Secret Validation**: Verify if the `RENDER_DEPLOY_HOOK` and `ADMIN_SEED_SECRET` are correctly configured in GitHub (based on logs/responses).
- **Quality Gate Update**: Propose adding the security scan (safety/security_scan.py) as a mandatory step in the production pipeline if feasible.
- **Service Verification**: Ensure Playwright E2E tests in the pipeline are hitting the correct production endpoints.

## Verification Plan

### Automated Tests
- `make test` (pytest)
- `make lint` (ruff)
- `make security` (security_scan.py)
- `PYTHONPATH=. .venv/bin/python scripts/test_recommendation_logic.py`
- **Production Health Check**: `BACKEND_URL=https://sliceinsights.onrender.com/api/v1 FRONTEND_URL=https://frontend-five-iota-18.vercel.app python3 scripts/autonomous_health_check.py`

### Manual Verification
- Review the updated documentation for accuracy.
- Verify the final Orchestration Report covers all executed agents.
