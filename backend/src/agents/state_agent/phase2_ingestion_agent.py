"""Phase 2 deterministic ingestion and deviation math for StateAgent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from src.agents.intelligence_agent.setup import GridEvent


@dataclass(frozen=True)
class IngestionResult:
    adjusted_supply_mw: float
    adjusted_demand_mw: float
    net_position_mw: float
    deficit_mw: float
    surplus_mw: float
    is_deficit: bool
    event_applied: GridEvent | None
    demand_multiplier: float
    supply_multiplier: float


class Phase2IngestionAgent:
    """
    Applies Phase 2 event-aware supply/demand math.
    """

    def _pick_event_for_state(self, state_id: str, events: Iterable[GridEvent]) -> GridEvent | None:
        for event in events:
            if state_id in event.affected_states:
                return event
        return None

    def evaluate(
        self,
        state_id: str,
        lightgbm_base_demand_mw: float,
        hardcoded_supply_mw: float,
        grid_events: List[GridEvent],
    ) -> IngestionResult:
        event = self._pick_event_for_state(state_id=state_id, events=grid_events)
        demand_multiplier = event.demand_multiplier if event is not None else 1.0
        supply_multiplier = event.supply_multiplier if event is not None else 1.0

        adjusted_supply = float(hardcoded_supply_mw) * float(supply_multiplier)
        adjusted_demand = float(lightgbm_base_demand_mw) * float(demand_multiplier)
        net_position = adjusted_supply - adjusted_demand

        is_deficit = net_position < 0.0
        deficit_mw = abs(net_position) if is_deficit else 0.0
        surplus_mw = net_position if net_position > 0.0 else 0.0

        return IngestionResult(
            adjusted_supply_mw=adjusted_supply,
            adjusted_demand_mw=adjusted_demand,
            net_position_mw=net_position,
            deficit_mw=deficit_mw,
            surplus_mw=surplus_mw,
            is_deficit=is_deficit,
            event_applied=event,
            demand_multiplier=float(demand_multiplier),
            supply_multiplier=float(supply_multiplier),
        )
