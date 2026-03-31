"""
routing_agent/settlement.py
===========================
Daily settlement and ledger persistence.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any


class SettlementAgent:
    """
    Writes a deterministic daily ledger to state_capacities.json.
    """

    def __init__(self, ledger_path: str | Path = "outputs/state_capacities.json"):
        self.ledger_path = Path(ledger_path)

    def settle_day(
        self,
        env: Any,
        dispatches: list[Any],
        load_shedding: list[dict[str, Any]],
        simulation_date: str | None = None,
    ) -> dict[str, Any]:
        sim_date = simulation_date or date.today().isoformat()

        per_state: dict[str, dict[str, Any]] = {}
        for nid, node in env.nodes.items():
            per_state[nid] = {
                "generation_mw": float(node.generation_mw),
                "adjusted_demand_mw": float(node.adjusted_demand_mw),
                "balance_mw": float(node.raw_balance_mw),
                "battery_soc": float(node.battery.soc) if node.battery else None,
                "battery_charge_mwh": float(node.battery.charge) if node.battery else None,
                "sold_mw": 0.0,
                "bought_mw": 0.0,
                "hoarded_mw": 0.0,
                "load_shed_mw": 0.0,
            }

        for d in dispatches:
            seller = getattr(d, "seller_city_id", None)
            buyer = getattr(d, "buyer_city_id", None)
            mw = float(getattr(d, "transfer_mw", 0.0))
            hour = getattr(d, "dispatch_hour", None)
            if seller in per_state:
                per_state[seller]["sold_mw"] += mw
            if buyer in per_state:
                per_state[buyer]["bought_mw"] += mw
                if hour == 3:
                    per_state[buyer]["hoarded_mw"] += mw

        for ls in load_shedding:
            sid = str(ls.get("state_id", ""))
            if sid in per_state:
                per_state[sid]["load_shed_mw"] += float(ls.get("shed_mw", 0.0))

        payload = {
            "date": sim_date,
            "states": per_state,
            "dispatch_count": len(dispatches),
            "load_shedding_count": len(load_shedding),
        }

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return payload
