"""
routing_agent/dispatcher.py
===========================
Dispatcher Agent: topology and physics gatekeeper.
"""

from __future__ import annotations

import logging
from typing import Any

from .dlr_calculator import calculate_effective_capacity

logger = logging.getLogger(__name__)


class DispatcherAgent:
    """
    Enforces spatial connectivity and DLR-based transfer caps.
    """

    def __init__(self, grid_env: Any):
        self.grid_env = grid_env

    def get_candidate_paths(self, seller_id: str, buyer_id: str) -> list[Any]:
        if hasattr(self.grid_env, "get_paths"):
            return self.grid_env.get_paths(seller_id, buyer_id)
        return []

    def apply_topology_and_dlr(
        self,
        seller_id: str,
        buyer_id: str,
        requested_mw: float,
        seller_ctx: dict[str, Any],
        buyer_ctx: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Returns dispatcher constraints for one potential trade leg.
        """
        paths = self.get_candidate_paths(seller_id, buyer_id)
        if not paths:
            return {
                "allowed": False,
                "reason": f"No physical connection {seller_id}->{buyer_id}",
                "line_cap_mw": 0.0,
                "selected_path": None,
                "dlr_applied": False,
                "effective_capacity_mw": 0.0,
            }

        # Use path with lowest base physical cost for cap estimation.
        selected_path = min(paths, key=lambda p: float(p.total_cost()))
        effective_capacity, dlr_applied = calculate_effective_capacity(
            selected_path,
            seller_ctx,
            buyer_ctx,
        )

        hard_cap = max(0.0, min(float(requested_mw), float(effective_capacity)))

        log_line = (
            f"PHASE_3_DISPATCHER seller={seller_id} buyer={buyer_id} requested={requested_mw:.2f} "
            f"path={getattr(selected_path, 'description', str(selected_path))} "
            f"effective_capacity={effective_capacity:.2f} hard_cap={hard_cap:.2f} "
            f"dlr_applied={dlr_applied}"
        )
        logger.info(log_line)

        return {
            "allowed": hard_cap > 0.0,
            "reason": "OK" if hard_cap > 0.0 else "Line cap reduced to zero",
            "line_cap_mw": hard_cap,
            "selected_path": selected_path,
            "dlr_applied": dlr_applied,
            "effective_capacity_mw": float(effective_capacity),
            "log": log_line,
        }

    @staticmethod
    def negotiation_prompt(
        seller_id: str,
        buyer_id: str,
        buyer_deficit_mw: float,
        line_cap_mw: float,
    ) -> str:
        return (
            f"You are {seller_id}. {buyer_id} needs {buyer_deficit_mw:.2f} MW. "
            f"Dispatcher has hard-capped this interconnector at {line_cap_mw:.2f} MW. "
            "Offer at most the cap."
        )
