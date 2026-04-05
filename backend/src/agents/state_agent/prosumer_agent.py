"""Prosumer bidding agents for Phase 3 reverse-auction DR."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DRBid:
    bidder_name: str
    offered_mw: float
    min_price_inr_per_mw: float


class ProsumerAgent:
    bidder_name = "BaseProsumer"
    base_price_inr_per_mw = 7.0
    max_offer_fraction = 0.40

    def bid(
        self,
        *,
        requested_mw: float,
        max_capacity_mw: float,
        rng: random.Random,
    ) -> DRBid:
        offered = min(float(requested_mw), float(max_capacity_mw) * self.max_offer_fraction)
        noise = rng.uniform(-0.15, 0.15)
        min_price = max(self.base_price_inr_per_mw + noise, 0.0)
        return DRBid(
            bidder_name=self.bidder_name,
            offered_mw=max(offered, 0.0),
            min_price_inr_per_mw=min_price,
        )


class EVFleetProsumer(ProsumerAgent):
    bidder_name = "EV_Fleet"
    base_price_inr_per_mw = 5.6
    max_offer_fraction = 0.55


class IndustrialHVACProsumer(ProsumerAgent):
    bidder_name = "Industrial_HVAC"
    base_price_inr_per_mw = 6.2
    max_offer_fraction = 0.45


class ResidentialSmartGridProsumer(ProsumerAgent):
    bidder_name = "Residential_SmartGrid"
    base_price_inr_per_mw = 6.8
    max_offer_fraction = 0.30


def default_prosumer_stack() -> List[ProsumerAgent]:
    return [
        EVFleetProsumer(),
        IndustrialHVACProsumer(),
        ResidentialSmartGridProsumer(),
    ]
