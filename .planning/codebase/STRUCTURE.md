# Codebase Structure

**Analysis Date:** 2026-04-05

## Directory Layout

```text
Smart_Grid_Simulation/
├── backend/                     # FastAPI API, simulation engine, intelligence agents, Python assets
│   ├── src/                     # Core backend source modules
│   │   ├── agents/              # Agent subsystems (intelligence, state, routing, fusion, shared)
│   │   └── environment/         # Grid physics and transmission environment
│   ├── model/                   # Trained model artifacts and scaler metadata files
│   ├── outputs/                 # Backend-generated JSON outputs and per-node context cache
│   ├── data/                    # Raw/processed data folders for modeling workflows
│   ├── notebooks/               # Exploratory/modeling notebooks
│   ├── routes.py                # FastAPI route definitions
│   ├── server.py                # API server entrypoint
│   ├── main.py                  # Scripted orchestration entrypoint
│   └── run_simulation.py        # Standalone simulation execution script
├── frontend/                    # Next.js app for dashboard/intelligence/simulation UI
│   ├── src/
│   │   ├── app/                 # Route pages and top-level layout (App Router)
│   │   ├── components/          # Reusable UI and domain-specific components
│   │   ├── hooks/               # API/data hooks
│   │   └── lib/                 # Static metadata/constants
│   └── package.json             # Frontend scripts and dependencies
├── outputs/                     # Root-level simulation outputs (legacy/read fallback)
├── .planning/codebase/          # Codebase mapping documents consumed by GSD tooling
└── README.md                    # Manual run instructions
```

## Directory Purposes

**`backend/src/agents/intelligence_agent`:**
- Purpose: Multi-phase intelligence generation pipeline for each node/city.
- Contains: Orchestrator and phase agents (`orchestrator.py`, `city_intel_agent.py`, `event_radar_agent.py`, `filter_agent.py`, `signal_extractor_agent.py`, `impact_narrator_agent.py`, `multiplier_synth_agent.py`).
- Key files: `backend/src/agents/intelligence_agent/orchestrator.py`, `backend/src/agents/intelligence_agent/setup.py`.

**`backend/src/agents/state_agent`:**
- Purpose: Convert forecast + intelligence context into deterministic state positions and buy/sell orders.
- Contains: `state_agent.py`, `intermittency_agent.py`.
- Key files: `backend/src/agents/state_agent/state_agent.py`.

**`backend/src/agents/routing_agent`:**
- Purpose: Dispatcher gates, route scoring, market clearing, load-shedding decisions, and settlement support.
- Contains: `routing_agent.py`, `dispatcher.py`, `dispatch_window_agent.py`, `route_score_agent.py`, `settlement.py`, `syndicate_*.py`.
- Key files: `backend/src/agents/routing_agent/routing_agent.py`, `backend/src/agents/routing_agent/settlement.py`.

**`backend/src/agents/fusion_agent`:**
- Purpose: ML inference helpers for demand prediction and forecast shaping.
- Contains: `inference.py`, `hourly_fusion_agent.py`, `renewable_impact_agent.py`, `reserve_activation_agent.py`.
- Key files: `backend/src/agents/fusion_agent/inference.py`.

**`backend/src/agents/shared`:**
- Purpose: Shared enums/constants/dataclasses used across agents.
- Contains: `models.py`, `constants.py`.
- Key files: `backend/src/agents/shared/models.py`.

**`backend/src/environment`:**
- Purpose: Physical grid model and mutable simulation state.
- Contains: `grid_physics.py`.
- Key files: `backend/src/environment/grid_physics.py`.

**`frontend/src/app`:**
- Purpose: Route-level pages and shell for web UI.
- Contains: `layout.js`, `page.js`, `intelligence/page.js`, `simulation/page.js`, `globals.css`.
- Key files: `frontend/src/app/layout.js`, `frontend/src/app/page.js`, `frontend/src/app/intelligence/page.js`, `frontend/src/app/simulation/page.js`.

**`frontend/src/components`:**
- Purpose: Visual modules for charts, grid rendering, agent cards/chat, and common UI elements.
- Contains: `grid/`, `charts/`, `agents/`, `ui/`.
- Key files: `frontend/src/components/grid/GridMap.js`, `frontend/src/components/grid/SimTerminal.js`, `frontend/src/components/agents/RegionCard.js`, `frontend/src/components/ui/NavBar.js`.

**`frontend/src/hooks`:**
- Purpose: API access and stream-handling hooks.
- Contains: `useApi.js`.
- Key files: `frontend/src/hooks/useApi.js`.

## Key File Locations

**Entry Points:**
- `backend/server.py`: FastAPI app runtime entrypoint that imports `app` from `backend/routes.py`.
- `backend/main.py`: End-to-end backend workflow (intelligence + simulation + in-process route checks).
- `backend/run_simulation.py`: Simulation pipeline callable as script and via API subprocess.
- `frontend/src/app/layout.js`: Frontend root layout.
- `frontend/src/app/page.js`: Main dashboard landing route.

**Configuration:**
- `backend/requirements.txt`: Python dependency manifest.
- `frontend/package.json`: Frontend scripts/dependencies.
- `frontend/next.config.js`: Next.js runtime config (details not inspected in this run).
- `frontend/tailwind.config.js`: Styling config (details not inspected in this run).

**Core Logic:**
- `backend/routes.py`: API orchestration and file-backed read/write integration points.
- `backend/src/environment/grid_physics.py`: Grid and path abstractions.
- `backend/src/agents/intelligence_agent/orchestrator.py`: Intelligence phase orchestration.
- `backend/src/agents/routing_agent/routing_agent.py`: Dispatch/routing execution and decision logging.
- `backend/src/agents/state_agent/state_agent.py`: Node-level position and order generation.

**Testing:**
- Not detected in explored paths (`backend/` and `frontend/` did not show `*.test.*` or `*.spec.*` files during this architecture-focused mapping).

## Naming Conventions

**Files:**
- Backend Python modules use `snake_case.py` (`routing_agent.py`, `grid_physics.py`, `run_simulation.py`).
- Frontend React components use `PascalCase.js` (`GridMap.js`, `DispatchTable.js`, `RegionCard.js`).
- Frontend route files follow Next.js App Router conventions with `page.js` and `layout.js` in route directories.

**Directories:**
- Backend domain grouping is feature/role-based under `backend/src/agents/<agent_group>/`.
- Frontend grouping is UI-role-based under `frontend/src/components/<domain>/`.

## Where to Add New Code

**New Backend API Endpoint:**
- Primary code: `backend/routes.py` (new `@app.get`/`@app.post` handler).
- Supporting domain logic: place in `backend/src/agents/` or `backend/src/environment/` and call from route layer.

**New Intelligence Phase/Agent:**
- Implementation: `backend/src/agents/intelligence_agent/<new_agent>.py`.
- Wiring: inject and sequence in `backend/src/agents/intelligence_agent/orchestrator.py` (`self._agents` and `NodeOrchestrator.run`).

**New Simulation Behavior (state/market/dispatch):**
- State-level policy: `backend/src/agents/state_agent/`.
- Routing/dispatch/settlement policy: `backend/src/agents/routing_agent/`.
- Physical constraints/topology changes: `backend/src/environment/grid_physics.py`.

**New Frontend Module/Page:**
- Route page: `frontend/src/app/<route>/page.js`.
- Reusable component: `frontend/src/components/<domain>/<ComponentName>.js`.
- Data hook/API integration: extend `frontend/src/hooks/useApi.js`.

**Utilities:**
- Backend shared constants/models: `backend/src/agents/shared/`.
- Frontend static metadata/helpers: `frontend/src/lib/`.

## Special Directories

**`backend/outputs/context_cache`:**
- Purpose: Daily per-node intelligence cache and raw API dump files.
- Generated: Yes.
- Committed: Unknown (evidence gap: repo policy not inspected beyond directory snapshot).

**`backend/model`:**
- Purpose: Trained artifacts used at simulation runtime (`lightgbm_model.pkl`, scaler files under `backend/model/utils`).
- Generated: Yes (training output).
- Committed: Yes for at least `backend/model/lightgbm_model.pkl` in current tree snapshot.

**`frontend/.next`:**
- Purpose: Next.js build cache and generated artifacts.
- Generated: Yes.
- Committed: Unknown from mapping snapshot (presence detected in working tree).

**`outputs/` (repo root):**
- Purpose: Legacy/fallback simulation artifacts read by backend fallback logic in `backend/routes.py`.
- Generated: Yes.
- Committed: Unknown (evidence gap: commit history/policy not inspected).

---

*Structure analysis: 2026-04-05*
