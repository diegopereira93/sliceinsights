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
