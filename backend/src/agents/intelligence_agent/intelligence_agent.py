"""Phase 1 deterministic event generator for daily grid events."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import List

from .setup import GridEvent


@dataclass(frozen=True)
class _MockEventTemplate:
    event_name: str
    affected_states: List[str]
    demand_multiplier: float
    supply_multiplier: float
    confidence_score: float


class IntelligenceAgent:
    """
    Phase 1: Event Fetching & Structuring.

    Generates a daily list of 0, 1, or 2 structured grid events using a
    fixed mock catalog. On normal days, this returns an empty list.
    """

    _EVENT_CATALOG: List[_MockEventTemplate] = [
        _MockEventTemplate(
            event_name="UP Heatwave",
            affected_states=["UP"],
            demand_multiplier=1.12,
            supply_multiplier=0.95,
            confidence_score=0.82,
        ),
        _MockEventTemplate(
            event_name="Karnataka Solar Drop",
            affected_states=["KAR"],
            demand_multiplier=1.04,
            supply_multiplier=0.80,
            confidence_score=0.88,
        ),
        _MockEventTemplate(
            event_name="Bihar Coal Strike",
            affected_states=["BHR"],
            demand_multiplier=1.06,
            supply_multiplier=0.76,
            confidence_score=0.79,
        ),
        _MockEventTemplate(
            event_name="WB Monsoon Surge",
            affected_states=["WB"],
            demand_multiplier=1.08,
            supply_multiplier=0.90,
            confidence_score=0.73,
        ),
        _MockEventTemplate(
            event_name="Northern Cooling Wave",
            affected_states=["UP", "BHR"],
            demand_multiplier=0.93,
            supply_multiplier=1.02,
            confidence_score=0.67,
        ),
    ]

    def fetch_daily_events(self) -> List[GridEvent]:
        event_count = random.choice([0, 1, 2])
        if event_count == 0:
            return []

        selected = random.sample(self._EVENT_CATALOG, k=event_count)
        return [
            GridEvent(
                event_name=evt.event_name,
                affected_states=list(evt.affected_states),
                demand_multiplier=evt.demand_multiplier,
                supply_multiplier=evt.supply_multiplier,
                confidence_score=evt.confidence_score,
            )
            for evt in selected
        ]

    def fetch_daily_events_seeded(self, seed: int | None = None) -> List[GridEvent]:
        """
        Deterministic helper for verification/tests without affecting runtime RNG.
        """
        rng = random.Random(seed if seed is not None else int(date.today().strftime("%Y%m%d")))
        event_count = rng.choice([0, 1, 2])
        if event_count == 0:
            return []
        selected = rng.sample(self._EVENT_CATALOG, k=event_count)
        return [
            GridEvent(
                event_name=evt.event_name,
                affected_states=list(evt.affected_states),
                demand_multiplier=evt.demand_multiplier,
                supply_multiplier=evt.supply_multiplier,
                confidence_score=evt.confidence_score,
            )
            for evt in selected
        ]
