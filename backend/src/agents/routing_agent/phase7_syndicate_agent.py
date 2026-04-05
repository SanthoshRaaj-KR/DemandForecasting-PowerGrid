"""Phase 7 syndicate execution with frequency-aware emergency intervention."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..shared.models import ProposedTrade


@dataclass(frozen=True)
class Phase7ExecutionResult:
    executed_trades: List[ProposedTrade]
    load_shedding_mw: Dict[str, float]
    remaining_deficit_mw: Dict[str, float]
    final_surplus_mw: Dict[str, float]
    final_edge_capacities_mw: Dict[Tuple[str, str], float]
    grid_frequency_before_hz: float
    grid_frequency_after_hz: float
    emergency_shed_mw: float
    frequency_triggered_emergency: bool
    observed_bottlenecks: List[str]


class Phase7SyndicateAgent:
    """
    Executes direct neighbor-to-neighbor trades, computes synthetic frequency,
    and performs emergency shedding only if critical frequency is breached.
    """

    BASE_FREQUENCY_HZ = 50.0
    CRITICAL_FREQUENCY_HZ = 49.5
    SAFE_FREQUENCY_TARGET_HZ = 49.9

    def __init__(self) -> None:
        self.historical_bottlenecks: List[Dict[str, str | int]] = []

    @classmethod
    def _frequency_from_deficit(cls, unserved_deficit_mw: float, total_grid_capacity_mw: float) -> float:
        if total_grid_capacity_mw <= 0:
            return cls.BASE_FREQUENCY_HZ
        percent_unserved = (max(float(unserved_deficit_mw), 0.0) / float(total_grid_capacity_mw)) * 100.0
        return cls.BASE_FREQUENCY_HZ - (0.1 * percent_unserved)

    @classmethod
    def _allowed_unserved_for_target(cls, total_grid_capacity_mw: float) -> float:
        # From formula: 50 - 0.1 * percent = target -> percent = (50-target)/0.1
        target_percent_unserved = (cls.BASE_FREQUENCY_HZ - cls.SAFE_FREQUENCY_TARGET_HZ) / 0.1
        return (target_percent_unserved / 100.0) * float(total_grid_capacity_mw)

    def warnings_for_day(self, day_index: int) -> List[str]:
        warnings: List[str] = []
        prev_day = int(day_index) - 1
        for entry in self.historical_bottlenecks:
            if int(entry.get("day_index", -999)) != prev_day:
                continue
            route = str(entry.get("route", "unknown-route"))
            reason = str(entry.get("reason", "congestion"))
            warnings.append(f"WARNING: {route} was severely congested yesterday ({reason}). Prefer alternate routes.")
        return warnings

    def record_bottlenecks(self, day_index: int, observed_bottlenecks: List[str]) -> None:
        for item in observed_bottlenecks:
            self.historical_bottlenecks.append(
                {
                    "day_index": int(day_index),
                    "route": item,
                    "reason": "thermal_dlr_or_route_failure",
                }
            )

    def execute(
        self,
        *,
        proposed_trades: List[ProposedTrade],
        deficit_states_mw: Dict[str, float],
        surplus_states_mw: Dict[str, float],
        daily_edge_capacities_mw: Dict[Tuple[str, str], float],
        total_grid_capacity_mw: float,
    ) -> Phase7ExecutionResult:
        remaining_deficit = {k: max(float(v), 0.0) for k, v in deficit_states_mw.items()}
        remaining_surplus = {k: max(float(v), 0.0) for k, v in surplus_states_mw.items()}
        edge_caps = {k: max(float(v), 0.0) for k, v in daily_edge_capacities_mw.items()}
        executed: List[ProposedTrade] = []
        observed_bottlenecks: List[str] = []

        for trade in proposed_trades:
            buyer = trade.buyer_state
            seller = trade.seller_state
            edge_key = (seller, buyer)
            cap = edge_caps.get(edge_key, 0.0)
            if cap <= 0.0:
                observed_bottlenecks.append(f"{seller}->{buyer}")
                continue

            buyer_need = remaining_deficit.get(buyer, 0.0)
            seller_avail = remaining_surplus.get(seller, 0.0)
            approved = min(float(trade.approved_mw), buyer_need, seller_avail, cap)
            if approved <= 0.0:
                observed_bottlenecks.append(f"{seller}->{buyer}")
                continue

            remaining_deficit[buyer] = max(buyer_need - approved, 0.0)
            remaining_surplus[seller] = max(seller_avail - approved, 0.0)
            edge_caps[edge_key] = max(cap - approved, 0.0)

            executed.append(
                ProposedTrade(
                    buyer_state=buyer,
                    seller_state=seller,
                    requested_mw=float(trade.requested_mw),
                    approved_mw=approved,
                    reason="EXECUTED_DIRECT_NEIGHBOR",
                )
            )

        unserved_before = sum(remaining_deficit.values())
        freq_before = self._frequency_from_deficit(unserved_before, total_grid_capacity_mw)
        freq_after = freq_before
        emergency_shed_total = 0.0
        emergency_triggered = False

        load_shedding: Dict[str, float] = {}
        if freq_before < self.CRITICAL_FREQUENCY_HZ:
            emergency_triggered = True
            allowed_unserved = max(self._allowed_unserved_for_target(total_grid_capacity_mw), 0.0)
            required_shed = max(unserved_before - allowed_unserved, 0.0)
            emergency_shed_total = required_shed

            if required_shed > 0.0:
                # Shed proportionally across states still in deficit.
                total_remaining = max(sum(remaining_deficit.values()), 1e-9)
                for state_id, deficit in remaining_deficit.items():
                    if deficit <= 0.0:
                        continue
                    share = deficit / total_remaining
                    shed = min(deficit, required_shed * share)
                    load_shedding[state_id] = shed
                    remaining_deficit[state_id] = max(deficit - shed, 0.0)

            freq_after = self._frequency_from_deficit(sum(remaining_deficit.values()), total_grid_capacity_mw)
        else:
            # No emergency shedding if frequency remains above critical.
            load_shedding = {}

        return Phase7ExecutionResult(
            executed_trades=executed,
            load_shedding_mw=load_shedding,
            remaining_deficit_mw=remaining_deficit,
            final_surplus_mw=remaining_surplus,
            final_edge_capacities_mw=edge_caps,
            grid_frequency_before_hz=freq_before,
            grid_frequency_after_hz=freq_after,
            emergency_shed_mw=emergency_shed_total,
            frequency_triggered_emergency=emergency_triggered,
            observed_bottlenecks=observed_bottlenecks,
        )
