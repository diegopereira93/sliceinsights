# Plan: Resolve E2E Test Failures (404 Not Found)

The E2E tests are currently failing because the `BASE_URL` in the GitHub Actions workflow points to a 404 page (`https://frontend-five-iota-18.vercel.app`). The correct production URL is `https://sliceinsights.vercel.app`.

## Proposed Changes

### CI/CD Pipeline

#### [MODIFY] [production-pipeline.yml](file:///home/diego/Documentos/projetos/data-products/sliceinsights/.github/workflows/production-pipeline.yml)
- Update `BASE_URL` in the `verify-deployment` job from `https://frontend-five-iota-18.vercel.app` to `https://sliceinsights.vercel.app`.
- Ensure the deployment step correctly targets the production environment.

### Frontend Configuration

#### [MODIFY] [vercel.json](file:///home/diego/Documentos/projetos/data-products/sliceinsights/frontend/vercel.json)
- Double-check environment variables to ensure they point to the correct backend. (Currently pointing to `https://sliceinsights.onrender.com`).

## Verification Plan

### Automated Tests
- Run Playwright E2E tests locally against the production URL to verify they pass.
  ```bash
  cd frontend
  BASE_URL=https://sliceinsights.vercel.app npx playwright test e2e/verification.spec.ts
  ```
- Trigger the GitHub Action (if possible) or wait for the next push to main to verify the pipeline passes.

### Manual Verification
- Access `https://sliceinsights.vercel.app` in the browser and verify the title and main content are correct.
