"""
Phase 6 schema-bound deterministic negotiation with hard safety override.

White Routing Enhancement:
- Accepts transit_risk_map from StimulusRadar
- Sorts paths by risk score (safer paths first)
- High-risk paths are deprioritized, NOT blocked
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..shared.models import ProposedTrade, RiskScore, RiskSeverity


@dataclass(frozen=True)
class NegotiationOutput:
    proposed_trades: List[ProposedTrade]


class Phase6NegotiationAgent:
    """
    Deterministic, schema-bound trade proposal generator.
    Now with White Routing: risk-aware path selection.
    
    Design Decisions (from 15-01 plan):
    - D-06: Sort paths by risk score (ascending = prefer safer paths)
    - D-07: High-risk paths are deprioritized, NOT blocked
    - D-09: Position-weighted risk (endpoints 100%, transit 50%)
    """
    
    # Risk weight by hop position (D-09)
    ENDPOINT_RISK_WEIGHT = 1.0
    TRANSIT_RISK_WEIGHT = 0.5
    
    # Risk penalty multiplier for path scoring
    RISK_PENALTY_FACTOR = 2.0

    def propose_trades(
        self,
        deficit_states_mw: Dict[str, float],
        available_surplus_states_mw: Dict[str, float],
        daily_edge_capacities_mw: Dict[Tuple[str, str], float],
        memory_warnings: Optional[List[str]] = None,
        transit_risk_map: Optional[Dict[str, RiskScore]] = None,
    ) -> NegotiationOutput:
        """
        Generate trade proposals with risk-aware path selection.
        
        Args:
            deficit_states_mw: Dict of state_id -> deficit MW needed
            available_surplus_states_mw: Dict of state_id -> surplus MW available
            daily_edge_capacities_mw: Dict of (seller, buyer) -> edge capacity MW
            memory_warnings: List of memory warnings from Phase 7 (blocked routes)
            transit_risk_map: Dict of state_id -> RiskScore from StimulusRadar
            
        Returns:
            NegotiationOutput with proposed trades sorted by risk (safer first)
        """
        trades: List[ProposedTrade] = []
        warnings = memory_warnings or []
        risk_map = transit_risk_map or {}
        blocked_pairs: set[Tuple[str, str]] = set()

        # Parse memory warnings (existing logic)
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

        # Collect all potential trades with risk scores
        potential_trades: List[Tuple[ProposedTrade, float]] = []  # (trade, risk_score)

        for buyer_state, deficit in sorted(deficit_states_mw.items(), key=lambda x: x[1], reverse=True):
            remaining = max(float(deficit), 0.0)
            if remaining <= 0.0:
                continue

            for seller_state, available in sorted(available_surplus_states_mw.items(), key=lambda x: x[1], reverse=True):
                if seller_state == buyer_state:
                    continue
                if available <= 0.0:
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

                # Calculate path risk score (D-09: position-weighted)
                path_risk = self._calculate_path_risk(
                    seller_state, buyer_state, risk_map
                )

                trade = ProposedTrade(
                    buyer_state=buyer_state,
                    seller_state=seller_state,
                    requested_mw=float(requested_mw),
                    approved_mw=float(approved_mw),
                    reason=(
                        f"RISK_AWARE approved_mw=min(requested_mw, available_surplus, edge_capacity), "
                        f"path_risk={path_risk:.2f}"
                    ),
                )
                potential_trades.append((trade, path_risk))

        # Sort by risk score (ascending = prefer safer paths) per D-06
        potential_trades.sort(key=lambda x: x[1])

        # Accept trades in risk-sorted order, respecting capacity constraints
        remaining_deficits = dict(deficit_states_mw)
        remaining_surplus = dict(available_surplus_states_mw)

        for trade, risk_score in potential_trades:
            buyer = trade.buyer_state
            seller = trade.seller_state
            
            # Check if still needed
            buyer_need = remaining_deficits.get(buyer, 0)
            seller_avail = remaining_surplus.get(seller, 0)
            
            if buyer_need <= 0 or seller_avail <= 0:
                continue
            
            # Recalculate approved amount based on current availability
            actual_approved = min(trade.approved_mw, buyer_need, seller_avail)
            if actual_approved <= 0:
                continue
            
            # Add to accepted trades
            trades.append(ProposedTrade(
                buyer_state=buyer,
                seller_state=seller,
                requested_mw=trade.requested_mw,
                approved_mw=actual_approved,
                reason=trade.reason,
            ))
            
            # Update remaining capacities
            remaining_deficits[buyer] = max(buyer_need - actual_approved, 0)
            remaining_surplus[seller] = max(seller_avail - actual_approved, 0)

        return NegotiationOutput(proposed_trades=trades)
    
    def _calculate_path_risk(
        self,
        seller_state: str,
        buyer_state: str,
        risk_map: Dict[str, RiskScore],
    ) -> float:
        """
        Calculate path risk score using position-weighted formula (D-09).
        
        For direct path (seller → buyer):
        - Seller (endpoint): 100% weight
        - Buyer (endpoint): 100% weight
        
        Total risk = (seller_risk * 1.0 + buyer_risk * 1.0) / 2
        
        For multi-hop paths (future enhancement):
        - Endpoints: 100% weight
        - Transit nodes: 50% weight
        
        Returns:
            float: Path risk score 0.0-1.0 (lower = safer)
        """
        seller_risk = risk_map.get(seller_state, None)
        buyer_risk = risk_map.get(buyer_state, None)
        
        seller_score = seller_risk.total_score if seller_risk else 0.0
        buyer_score = buyer_risk.total_score if buyer_risk else 0.0
        
        # Position-weighted average (D-09)
        path_risk = (
            seller_score * self.ENDPOINT_RISK_WEIGHT +
            buyer_score * self.ENDPOINT_RISK_WEIGHT
        ) / 2
        
        return path_risk
