# Testing Patterns

**Analysis Date:** 2026-04-05

## Test Framework

**Runner:**
- Frontend: Not detected. `frontend/package.json` contains only `dev`, `build`, and `start` scripts (no `test` script).
- Backend: Not detected. `backend/requirements.txt` does not include `pytest`/`unittest` tooling packages, and no `pytest.ini` or `pyproject.toml` was found under `backend/`.
- Config: No `jest.config.*`, `vitest.config.*`, or Python test config files were detected in project roots `frontend/` and `backend/`.

**Assertion Library:**
- Not detected.

**Run Commands:**
```bash
npm run dev           # Starts frontend dev server (`frontend/package.json`)
uvicorn server:app --reload --port 8000   # Runs backend API (`backend/server.py`)
python main.py        # Runs backend orchestration workflow (`backend/main.py`)
```

## Test File Organization

**Location:**
- No dedicated test directories (such as `tests/`, `__tests__/`) were detected in `frontend/` or `backend/`.
- No co-located `*.test.*` / `*.spec.*` files were detected in reviewed source paths:
  - `frontend/src/app/**`
  - `frontend/src/components/**`
  - `backend/src/agents/**`
  - `backend/src/environment/**`

**Naming:**
- Test naming pattern is not established in current codebase.

**Structure:**
```text
Not detected: no test file structure present in `frontend/` or `backend/`.
```

## Test Structure

**Suite Organization:**
```typescript
// Not detected in repository: no test suites or describe/it blocks found.
```

**Patterns:**
- Setup pattern: Not detected.
- Teardown pattern: Not detected.
- Assertion pattern: Not detected.

## Mocking

**Framework:** Not detected.

**Patterns:**
```typescript
// Not detected: no test-level mocks found.
```

**What to Mock:**
- No formal testing guidance encoded in codebase.
- Runtime fallback behavior exists in production hook code: `frontend/src/hooks/useApi.js` returns `null` from `apiFetch` on failures and derives UI behavior from nullable data.

**What NOT to Mock:**
- No explicit policy detected.

## Fixtures and Factories

**Test Data:**
```typescript
// Not detected: no fixtures/factories in test files.
```

**Location:**
- Not detected.

## Coverage

**Requirements:** None enforced (no coverage tooling/config detected).

**View Coverage:**
```bash
# Not available: no coverage command configured in `frontend/package.json`
# and no backend coverage tool configuration detected.
```

## Test Types

**Unit Tests:**
- Not used in repository (no unit test files detected).

**Integration Tests:**
- Not used as automated suites.
- Manual integration appears to be the current pattern:
  - Backend endpoint validation through in-process route calls in `backend/main.py` (`validate_routes()`).
  - Frontend integration validated by running against backend endpoints via hooks in `frontend/src/hooks/useApi.js`.

**E2E Tests:**
- Not used (no Playwright/Cypress setup detected).

## Common Patterns

**Async Testing:**
```typescript
// Not detected as test code.
// Async runtime behavior exists in app code:
// - streaming reader loop in `frontend/src/hooks/useApi.js` (`runSimulation`)
// - `StreamingResponse` in `backend/routes.py` (`/api/run-simulation`)
```

**Error Testing:**
```typescript
// Not detected as test code.
// Error handling is implemented in runtime code (e.g., fail-soft `apiFetch` in `frontend/src/hooks/useApi.js`)
// but not validated by automated tests.
```

## Notable Gaps

- No automated test runner is configured in `frontend/package.json` or backend config files.
- No regression coverage exists for market-clearing and dispatch logic in `backend/src/agents/routing_agent/routing_agent.py`.
- No automated validation exists for state-position math and bidding behavior in `backend/src/agents/state_agent/state_agent.py`.
- No API contract tests exist for route handlers in `backend/routes.py` (`/api/intelligence`, `/api/grid-status`, `/api/run-simulation`, `/api/simulation-result`).
- No component tests exist for critical UI modules in `frontend/src/components/grid/SimTerminal.js` and `frontend/src/components/grid/DispatchTable.js`.

---

*Testing analysis: 2026-04-05*
