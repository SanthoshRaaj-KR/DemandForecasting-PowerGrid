"""Phase 4 Bayesian strategic lookahead for surplus protection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LookaheadResult:
    hoard_mode: bool
    max_future_deficit_mw: float
    expected_risk_mw: float


class Phase4LookaheadAgent:
    """
    Surplus-only future-risk scan:
    Expected_Risk = max_future_deficit * confidence_score.
    """

    def evaluate(
        self,
        *,
        is_currently_surplus: bool,
        forecast_7d_mw: list[float],
        hardcoded_supply_mw: float,
        confidence_score: float,
        tolerance_mw: float = 500.0,
    ) -> LookaheadResult:
        if not is_currently_surplus:
            return LookaheadResult(hoard_mode=False, max_future_deficit_mw=0.0, expected_risk_mw=0.0)

        max_future_deficit = 0.0
        for predicted_demand in forecast_7d_mw[:7]:
            deficit = max(float(predicted_demand) - float(hardcoded_supply_mw), 0.0)
            if deficit > max_future_deficit:
                max_future_deficit = deficit

        expected_risk = max_future_deficit * max(min(float(confidence_score), 1.0), 0.0)
        hoard_mode = expected_risk > float(tolerance_mw)

        return LookaheadResult(
            hoard_mode=hoard_mode,
            max_future_deficit_mw=max_future_deficit,
            expected_risk_mw=expected_risk,
        )
