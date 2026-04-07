# Phase 15: White Routing, A+ Event Fetching & XAI UI Rephrasing - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade Phase 6 routing to **predict transit risks** before locking paths (White Routing), enhance event scraping for **comprehensive multi-source coverage** (economic, climatic, political), and transform XAI output into **human-readable command center narratives** with detail drill-down.

This phase delivers:
1. **Stimulus Radar** — IntelligenceAgent marks transit nodes with forward-looking risk flags
2. **Risk-Aware Path Selection** — Phase 6 deprioritizes risky paths instead of naive BFS
3. **A+ Event Fetching** — Full spectrum event detection (weather + grid + economic + political)
4. **XAI Rephrasing** — Plain English summaries for operators with "Show Details" technical drill-down

</domain>

<decisions>
## Implementation Decisions

### White Routing: Query Architecture
- **D-01:** Hybrid approach — pre-compute risk map at day start, selective query if base risk > threshold
- **D-02:** IntelligenceAgent produces `transit_risk_map: Dict[str, RiskScore]` at simulation day start
- **D-03:** Phase 6 queries `IntelligenceAgent.get_detailed_risk(state, hours_ahead)` only when base risk exceeds threshold

### White Routing: Stimulus Flag Sources
- **D-04:** Full spectrum stimulus detection:
  - Weather: Storms, heatwaves, cyclones, heavy precipitation (Open-Meteo)
  - Grid Events: Outages, maintenance schedules, transmission line trips (RSS feeds)
  - Economic: Coal prices, fuel shortages, industrial load patterns
  - Political: Strikes, elections, festivals, bandhs
- **D-05:** All sources feed into unified `StimulusFlag` dataclass with `source`, `severity`, `eta_hours`, `estimated_impact_mw`

### White Routing: Risk Response Behavior
- **D-06:** Deprioritize risky paths — sort by risk-adjusted score, prefer safer routes but still consider risky ones if no alternative
- **D-07:** Do NOT hard-block based on stimulus flags alone (unlike memory warnings which block)
- **D-08:** Risk score affects path ranking, not path availability

### White Routing: Transit Node Weighting
- **D-09:** Position-weighted risk calculation:
  - First hop (seller) and last hop (buyer): 100% risk weight
  - Middle transit nodes: 50% risk weight
- **D-10:** Path total risk = weighted sum of all node risks along path

### XAI Rephrasing: Audience
- **D-11:** Primary audience: Executive/Regulator — plain English, no grid jargon, high-level summary
- **D-12:** Secondary audience: Technical operators — detailed view available on demand

### XAI Rephrasing: UI Structure
- **D-13:** Three-panel dashboard layout:
  - **NOW** (🔴): Current grid state, active interventions
  - **PREDICTED** (🟡): Upcoming situations based on forecasts
  - **RISK WATCH** (⚠️): Forward-looking risks from stimulus radar
- **D-14:** Each panel has "Show Details" toggle for technical drill-down

### XAI Rephrasing: Generation Method
- **D-15:** Backend generates both versions — `Phase8XAIAgent` returns:
  ```python
  {
      "plain_summary": "UP is facing a 420 MW shortage...",
      "technical_details": "[Total Deficit]=420.00 MW | ...",
      "panel_data": {
          "now": {...},
          "predicted": {...},
          "risk_watch": {...}
      }
  }
  ```
- **D-16:** No LLM rephrasing at runtime — use template-based generation for consistency and cost efficiency
- **D-17:** Frontend renders `plain_summary` by default, reveals `technical_details` on button click

### Agent Discretion
- Exact risk score thresholds (HIGH/MEDIUM/LOW boundaries)
- Template sentence patterns for plain English generation
- Specific API structure for frontend consumption
- Caching strategy for risk map

</decisions>

<specifics>
## Specific Ideas

- **White Routing concept from user:** "Before the SyndicateAgent locks in a path (e.g., Karnataka → WB → Bihar → UP), it queries the IntelligenceAgent for 'Stimulus Flags' on the transit nodes. If the news or weather indicates a massive storm hitting West Bengal in 2 hours, the 'risk weight' of that path increases."

- **Impact goal:** "Prevents cascading failures where a trade starts, the line trips midway, and the sudden loss of power crashes the receiving state's frequency."

- **XAI clarity:** "It has to rephrase and show in the UI not exactly as it is. We have to properly show in command people understandable form what is happening, what is predicted, what might happen."

- **A+ grade events:** "All events economic and climatic and other disruptions or events that might increase or decrease the energy — fetch them properly with respect to the city."

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Event Scraping
- `backend/src/agents/intelligence_agent/event_scraper.py` — Current RSS scraping, `EventScraper` class, `WeatherScraper` class, `GRID_KEYWORDS`, `STATE_ALIASES`
- `backend/src/agents/intelligence_agent/setup.py` — `TRUSTED_RSS_FEEDS`, `ScrapedEvent` dataclass, `CITY_REGISTRY`

### Existing Routing Logic
- `backend/src/agents/routing_agent/phase6_negotiation_agent.py` — Current BFS-style `propose_trades()`, memory warning blocking via `blocked_pairs`
- `backend/src/agents/routing_agent/unified_routing_orchestrator.py` — Waterfall orchestration, memory read/write loops

### Existing XAI Output
- `backend/src/agents/routing_agent/phase8_xai_agent.py` — Current `Phase8Summary` dataclass, `build_summary()`, `_generate_memory_warning()`

### Project Architecture
- `.planning/PROJECT.md` — 4-stage workflow overview, patent features
- `.planning/ROADMAP.md` — Phase dependencies
- `AGENT_REGISTRY.md` — All 35 agents mapped to stages

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EventScraper.classify_event_type()` — Already classifies: outage, weather, supply_drop, demand_spike, political, capacity_addition
- `EventScraper.detect_affected_states()` — Maps events to state IDs via `STATE_ALIASES`
- `EventScraper.estimate_mw_impact()` — Extracts MW values from event text
- `WeatherScraper.detect_weather_anomaly()` — Returns anomaly dict with type, severity, estimated_demand_increase_pct
- `Phase6NegotiationAgent.propose_trades()` — Already accepts `memory_warnings` and blocks routes — can be extended for risk scoring

### Established Patterns
- Dataclass-based contracts (`ScrapedEvent`, `Phase8Summary`, `ProposedTrade`)
- Deterministic logic in routing agents (no LLM in hot path)
- Memory warning format: `"WARNING: A->B hit thermal cap"` — Phase 6 parses this

### Integration Points
- `IntelligenceAgent` (new component) will sit between `EventScraper`/`WeatherScraper` and `Phase6NegotiationAgent`
- `Phase8XAIAgent.build_summary()` needs to return new structure with `plain_summary` + `panel_data`
- Frontend currently consumes raw JSON from `/api/simulation` — needs new XAI response contract

</code_context>

<deferred>
## Deferred Ideas

- **Real-time WebSocket updates** — UI currently polls; live push would require infra changes
- **ML-based risk prediction** — Using historical data to predict failures (beyond rule-based)
- **Multi-language XAI output** — Hindi/regional language summaries for local operators

</deferred>

---

*Phase: 15-white-routing-and-xai-ui*
*Context gathered: 2026-04-07*
