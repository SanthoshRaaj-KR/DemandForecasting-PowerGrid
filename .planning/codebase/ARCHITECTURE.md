# Architecture

**Analysis Date:** 2026-04-05

## Pattern Overview

**Overall:** Polyglot, two-tier application with a script-driven backend pipeline and a route-driven frontend UI.

**Key Characteristics:**
- Use a backend orchestration workflow that is explicit and phase-based in `backend/main.py`, `backend/run_simulation.py`, and `backend/src/agents/intelligence_agent/orchestrator.py`.
- Use HTTP API boundaries for frontend/backend communication through `backend/routes.py` and `frontend/src/hooks/useApi.js`.
- Use file-backed state handoff (JSON cache/results) across backend subsystems via `backend/outputs/context_cache/*.json`, `backend/outputs/grid_intelligence_*.json`, and `backend/outputs/simulation_result_*.json`.

## Layers

**Frontend Presentation Layer:**
- Purpose: Render dashboards for grid status, intelligence cards, and simulation war-room controls.
- Location: `frontend/src/app/`, `frontend/src/components/`
- Contains: Next.js App Router pages (`page.js`), visual components (`GridMap.js`, `DispatchTable.js`, `RegionCard.js`), UI primitives (`frontend/src/components/ui/Primitives.js`).
- Depends on: React hooks and API hooks from `frontend/src/hooks/useApi.js`, constants from `frontend/src/lib/gridMeta.js`.
- Used by: Browser clients hitting routes from `frontend/src/app/layout.js`, `frontend/src/app/page.js`, `frontend/src/app/intelligence/page.js`, `frontend/src/app/simulation/page.js`.

**API Layer (Backend Web Surface):**
- Purpose: Expose health, intelligence, grid-state, simulation stream, and latest result endpoints.
- Location: `backend/routes.py` (mounted by `backend/server.py`).
- Contains: FastAPI app definition, CORS middleware setup, endpoint handlers (`/api/intelligence`, `/api/grid-status`, `/api/run-simulation`, etc.), lightweight fallback builders.
- Depends on: `backend/src/environment/grid_physics.py`, `backend/src/agents/intelligence_agent/orchestrator.py`, local result/cache files under `backend/outputs/`.
- Used by: Frontend hooks in `frontend/src/hooks/useApi.js` and manual server startup through `uvicorn server:app`.

**Simulation Core Layer:**
- Purpose: Execute phase-driven multi-agent market clearing and power-flow/battery updates.
- Location: `backend/run_simulation.py`, `backend/src/environment/grid_physics.py`, `backend/src/agents/state_agent/`, `backend/src/agents/routing_agent/`.
- Contains: Grid model abstractions (`GridEnvironment`, `TransmissionEdge`, `TransmissionPath`, `BatteryCell`), state-position logic (`StateAgent`), route and dispatch logic (`RoutingAgent`), settlement and explainability integration.
- Depends on: Shared models in `backend/src/agents/shared/models.py`, optional ML forecast loader in `backend/src/agents/fusion_agent/inference.py`, cached context in `backend/outputs/context_cache/`.
- Used by: `backend/run_simulation.py` and `/api/run-simulation` in `backend/routes.py`.

**Intelligence Pipeline Layer:**
- Purpose: Build node-level intelligence context by chaining fetch/filter/extract/narrate/synthesize phases.
- Location: `backend/src/agents/intelligence_agent/`.
- Contains: `NodeOrchestrator` and `SmartGridIntelligenceAgent` in `orchestrator.py`, plus specialized phase agents (`city_intel_agent.py`, `event_radar_agent.py`, `filter_agent.py`, `multiplier_synth_agent.py`).
- Depends on: External APIs through `DataFetcher` (`fetching_details.py`), OpenAI client initialization in `orchestrator.py`, cache/dataclass definitions in `setup.py`.
- Used by: `backend/main.py` (`generate_intelligence`) and POST `/api/generate-intelligence` in `backend/routes.py`.

**Persistence/Artifact Layer:**
- Purpose: Persist intelligence snapshots, per-node cache, simulation outputs, and state capacities as JSON files.
- Location: `backend/outputs/` and root `outputs/` (legacy fallback path also referenced in `backend/routes.py`).
- Contains: `context_cache/node_*_YYYY-MM-DD.json`, `grid_intelligence_YYYY-MM-DD.json`, `simulation_result_YYYY-MM-DD.json`, `state_capacities.json`.
- Depends on: All backend producer flows writing via `Path.write_text` in `backend/main.py`, `backend/run_simulation.py`, and `backend/routes.py`.
- Used by: Read paths in `backend/routes.py` (`_load_node_cache`, `_latest_simulation_file`, `_load_latest_dispatch_log`) and initial UI fetches in `frontend/src/hooks/useApi.js`.

## Data Flow

**Intelligence Refresh Flow:**

1. Client calls `POST /api/generate-intelligence` from UI or manual API call to `backend/routes.py`.
2. Route runs `_generate_intelligence()` which invokes `SmartGridIntelligenceAgent.run_all_regions()` from `backend/src/agents/intelligence_agent/orchestrator.py`.
3. Orchestrator runs per-node phases and writes node cache plus aggregate intelligence to `backend/outputs/context_cache/` and `backend/outputs/grid_intelligence_*.json`.
4. `GET /api/intelligence` reads cache-only data through `_load_node_cache()` and returns normalized payload consumed by `frontend/src/app/intelligence/page.js`.

**Simulation Execution Flow:**

1. UI starts simulation with `runSimulation()` in `frontend/src/hooks/useApi.js`, posting to `/api/run-simulation`.
2. `backend/routes.py` launches `backend/run_simulation.py` as a subprocess and streams stdout lines to the browser via `StreamingResponse`.
3. `run_simulation.py` loads context, computes state positions, clears market with routing agents, applies flows through `GridEnvironment`, and settles results.
4. Final output is written to `backend/outputs/simulation_result_*.json`; frontend then calls `GET /api/simulation-result` and renders `DispatchTable`, `DispatcherRadar`, and map overlays.

**State Management:**
- Use server-side file snapshots as the source of truth for intelligence and simulation outputs (`backend/outputs/*.json`).
- Use client-side React state for transient UI lifecycle (`running`, `done`, `logs`, `results`) inside `frontend/src/hooks/useApi.js`.

## Key Abstractions

**GridEnvironment and Physical Entities:**
- Purpose: Represent nodes, edges, paths, congestion, flow application, and battery behavior.
- Examples: `backend/src/environment/grid_physics.py` (`GridEnvironment`, `RegionNode`, `TransmissionEdge`, `TransmissionPath`, `BatteryCell`).
- Pattern: Rich domain model with mutable simulation state and explicit helper methods (`set_daily_demand`, `apply_flow`, `reset_flows`).

**Agent Contracts via Shared Dataclasses:**
- Purpose: Keep inter-agent communication strongly structured (orders, dispatches, state positions).
- Examples: `backend/src/agents/shared/models.py` (`Order`, `DispatchRecord`, `StatePosition`, `LoadSheddingRecord`).
- Pattern: Dataclass-based message contracts passed between state/routing/settlement subsystems.

**NodeOrchestrator Phase Pipeline:**
- Purpose: Execute deterministic phase order for intelligence generation with traceability.
- Examples: `backend/src/agents/intelligence_agent/orchestrator.py` (`NodeOrchestrator.run`, `_build_phase_trace`).
- Pattern: Ordered pipeline composition with injected agent instances stored in role-keyed registry (`self._agents`).

**Frontend API Hook Facade:**
- Purpose: Encapsulate API calls and stream handling in reusable hooks.
- Examples: `frontend/src/hooks/useApi.js` (`useIntelligence`, `useGridStatus`, `useSimulation`).
- Pattern: Hook-based adapter layer mapping REST endpoints into page-level reactive data.

## Entry Points

**Backend API Entrypoint:**
- Location: `backend/server.py`
- Triggers: `uvicorn server:app --reload --port 8000` or `python server.py`.
- Responsibilities: Import and expose FastAPI app from `backend/routes.py`.

**Backend Workflow Entrypoint:**
- Location: `backend/main.py`
- Triggers: `python main.py`.
- Responsibilities: Run intelligence generation, execute simulation step, and perform in-process route validation.

**Simulation Script Entrypoint:**
- Location: `backend/run_simulation.py`
- Triggers: Direct script execution or subprocess spawn from `POST /api/run-simulation`.
- Responsibilities: Execute multi-day simulation loop, accumulate logs, and write result JSON.

**Frontend Entrypoint:**
- Location: `frontend/src/app/layout.js` and `frontend/src/app/page.js`
- Triggers: `npm run dev` / Next.js runtime.
- Responsibilities: Mount global layout/navigation and route users to dashboard, intelligence, and simulation pages.

## Error Handling

**Strategy:** Local try/except guards with fallback payloads for read paths, and HTTPException for explicit API failures.

**Patterns:**
- Raise API-level failures with `HTTPException` in `backend/routes.py` (for example `_generate_intelligence()` and missing simulation script checks).
- Return safe defaults when cache/results are absent in `backend/routes.py` (`_build_fallback_intelligence`, empty dispatch list, `"no_result"` object).

## Cross-Cutting Concerns

**Logging:** Use stdout prints and Python logging in orchestration/simulation (`backend/main.py`, `backend/run_simulation.py`, `backend/src/agents/intelligence_agent/orchestrator.py`).
**Validation:** Minimal schema validation via typed dataclasses in `backend/src/agents/shared/models.py`; no centralized request-validation layer beyond FastAPI typing in `backend/routes.py`.
**Authentication:** Not detected on API routes in `backend/routes.py` (evidence gap: no auth middleware, dependency injection, or token checks found in inspected backend entry files).

---

*Architecture analysis: 2026-04-05*
