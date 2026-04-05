# Codebase Concerns

**Analysis Date:** 2026-04-05

## Tech Debt

**Routing safety check is a probabilistic stub instead of deterministic validation (Severity: High):**
- Issue: Route approval is randomized (`random.random() < LLM_APPROVAL_PROBABILITY`) rather than based on real safety constraints.
- Files: `backend/src/agents/routing_agent/llm_safety_stub.py`, `backend/src/agents/routing_agent/routing_agent.py`
- Impact: Dispatch outcomes are non-deterministic and may approve unsafe paths or reject valid ones between runs; this undermines reliability and reproducibility.
- Fix approach: Replace stubbed logic with deterministic rule-based checks tied to `TransmissionPath`/edge constraints and make approval traces auditable in `decision_trace`.

**Public simulation/intelligence execution endpoints have no auth guards (Severity: High):**
- Issue: Compute-expensive and side-effecting endpoints are callable without authentication/authorization.
- Files: `backend/routes.py` (`/api/run-simulation`, `/api/generate-intelligence`)
- Impact: Any caller can trigger subprocess execution and external API usage, creating abuse/cost risk and denial-of-service potential.
- Fix approach: Require API auth (token/session), role checks, and per-client rate limiting before invoking pipeline/subprocess actions.

**Exception swallowing hides data integrity and runtime failures (Severity: High):**
- Issue: Multiple broad `except Exception: pass` / empty `catch {}` blocks suppress root-cause visibility.
- Files: `backend/routes.py` (`_load_node_cache`, `_load_latest_dispatch_log`), `frontend/src/hooks/useApi.js` (`apiFetch`, simulation run catch), `backend/run_simulation.py` (model-load fallback)
- Impact: Failures degrade silently into empty/default outputs, making operational issues hard to detect and increasing risk of incorrect UI/dispatch decisions.
- Fix approach: Log structured errors with context, expose recoverable vs unrecoverable states to API/UI, and avoid blanket `pass`.

## Known Bugs

**Frontend README advertises mock fallback that is not implemented in current hook code (Severity: Medium):**
- Symptoms: UI receives `null` on API failure instead of deterministic mock data.
- Files: `frontend/README.md` (claims mock fallback), `frontend/src/hooks/useApi.js` (`apiFetch` returns `null`)
- Trigger: Backend unavailable or API errors.
- Workaround: Run backend locally before frontend; no in-code mock fallback path is currently active.

**Grid status endpoint applies generation multiplier but not demand multiplier context (Severity: Medium):**
- Symptoms: `/api/grid-status` response can under-represent intelligence-adjusted demand while showing adjusted generation.
- Files: `backend/routes.py` (`grid_status`, `node.adjusted_demand_mw = node.demand_mw`)
- Trigger: Non-neutral demand multipliers in cached intelligence.
- Workaround: Use simulation outputs (`/api/simulation-result`) for adjusted-demand-dependent views.

## Security Considerations

**CORS policy is broad for methods/headers and assumes localhost-only trust boundary (Severity: Medium):**
- Risk: Any method/header is allowed from configured origins; if origin list expands without controls, API surface is broadly exposed.
- Files: `backend/routes.py` (`CORSMiddleware` with `allow_methods=["*"]`, `allow_headers=["*"]`)
- Current mitigation: Origins are currently limited to localhost URLs.
- Recommendations: Restrict methods/headers to required set and pair with auth + CSRF strategy appropriate for deployment model.

**`.env` files exist but no startup validation contract is centralized (Severity: Medium):**
- Risk: Runtime behavior depends on environment variables but validation is partial/inconsistent across modules.
- Files: `backend/.env` (present), `frontend/.env.local` (present), `backend/src/agents/intelligence_agent/orchestrator.py` (key checks), `frontend/src/hooks/useApi.js` (`NEXT_PUBLIC_API_URL`)
- Current mitigation: Intelligence orchestrator checks for required API keys.
- Recommendations: Add explicit startup config validation for all required variables and fail fast with actionable errors.

## Performance Bottlenecks

**Synchronous multi-source fetch + deliberate sleeps in intelligence pipeline (Severity: Medium):**
- Problem: Node orchestration performs sequential external calls and inserts `time.sleep(0.4)` per query and `time.sleep(2)` per node.
- Files: `backend/src/agents/intelligence_agent/orchestrator.py`
- Cause: Serial execution with throttle sleeps inside request/compute path.
- Improvement path: Move to background job queue with status polling; parallelize independent fetches and bound retries/timeouts.

**`/api/grid-status` reconstructs environment and cache-derived state on every request (Severity: Medium):**
- Problem: Endpoint creates `GridEnvironment`, recalculates demand, and maps full nodes/edges each call.
- Files: `backend/routes.py`, `backend/src/environment/grid_physics.py`
- Cause: No memoization/cache layer for frequently requested dashboard data.
- Improvement path: Cache short-lived snapshots and invalidate on new intelligence/simulation runs.

## Fragile Areas

**Path/cwd-dependent model and output paths (Severity: Medium):**
- Files: `backend/run_simulation.py` (`model/...`, `outputs/...` relative paths), `backend/routes.py` (mix of `BACKEND_DIR/outputs` and repo-root fallback)
- Why fragile: Running from different working directories can break artifact resolution or split outputs across locations.
- Safe modification: Standardize absolute paths anchored to `Path(__file__)` and centralize path configuration.
- Test coverage: No automated tests detected for path resolution behavior.

**Fallback-heavy API behavior can mask stale or incomplete data contracts (Severity: Medium):**
- Files: `backend/routes.py` (`_build_fallback_intelligence`, empty-list fallbacks), `frontend/src/hooks/useApi.js` (null fallback)
- Why fragile: Consumers may treat fallback/default as valid live data without explicit freshness/error flags.
- Safe modification: Include explicit `source`, `stale`, and `error` metadata in API responses and require UI badges for degraded states.
- Test coverage: No API contract tests detected in repository paths inspected.

## Scaling Limits

**Unbounded simulation process spawning from API endpoint (Severity: High):**
- Current capacity: One subprocess per request via `subprocess.Popen([sys.executable, run_simulation.py])`.
- Limit: Concurrent calls can saturate CPU/memory and I/O with no queueing, locking, or admission control.
- Scaling path: Add job queue + worker pool + max-concurrency guard; return job IDs instead of direct process streaming.
- Files: `backend/routes.py`

## Dependencies at Risk

**Version drift risk from non-pinned core server dependencies (Severity: Medium):**
- Risk: `fastapi>=0.111.0` and `uvicorn[standard]>=0.29.0` permit incompatible upgrades over time.
- Impact: Behavior/regression risk across environments and deployments.
- Migration plan: Pin exact versions, use lockfiles, and update through tested dependency bumps.
- Files: `backend/requirements.txt`

## Missing Critical Features

**No authentication/authorization layer for control-plane operations (Severity: High):**
- Problem: Sensitive operational actions (generate intelligence, run simulation) are unauthenticated.
- Blocks: Safe multi-user or internet-exposed deployment.
- Files: `backend/routes.py`

**No explicit rate limiting/backpressure on expensive endpoints (Severity: High):**
- Problem: API can be spammed with compute-heavy jobs and external-data fetches.
- Blocks: Predictable uptime under load and cost control.
- Files: `backend/routes.py`, `backend/src/agents/intelligence_agent/orchestrator.py`

## Test Coverage Gaps

**Backend simulation/routing/intelligence core lacks automated tests (Severity: High):**
- What's not tested: Dispatch clearing, safety gates, settlement, intelligence synthesis, and endpoint behavior.
- Files: `backend/run_simulation.py`, `backend/routes.py`, `backend/src/agents/routing_agent/*.py`, `backend/src/agents/intelligence_agent/*.py`
- Risk: Regressions in dispatch math/safety behavior can ship unnoticed.
- Priority: High

**Frontend API integration and degraded-state UX are untested (Severity: Medium):**
- What's not tested: `null` responses, stream interruption handling, and cross-page data shape consistency.
- Files: `frontend/src/hooks/useApi.js`, `frontend/src/app/intelligence/page.js`, `frontend/src/app/simulation/page.js`
- Risk: UI can present incomplete/incorrect operational state without clear failure messaging.
- Priority: Medium

**Evidence missing for formal test harness (Severity: Medium):**
- What's not tested: Test runner setup itself.
- Files: `frontend/package.json` (no `test` script), repository paths inspected show no `*.test.*`/`*.spec.*` files under `backend/src` and `frontend/src`.
- Risk: No enforced quality gate before changes.
- Priority: Medium

---

*Concerns audit: 2026-04-05*
