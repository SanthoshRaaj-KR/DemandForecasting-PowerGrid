"""Phase 5 incident-aware thermal derating for corridor capacities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from src.agents.intelligence_agent.setup import GridEvent


@dataclass(frozen=True)
class EdgeDeratingResult:
    capacities_mw: Dict[Tuple[str, str], float]
    impacted_edges: Dict[Tuple[str, str], str]


class Phase5IncidentDispatcherAgent:
    """
    Applies event-driven thermal derating to edges touching impacted states.
    """

    def __init__(self, default_penalty: float = 0.20):
        self.default_penalty = max(min(float(default_penalty), 1.0), 0.0)

    @staticmethod
    def _is_incident_event(event_name: str) -> bool:
        lowered = event_name.lower()
        return any(keyword in lowered for keyword in ("heatwave", "fire", "surge", "outage", "strike"))

    def derive_daily_capacities(
        self,
        base_capacities_mw: Dict[Tuple[str, str], float],
        grid_events: Iterable[GridEvent],
    ) -> EdgeDeratingResult:
        capacities = {k: float(v) for k, v in base_capacities_mw.items()}
        impacted: Dict[Tuple[str, str], str] = {}

        for event in grid_events:
            if not self._is_incident_event(event.event_name):
                continue

            affected_states = set(event.affected_states)
            for edge_key, base_cap in list(capacities.items()):
                src, dst = edge_key
                if src in affected_states or dst in affected_states:
                    derated = max(base_cap * (1.0 - self.default_penalty), 0.0)
                    capacities[edge_key] = derated
                    impacted[edge_key] = event.event_name

        return EdgeDeratingResult(capacities_mw=capacities, impacted_edges=impacted)
