"""Stochastic Trigger (intelligence.py).

Uses the real intelligence-agent pipeline (trusted RSS/event scraping) and
persists day-indexed cache payloads for simulator/API consumers.
"""

from __future__ import annotations

import json
import io
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.agents.intelligence_agent.orchestrator import SmartGridIntelligenceAgent


class StochasticTrigger:
    """Daily intelligence layer backed by real event scraping."""

    def __init__(self, backend_dir: Path | None = None) -> None:
        self.backend_dir = backend_dir or Path(__file__).resolve().parent
        self.cache_dir = self.backend_dir / "outputs" / "intelligence_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._agent = SmartGridIntelligenceAgent()

    def _cache_path(self, day_index: int) -> Path:
        return self.cache_dir / f"day_{day_index:03d}.json"

    @staticmethod
    def _extract_primary_event_name(raw: Dict[str, Any]) -> str:
        events = raw.get("phase_1_grid_events", []) or []
        if events and isinstance(events, list):
            first = events[0] or {}
            name = str(first.get("event_name", "")).strip()
            if name:
                return name
        return "no_grid_event_detected"

    def generate_daily_report(
        self,
        *,
        day_index: int,
        date_str: str,
        state_ids: List[str],
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Return real per-state event + multiplier report, with day cache."""
        cache = self._cache_path(day_index)
        if cache.exists() and not force_refresh:
            return json.loads(cache.read_text(encoding="utf-8"))

        rows: List[Dict[str, Any]] = []
        state_multipliers: Dict[str, float] = {}
        raw_agent_payload: Dict[str, Any] = {}

        try:
            # Runs the real intelligence stack:
            # SmartGridIntelligenceAgent -> DeviationDetector -> EventScraper.
            with contextlib.redirect_stdout(io.StringIO()):
                raw_agent_payload = self._agent.run_all_regions()

            for state_id in state_ids:
                data = raw_agent_payload.get(state_id, {}) or {}
                multipliers = data.get("grid_multipliers", {}) or {}
                demand_multiplier = float(multipliers.get("economic_demand_multiplier", 1.0))
                event_name = self._extract_primary_event_name(data)
                source_event_count = len(data.get("phase_1_grid_events", []) or [])

                state_multipliers[state_id] = demand_multiplier
                rows.append(
                    {
                        "state_id": state_id,
                        "event_name": event_name,
                        "demand_multiplier": round(demand_multiplier, 4),
                        "source": "intelligence_agent_live",
                        "source_event_count": source_event_count,
                    }
                )

        except Exception as exc:
            # Do not fabricate mock events; fail safe to neutral multipliers.
            for state_id in state_ids:
                state_multipliers[state_id] = 1.0
                rows.append(
                    {
                        "state_id": state_id,
                        "event_name": "intelligence_fetch_failed",
                        "demand_multiplier": 1.0,
                        "source": "intelligence_agent_live",
                        "error": str(exc),
                        "source_event_count": 0,
                    }
                )

        report = {
            "day_index": day_index,
            "date": date_str,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "events": rows,
            "state_multipliers": state_multipliers,
            "agent_payload": raw_agent_payload,
        }
        cache.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
