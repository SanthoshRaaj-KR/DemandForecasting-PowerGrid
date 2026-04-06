# Smart Grid Simulation - Roadmap

**Project:** Multi-Agent Smart Grid Simulator  
**Milestone:** M1 - Core Workflow Foundation  
**Status:** Phase 1 in progress

---

## Overview

This roadmap implements the **4-stage workflow** (A Priori Planner → Delta Trigger → Waterfall Orchestrator → Self-Healing Memory) across 5 phases, establishing the architectural foundation before building patent features.

**Scope:** Backend only (frontend deferred to Phase 11)  
**Target:** Autonomous 30-day grid simulation with ~70% LLM cost reduction

---

## Phase 1: Agent Architecture Cleanup

**Goal:** Audit and streamline agent hierarchy from 20+ scattered files to 8 core agents with clear workflow mapping

**Requirements:** REQ-001, REQ-002, REQ-003

**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Audit existing agents and create registry
- [ ] 01-02-PLAN.md — Delete/merge redundant agents
- [ ] 01-03-PLAN.md — Validate new structure

**Success Criteria:**
- AGENT_REGISTRY.md exists mapping all agents to stages
- `src/agents/` has max 8 subdirectories
- All tests pass after cleanup

---

## Phase 2: Stage 1 - A Priori Planner Integration

**Goal:** Integrate LightGBM baseline scheduling that creates 30-day forecast and sets LLM sleep/wake flags

**Requirements:** REQ-004, REQ-005, REQ-006

**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Refactor ForwardMarketPlanner with baseline generation
- [ ] 02-02-PLAN.md — Update main.py workflow to run planner first

**Success Criteria:**
- `outputs/baseline_schedule_YYYY-MM-DD.json` generated
- Contains 30-day predictions for all 4 states
- `llm_agents_enabled` flag correctly set per day

---

## Phase 3: Stage 2 - Delta Trigger Mechanism

**Goal:** Implement anomaly detection and Delta calculation that conditionally wakes LLM agents only when needed

**Requirements:** REQ-007, REQ-008, REQ-009, REQ-010

**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Refactor IntelligenceAgent with Delta calculation
- [ ] 03-02-PLAN.md — Add conditional LLM trigger logic

**Success Criteria:**
- `outputs/delta_YYYY-MM-DD.json` only created on anomaly days
- Test: 30-day simulation shows LLMs wake on ~10% of days
- Delta calculation: `actual_demand - baseline_demand`

---

## Phase 4: Stage 3 - Strict Waterfall Orchestrator

**Goal:** Enforce 4-step deficit resolution sequence (Temporal → Economic → Spatial → Fallback)

**Requirements:** REQ-011, REQ-012, REQ-013, REQ-014, REQ-015

**Plans:** 3 plans

Plans:
- [ ] 04-01-PLAN.md — Refactor UnifiedRoutingOrchestrator with waterfall logic
- [ ] 04-02-PLAN.md — Implement Steps 1-2 (Battery + DR stub)
- [ ] 04-03-PLAN.md — Implement Steps 3-4 (Routing + Fallback)

**Success Criteria:**
- Battery always drained before DR attempted
- DR attempted before transmission routing
- Routing attempted before load shedding
- Test: Verify step sequence in XAI logs

---

## Phase 5: Stage 4 - Self-Healing Memory (XAI Write Loop)

**Goal:** Enable XAI agent to autonomously write failure warnings to memory buffer for next-day learning

**Requirements:** REQ-016, REQ-017, REQ-018, REQ-019

**Plans:** 2 plans

Plans:
- [ ] 05-01-PLAN.md — Refactor XAIAgent with memory write logic
- [ ] 05-02-PLAN.md — Test memory injection into routing prompts

**Success Criteria:**
- `grid_short_term_memory` buffer limited to 3 items
- Memory entries auto-generated after transmission failures
- Test: 5-day heatwave simulation shows memory prevents repeated bottlenecks

---

## Milestone Success Criteria

M1 complete when:
- ✅ All 5 phases marked complete
- ✅ All requirements (REQ-001 through REQ-019) validated
- ✅ 30-day simulation runs end-to-end
- ✅ LLM API calls reduced by ~70% (vs always-on baseline)
- ✅ Memory buffer demonstrates autonomous learning

---

## Next Milestone

**M2 - Patent Features** (Phases 6-8):
- Phase 6: DR Bounty Reverse Auction
- Phase 7: Lifeboat Protocol (Graph-Cut Islanding)
- Phase 8: Recursive Hyperparameter Autopsy

*Not in scope for current execution*

---

**Roadmap Version:** 1.0  
**Last Updated:** 2026-04-06
