# Coding Conventions

**Analysis Date:** 2026-04-05

## Naming Patterns

**Files:**
- Frontend feature files use `PascalCase.js` for React components in `frontend/src/components/**` (examples: `frontend/src/components/ui/NavBar.js`, `frontend/src/components/grid/DispatchTable.js`).
- Frontend route files use Next.js App Router conventions with lowercase `page.js` and `layout.js` in `frontend/src/app/**` (examples: `frontend/src/app/page.js`, `frontend/src/app/simulation/page.js`, `frontend/src/app/layout.js`).
- Frontend hooks use `camelCase` prefixed with `use` in `frontend/src/hooks` (example: `frontend/src/hooks/useApi.js`).
- Backend modules use `snake_case.py` consistently in `backend/src/**` (examples: `backend/src/agents/state_agent/state_agent.py`, `backend/src/agents/intelligence_agent/signal_extractor_agent.py`).

**Functions:**
- Frontend React components and exported UI blocks use `PascalCase` function names (examples: `HomePage` in `frontend/src/app/page.js`, `SimulationPage` in `frontend/src/app/simulation/page.js`, `DispatchTable` in `frontend/src/components/grid/DispatchTable.js`).
- Frontend helper/utility functions use `camelCase` (examples: `buildForecastData` in `frontend/src/app/page.js`, `normalizeDispatches` in `frontend/src/components/grid/DispatchTable.js`).
- Backend functions and methods use `snake_case` (examples: `generate_intelligence` in `backend/main.py`, `run_simulation` in `backend/run_simulation.py`, `verify_route_safety_with_llm` in `backend/src/agents/routing_agent/llm_safety_stub.py`).

**Variables:**
- Frontend constants are uppercase snake case when module-level constants are intended to be static (examples: `API_BASE` in `frontend/src/hooks/useApi.js`, `NAV_ITEMS` in `frontend/src/components/ui/NavBar.js`, `AGENT_COLORS` in `frontend/src/components/grid/SimTerminal.js`).
- Backend constants use uppercase snake case in shared constants/config files (examples: `BASELINE_BID_PRICE` in `backend/src/agents/shared/constants.py`, `CITY_REGISTRY` in `backend/src/agents/intelligence_agent/setup.py`).
- Local runtime values use `camelCase` in frontend and `snake_case` in backend.

**Types:**
- Backend typing is explicit and systematic with `dataclass` models and annotated return types in agent/domain code (examples: `Order`, `DispatchRecord`, `StatePosition` in `backend/src/agents/shared/models.py`; typed signatures in `backend/src/agents/routing_agent/routing_agent.py` and `backend/routes.py`).
- Frontend is JavaScript-only and relies on runtime guards and value coercion instead of static type declarations (examples: `Number(...)` conversion in `frontend/src/app/page.js` and `frontend/src/components/grid/DispatchTable.js`).

## Code Style

**Formatting:**
- Frontend style follows default Next.js + ESLint formatting with semicolon-free JavaScript and single quotes across files (examples throughout `frontend/src/app/page.js`, `frontend/src/components/ui/Primitives.js`).
- Backend style follows PEP 8-like formatting with docstrings and type annotations (examples: module docstrings and typed functions in `backend/run_simulation.py`, `backend/src/agents/intelligence_agent/orchestrator.py`).
- No Prettier config was detected in `frontend/` and no dedicated formatter config was detected in `backend/`.

**Linting:**
- Frontend linting is configured through Next.js ESLint preset via `frontend/package.json` dependency `eslint-config-next`; no custom `.eslintrc*` or `eslint.config.*` file detected.
- Backend lint config (e.g., `ruff`, `flake8`, `pylint`) was not detected.

## Import Organization

**Order:**
1. Framework/library imports first (examples: React/Next imports in `frontend/src/app/page.js`; stdlib imports in `backend/routes.py`).
2. Internal alias/local imports second (examples: `@/components/...` in `frontend/src/app/page.js`; `from src...` imports in `backend/routes.py`).
3. Constants/config bindings and local helper declarations after imports.

**Path Aliases:**
- Frontend uses `@/*` alias configured in `frontend/jsconfig.json`, mapped to `frontend/src/*`.
- Backend uses project-root style `src...` imports, enabled by path insertion in entry modules (examples: `sys.path.insert(0, str(BACKEND_DIR))` in `backend/routes.py`, `sys.path.insert(0, ".")` in `backend/run_simulation.py`).

## Error Handling

**Patterns:**
- Frontend API hooks favor fail-soft behavior and return nullable data instead of throwing (example: `apiFetch` returns `null` in `frontend/src/hooks/useApi.js`).
- Frontend simulation streaming logic uses broad `try/catch` with suppressed error detail (`catch {}`) and then attempts fallback fetch in `frontend/src/hooks/useApi.js`.
- Backend APIs convert failures to HTTP responses with `HTTPException` for route-level failures (example: `_generate_intelligence` in `backend/routes.py`).
- Backend internal loaders use tolerant `try/except` blocks that skip bad cache files and continue (example: `_load_node_cache` in `backend/routes.py`).

## Logging

**Framework:** Python `logging` in backend and browser-rendered status logs in frontend UI.

**Patterns:**
- Backend runtime logging uses module loggers (`logging.getLogger(__name__)`) and structured phase-like message strings (examples: `backend/run_simulation.py`, `backend/src/agents/routing_agent/dispatcher.py`).
- Backend startup/orchestration scripts also use `print(...)` for pipeline visibility and summary output (examples: `backend/main.py`, `backend/src/agents/intelligence_agent/orchestrator.py`).
- Frontend does not use `console.*` for primary observability in core pages; logs are rendered in UI components from API stream data (examples: `frontend/src/components/grid/SimTerminal.js`, `frontend/src/components/agents/AgentChat.js`).

## Comments

**When to Comment:**
- Backend uses extensive module and phase comments to explain simulation phases and design intent (examples: `backend/run_simulation.py`, `backend/src/agents/intelligence_agent/orchestrator.py`).
- Frontend uses targeted inline comments for UI sections and interaction blocks (examples: `frontend/src/components/grid/DispatchTable.js`, `frontend/src/components/agents/AgentChat.js`).

**JSDoc/TSDoc:**
- JSDoc/TSDoc is not used in frontend source files.
- Python docstrings are standard in backend modules, classes, and functions (examples: `backend/src/agents/shared/models.py`, `backend/src/environment/grid_physics.py`).

## Function Design

**Size:**  
- Use large page/container components for orchestration and composition in frontend pages (`frontend/src/app/page.js`, `frontend/src/app/simulation/page.js`) and keep reusable display widgets in `frontend/src/components/**`.
- Backend orchestration functions are long and phase-oriented, while core domain logic is split into agent modules (`backend/run_simulation.py` orchestrates; `backend/src/agents/state_agent/state_agent.py` and `backend/src/agents/routing_agent/routing_agent.py` encapsulate logic).

**Parameters:**  
- Frontend components accept object props with defaults where useful (examples: `ForecastChart({ forecastData = [] })`, `Card({ children, className = '', glow = false })`).
- Backend functions favor explicit typed parameters and structured dict payloads for context/state passing (examples: `clear_market(..., state_positions: dict[str, Any] | None = None)` in `backend/src/agents/routing_agent/routing_agent.py`).

**Return Values:**  
- Frontend hooks return shape-stable objects `{ data, loading }` or `{ logs, results, running, done, runSimulation }` (`frontend/src/hooks/useApi.js`).
- Backend route handlers return JSON-serializable dict/list payloads; agent logic returns dataclasses or typed dicts (examples: `backend/routes.py`, `backend/src/agents/shared/models.py`).

## Module Design

**Exports:**  
- Frontend modules use named exports for reusable UI modules/hooks and default exports for page-level route modules (examples: named export `NavBar` in `frontend/src/components/ui/NavBar.js`, default export in `frontend/src/app/intelligence/page.js`).
- Backend modules expose classes/functions directly by import path; `__init__.py` marker files exist across package directories under `backend/src/agents/**`.

**Barrel Files:**  
- Barrel re-export files were not detected in frontend component directories.
- Backend package init files exist but are not used as broad aggregation barrels.

---

*Convention analysis: 2026-04-05*
