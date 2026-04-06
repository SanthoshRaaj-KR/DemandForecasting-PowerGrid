# Smart Grid Multi-Agent Simulation

## Vision

Build a **production-grade Multi-Agent Smart Grid Simulator** that implements two patent-worthy innovations and three enterprise-grade enhancements to demonstrate how AI agents can autonomously optimize power distribution across a 4-state electrical grid.

## Problem

Current smart grid systems face critical limitations:
- **Black-box AI decisions** that regulators cannot audit or trust
- **Cascading blackouts** from poor load balancing (e.g., 2012 India blackout affecting 600M people)
- **Compute waste** from running expensive LLM agents on predictable baseline data
- **Static demand-response** programs that don't leverage market dynamics
- **No self-learning** capability without millions of training data rows

## Solution

A **4-stage agentic workflow** that combines traditional ML (LightGBM) for baseline predictions with LLM agents for anomaly handling:

**Stage 1: A Priori Planner** (Day 0)
- LightGBM predicts 30-day baseline for all 4 states (UP, Bihar, West Bengal, Karnataka)
- Creates baseline schedule, keeps LLM agents asleep for normal days

**Stage 2: Intelligence Extraction** (Daily)
- Stochastic event generator detects anomalies (heatwaves, strikes, etc.)
- Calculates Delta (unexpected MW deficit/surplus)
- Only wakes LLM agents if Delta > 0

**Stage 3: Strict Waterfall Orchestrator** (Anomaly days)
- Step 1 (Temporal): Drain state batteries first
- Step 2 (Economic): Run DR bounty reverse auction
- Step 3 (Spatial): Route power via BFS network graph
- Step 4 (Fallback): Lifeboat Protocol (graph-cut) or load shedding

**Stage 4: Self-Healing Memory** (End of day)
- XAI agent analyzes failures
- Writes 1-sentence warnings to 3-day sliding window buffer
- Memory prevents repeated mistakes tomorrow

## Core Features (Patent + Enhancements)

### 🔥 PATENT 1: Recursive LLM Parameter Autopsy
**Innovation:** Zero-shot self-healing without neural networks
- At end of 30-day cycle, LLM Overseer reads XAI logs
- Autonomously generates JSON patches to Python config files
- Next cycle runs with updated hyperparameters (e.g., DR bounty prices)
- **Novel:** Agentic learning via reflection, not backpropagation

### 🔥 PATENT 2: Lifeboat Protocol (Graph-Cut Islanding)
**Innovation:** Autonomous topology severance
- Monitors national grid frequency (target: 50 Hz)
- If f < 49.5 Hz (emergency), calculates which state to sacrifice
- Runs min-cut graph algorithm to sever transmission edges
- Intentionally islands one state to save the other three
- **Novel:** LLM + Graph Theory for autonomous circuit breaking

### ✅ ENHANCEMENT 1: 7-Phase XAI Audit Ledger
**Upgrade:** Legal compliance via chain-of-thought logging
- Every MW routed generates Phase Trace with human-readable justification
- Exports regulator-ready audit: "Phase 2: Drained 150MW from battery because..."
- **Impact:** Makes AI legally deployable (regulators can audit decisions)

### ✅ ENHANCEMENT 2: Game-Theoretic DR Bounties
**Upgrade:** Micro-auctions for demand response
- States broadcast deficit to local prosumers (factories, EVs, homes)
- Prosumers bid their shutdown price
- System clears cheapest bids first (reverse auction)
- **Impact:** Creates micro-economy, rewards efficiency over burning coal

### ✅ ENHANCEMENT 3: Two-Tier Delta Orchestrator
**Upgrade:** Radical compute cost reduction
- LightGBM handles 90% predictable baseline (cheap, fast)
- LLM agents only wake for 10% unpredictable chaos (Delta > 0)
- **Impact:** ~70% API cost savings vs always-on LLM approach

## Real-World Impact

1. **Economic:** Prevents billion-dollar cascading blackouts
2. **Regulatory:** First AI grid system with auditable decision-making
3. **Operational:** 70% compute cost reduction enables commercial SaaS deployment
4. **Democratic:** Prosumers become active market participants (not just consumers)

## Technical Stack

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI (async API server)
- **ML Model:** LightGBM (30-day demand forecasting)
- **LLM Integration:** OpenAI API (GPT-4 for agent reasoning)
- **Graph Library:** NetworkX (BFS routing, min-cut algorithm)
- **Optimization:** OR-Tools (auction clearing, constraint solving)

### Agents
- **IntelligenceAgent:** Anomaly detection, Delta calculation
- **StateAgent:** Battery management, local balancing
- **ProsumerAgent:** DR bid submission
- **DRBountyAuctioneer:** Reverse auction clearing
- **NegotiationAgent:** Multi-state power routing
- **SyndicateAgent:** BFS network traversal
- **LifeboatProtocol:** Graph-cut emergency failsafe
- **XAIAgent:** Audit ledger generation, memory management
- **HyperparameterOverseer:** 30-day recursive learning

### Grid Simulation
- **GridPhysics:** Transmission line physics (losses, capacities, thermal limits)
- **4-State Topology:** UP, Bihar, West Bengal, Karnataka
- **Corridors:** 6 bidirectional transmission lines with MW capacities
- **Batteries:** State-level energy storage (500-1000 MW capacity)

### Frontend (Deferred)
- Next.js dashboard (Phase 11, not in scope for first 5 phases)

## Requirements

### Validated
(None yet - greenfield project)

### Active

#### Phase 1: Agent Architecture Cleanup
- [ ] REQ-001: Agent registry mapping all agents to 4-stage workflow
- [ ] REQ-002: Remove redundant/stub agent files (dummy_context, llm_safety_stub, etc.)
- [ ] REQ-003: Clear separation of concerns (max 8 core agents)

#### Phase 2: Stage 1 - A Priori Planner
- [ ] REQ-004: LightGBM baseline schedule generation
- [ ] REQ-005: Output baseline_schedule.json for 30-day period
- [ ] REQ-006: LLM agent sleep/wake flag based on Delta=0 detection

#### Phase 3: Stage 2 - Delta Trigger Mechanism
- [ ] REQ-007: Anomaly detection (heatwave, strike, equipment failure)
- [ ] REQ-008: Delta calculation (actual - baseline demand)
- [ ] REQ-009: Strict JSON output format for Delta events
- [ ] REQ-010: Conditional LLM wake-up (only if Delta > 0)

#### Phase 4: Stage 3 - Strict Waterfall Orchestrator
- [ ] REQ-011: 4-step waterfall enforcement (Temporal → Economic → Spatial → Fallback)
- [ ] REQ-012: Battery drainage before DR (Step 1)
- [ ] REQ-013: DR auction before transmission (Step 2)
- [ ] REQ-014: BFS routing before load shedding (Step 3)
- [ ] REQ-015: Lifeboat Protocol OR load shedding (Step 4)

#### Phase 5: Stage 4 - Self-Healing Memory
- [ ] REQ-016: XAI agent writes to grid_short_term_memory buffer
- [ ] REQ-017: 3-day sliding window (max 3 warnings)
- [ ] REQ-018: Memory injection into next-day LLM prompts
- [ ] REQ-019: Autonomous learning (avoid repeated failures)

### Out of Scope (First 5 Phases)
- Frontend dashboard - Deferred to Phase 11
- DR Bounty auction implementation - Phase 6 (economic enhancement)
- Lifeboat Protocol graph-cut - Phase 7 (patent feature)
- Hyperparameter autopsy - Phase 8 (30-day learning)
- Full XAI audit ledger - Phase 9 (compliance feature)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Focus on backend first (phases 1-5) | User requested no UI changes, establish core workflow | Frontend deferred to Phase 11 |
| Manual GSD bootstrap | PowerShell 6+ not available, Git Bash sufficient for Node.js tools | Execute phases directly without orchestration overhead |
| 4-state grid model | Matches real Indian grid topology (Bihar-UP-WB-Karnataka corridor) | Realistic transmission constraints |
| LightGBM + LLM hybrid | 90% baseline (cheap ML) + 10% anomaly (expensive LLM) | ~70% cost reduction vs pure LLM |

## Success Metrics

After Phase 5 completion:
- ✅ All agents mapped to clear workflow stages
- ✅ LightGBM baseline runs autonomously (Day 0)
- ✅ Delta trigger only wakes LLMs on anomaly days
- ✅ Waterfall orchestrator enforces 4-step sequence
- ✅ Memory buffer prevents repeated transmission failures
- ✅ Test: 30-day simulation shows ~70% reduction in LLM API calls

---

**Last Updated:** 2026-04-06 (Project initialized)
**Current Phase:** Phase 1 (Agent Architecture Cleanup)
**Next Milestone:** Core Workflow Foundation (Phases 1-5)
