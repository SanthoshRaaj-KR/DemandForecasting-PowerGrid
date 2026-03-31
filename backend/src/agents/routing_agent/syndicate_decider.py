"""
routing_agent/syndicate_decider.py
==================================
Syndicate Decider Agent: final trade approval and load-shedding mandates.
"""

from __future__ import annotations

from typing import Any


class SyndicateDecider:
    """
    National-level verifier that can approve/veto trades and enforce load-shedding.
    """

    def __init__(self, macro_safety_margin_mw: float = 0.0):
        self.macro_safety_margin_mw = float(macro_safety_margin_mw)

    def verify_trade(
        self,
        buyer_id: str,
        seller_id: str,
        requested_mw: float,
        dispatcher_cap_mw: float,
        seller_available_mw: float,
        path: Any,
    ) -> dict[str, Any]:
        approved_mw = min(
            float(requested_mw),
            float(dispatcher_cap_mw),
            float(seller_available_mw),
        )

        if approved_mw <= 0:
            return {
                "approved": False,
                "approved_mw": 0.0,
                "reason": "Rejected: insufficient seller surplus or line cap",
            }

        # Macro-grid conservative condition placeholder.
        # Can be extended with frequency or N-1 checks.
        if approved_mw < self.macro_safety_margin_mw:
            return {
                "approved": False,
                "approved_mw": 0.0,
                "reason": (
                    "Rejected: macro safety margin not satisfied "
                    f"(approved_mw={approved_mw:.2f}, min={self.macro_safety_margin_mw:.2f})"
                ),
            }

        return {
            "approved": True,
            "approved_mw": approved_mw,
            "reason": (
                f"Approved {approved_mw:.2f} MW {seller_id}->{buyer_id} via "
                f"{getattr(path, 'description', str(path))}"
            ),
        }

    def mandate_load_shedding(
        self,
        buyer_id: str,
        unresolved_deficit_mw: float,
        dispatch_hour: int | None,
    ) -> dict[str, Any]:
        shed = max(float(unresolved_deficit_mw), 0.0)
        return {
            "state_id": buyer_id,
            "shed_mw": shed,
            "level": "LEVEL_1",
            "dispatch_hour": dispatch_hour,
            "reason": (
                f"Controlled Load-Shedding mandated for {buyer_id}: "
                f"unresolved deficit {shed:.2f} MW after safe routing exhaustion"
            ),
        }
