"""Phase 3 demand-response bounty protocol for StateAgent."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .prosumer_agent import DRBid, ProsumerAgent, default_prosumer_stack


@dataclass(frozen=True)
class DRBountyResult:
    residual_deficit_mw: float
    dr_activated_mw: float
    dr_savings_inr: float
    dr_activated: bool
    clearing_price_inr_per_mw: float
    accepted_bids: List[DRBid]


class Phase3DRBountyAgent:
    """
    Activates DR when imports are more expensive than DR clearing.
    """

    DEFAULT_DR_FRACTION_CAP = 0.10

    def __init__(self, prosumers: List[ProsumerAgent] | None = None):
        self._prosumers = prosumers or default_prosumer_stack()

    def evaluate(
        self,
        deficit_mw: float,
        current_import_tariff: float,
        dr_clearing_price: float,
        total_capacity_mw: float,
        max_dr_capacity_mw: float | None = None,
        auction_seed: int | None = None,
    ) -> DRBountyResult:
        deficit = max(float(deficit_mw), 0.0)
        if deficit <= 0.0:
            return DRBountyResult(
                residual_deficit_mw=0.0,
                dr_activated_mw=0.0,
                dr_savings_inr=0.0,
                dr_activated=False,
                clearing_price_inr_per_mw=0.0,
                accepted_bids=[],
            )

        cap = (
            float(max_dr_capacity_mw)
            if max_dr_capacity_mw is not None
            else float(total_capacity_mw) * self.DEFAULT_DR_FRACTION_CAP
        )
        cap = max(cap, 0.0)

        if float(current_import_tariff) <= float(dr_clearing_price):
            return DRBountyResult(
                residual_deficit_mw=deficit,
                dr_activated_mw=0.0,
                dr_savings_inr=0.0,
                dr_activated=False,
                clearing_price_inr_per_mw=0.0,
                accepted_bids=[],
            )

        # Reverse-auction DR bounties:
        # buy cheapest bids first until deficit resolved, DR cap exhausted,
        # or interstate import is cheaper.
        rng = random.Random(auction_seed)
        bids: List[DRBid] = []
        for prosumer in self._prosumers:
            bid = prosumer.bid(
                requested_mw=deficit,
                max_capacity_mw=cap,
                rng=rng,
            )
            if bid.offered_mw > 0.0:
                bids.append(bid)

        bids.sort(key=lambda b: b.min_price_inr_per_mw)

        remaining_deficit = deficit
        remaining_cap = cap
        activated_total = 0.0
        accepted: List[DRBid] = []
        clearing_price = 0.0

        for bid in bids:
            if remaining_deficit <= 0.0 or remaining_cap <= 0.0:
                break
            if bid.min_price_inr_per_mw > float(current_import_tariff):
                break

            take_mw = min(bid.offered_mw, remaining_deficit, remaining_cap)
            if take_mw <= 0.0:
                continue

            accepted.append(
                DRBid(
                    bidder_name=bid.bidder_name,
                    offered_mw=take_mw,
                    min_price_inr_per_mw=bid.min_price_inr_per_mw,
                )
            )
            activated_total += take_mw
            remaining_deficit -= take_mw
            remaining_cap -= take_mw
            clearing_price = max(clearing_price, bid.min_price_inr_per_mw)

        residual = max(remaining_deficit, 0.0)
        # Savings benchmark against importing at interstate tariff.
        savings = activated_total * max(float(current_import_tariff) - clearing_price, 0.0)

        return DRBountyResult(
            residual_deficit_mw=residual,
            dr_activated_mw=activated_total,
            dr_savings_inr=savings,
            dr_activated=activated_total > 0.0,
            clearing_price_inr_per_mw=clearing_price,
            accepted_bids=accepted,
        )
