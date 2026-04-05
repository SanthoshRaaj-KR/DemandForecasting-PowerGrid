"""Phase 6 schema-bound deterministic negotiation with hard safety override."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..shared.models import ProposedTrade


@dataclass(frozen=True)
class NegotiationOutput:
    proposed_trades: List[ProposedTrade]


class Phase6NegotiationAgent:
    """
    Deterministic, schema-bound trade proposal generator.
    """

    def propose_trades(
        self,
        deficit_states_mw: Dict[str, float],
        available_surplus_states_mw: Dict[str, float],
        daily_edge_capacities_mw: Dict[Tuple[str, str], float],
        memory_warnings: List[str] | None = None,
    ) -> NegotiationOutput:
        trades: List[ProposedTrade] = []
        warnings = memory_warnings or []
        blocked_pairs: set[Tuple[str, str]] = set()

        for warning in warnings:
            lowered = warning.lower()
            if "warning:" not in lowered:
                continue
            # Format expected from phase7 memory: "WARNING: A->B ...".
            try:
                payload = lowered.split("warning:", 1)[1].strip()
                route_part = payload.split(" ", 1)[0].strip()
                if "->" in route_part:
                    s, b = route_part.split("->", 1)
                    blocked_pairs.add((s.strip().upper(), b.strip().upper()))
            except Exception:
                continue

        for buyer_state, deficit in sorted(deficit_states_mw.items(), key=lambda x: x[1], reverse=True):
            remaining = max(float(deficit), 0.0)
            if remaining <= 0.0:
                continue

            for seller_state, available in sorted(available_surplus_states_mw.items(), key=lambda x: x[1], reverse=True):
                if seller_state == buyer_state:
                    continue
                if available <= 0.0 or remaining <= 0.0:
                    continue
                if (seller_state.upper(), buyer_state.upper()) in blocked_pairs:
                    continue

                edge_cap = float(daily_edge_capacities_mw.get((seller_state, buyer_state), 0.0))
                if edge_cap <= 0.0:
                    continue

                requested_mw = min(remaining, float(available))
                approved_mw = min(requested_mw, float(available), edge_cap)
                if approved_mw <= 0.0:
                    continue

                trades.append(
                    ProposedTrade(
                        buyer_state=buyer_state,
                        seller_state=seller_state,
                        requested_mw=float(requested_mw),
                        approved_mw=float(approved_mw),
                        reason=(
                            "SAFETY_OVERRIDE approved_mw=min(requested_mw, available_surplus, edge_capacity)"
                        ),
                    )
                )

                remaining -= approved_mw
                available_surplus_states_mw[seller_state] = max(float(available_surplus_states_mw[seller_state]) - approved_mw, 0.0)

        return NegotiationOutput(proposed_trades=trades)
