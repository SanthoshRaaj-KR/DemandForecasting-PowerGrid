"""
state_agent/state_agent.py
==========================
Deterministic state-node logic for calibration, intelligence injection,
and order generation.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.intelligence_agent.setup import GridEvent
from ..shared.models import Order, OrderType, RiskLevel, StatePosition
from ..shared.constants import (
    BASELINE_ASK_PRICE,
    DISTRESSED_ASK_PRICE,
    BASELINE_BID_PRICE,
    PANIC_BID_PRICE,
    BATTERY_FULL_SOC_THRESHOLD,
)
from .phase2_ingestion_agent import Phase2IngestionAgent
from .phase3_dr_bounty_agent import Phase3DRBountyAgent
from .phase4_lookahead_agent import Phase4LookaheadAgent

logger = logging.getLogger(__name__)


class StateAgent:
    """
    Local trading agent for one state node.

    Backward-compatible constructor fields (`net_mw`, `battery_soc`, `llm_context`)
    are preserved for existing market order generation.
    """

    def __init__(
        self,
        city_id: str,
        net_mw: float,
        battery_soc: float,
        llm_context: dict[str, Any],
    ) -> None:
        self.city_id = city_id
        self.net_mw = net_mw
        self.battery_soc = battery_soc
        self.llm_context = llm_context

        self.hoard_flag: bool = bool(
            llm_context.get("hoard_flag", llm_context.get("pre_event_hoard", False))
        )
        self.demand_spike_risk: RiskLevel = self._parse_risk(
            llm_context.get("demand_spike_risk", "LOW")
        )
        self.temperature_anomaly: float = float(llm_context.get("temperature_anomaly", 0.0))
        self._phase2_ingestion_agent = Phase2IngestionAgent()
        self._phase3_dr_bounty_agent = Phase3DRBountyAgent()
        self._phase4_lookahead_agent = Phase4LookaheadAgent()

    # ------------------------------------------------------------------
    # Phase-1 + Phase-2 deterministic math
    # ------------------------------------------------------------------

    @staticmethod
    def calibrate_baseline_supply(
        forecast_7d_mw: list[float],
        safety_buffer: float = 1.05,
    ) -> float:
        if not forecast_7d_mw:
            return 0.0
        avg_forecast = sum(float(v) for v in forecast_7d_mw) / float(len(forecast_7d_mw))
        return avg_forecast * float(safety_buffer)

    def evaluate_state_position(
        self,
        forecast_7d_mw: list[float],
        todays_demand_forecast_mw: float,
        intelligence: dict[str, Any],
        safety_buffer: float = 1.05,
        pre_event_hoard_hour: int = 3,
        normal_dispatch_hour: int = 14,
    ) -> StatePosition:
        """
        Implements exact daily math sequence:
        1) baseline supply calibration from 7-day forecast
        2) intelligence multiplier injection
        3) mathematically verified net deficit/surplus
        4) temporal pre-event dispatch hint
        """
        edm = float(
            intelligence.get(
                "economic_demand_multiplier",
                intelligence.get("demand_multiplier", 1.0),
            )
        )
        gmm = float(
            intelligence.get(
                "generation_multiplier",
                intelligence.get("generation_capacity_multiplier", 1.0),
            )
        )
        pre_event_hoard = bool(
            intelligence.get("pre_event_hoard", intelligence.get("hoard_flag", False))
        )

        avg_forecast = (
            sum(float(v) for v in forecast_7d_mw) / float(len(forecast_7d_mw))
            if forecast_7d_mw
            else 0.0
        )
        baseline_supply = self.calibrate_baseline_supply(forecast_7d_mw, safety_buffer=safety_buffer)

        adjusted_demand = float(todays_demand_forecast_mw) * edm
        adjusted_supply = baseline_supply * gmm
        net = adjusted_supply - adjusted_demand
        deficit = abs(net) if net < 0 else 0.0
        surplus = net if net > 0 else 0.0

        # --- Selfish Seller / Self-Preservation Logic ---
        future_hoard_triggered = False
        future_deficit_mw = 0.0
        hoard_day = 0
        if forecast_7d_mw and len(forecast_7d_mw) > 1 and surplus > 0:
            # Check for massive deficit in the next 1-6 days
            for i, future_demand in enumerate(forecast_7d_mw[1:], start=1):
                # Using today's supply as baseline expected future supply
                day_net = adjusted_supply - future_demand
                if day_net < 0 and abs(day_net) > (0.05 * adjusted_supply):  # > 5% deficit
                    future_hoard_triggered = True
                    future_deficit_mw = abs(day_net)
                    hoard_day = i
                    break
        
        if future_hoard_triggered:
            pre_event_hoard = True
            # Force net to 0, hoarding the surplus
            surplus = 0.0
            net = 0.0

        dispatch_hour_hint = pre_event_hoard_hour if pre_event_hoard else normal_dispatch_hour

        phase_log = [
            (
                f"CALIBRATION | Baseline set to {baseline_supply:.0f} MW | "
                f"avg_forecast={avg_forecast:.2f} safety_buffer={safety_buffer:.2f}"
            ),
            (
                f"AUDIT | Net position: {net:+.1f} MW | "
                f"demand_adj={edm:.3f} supply_adj={gmm:.3f} "
                f"deficit={deficit:.1f} surplus={surplus:.1f}"
            ),
            (
                f"TEMPORAL | Dispatch window: {dispatch_hour_hint:02d}:00 | "
                f"pre_event_hoard={pre_event_hoard}"
            ),
        ]

        if future_hoard_triggered:
            phase_log.append(
                f"SELF-PRESERVATION | Hoarding for Day {hoard_day} | "
                f"future_deficit={future_deficit_mw:.1f} MW. Surplus retained for local security."
            )
            intelligence["pre_event_hoard"] = True
            intelligence["hoard_day"] = hoard_day

        return StatePosition(
            state_id=self.city_id,
            forecast_7d_mw=[float(v) for v in forecast_7d_mw],
            avg_forecast_mw=avg_forecast,
            baseline_supply_mw=baseline_supply,
            todays_demand_forecast_mw=float(todays_demand_forecast_mw),
            adjusted_demand_mw=adjusted_demand,
            adjusted_supply_mw=adjusted_supply,
            net_position_mw=net,
            deficit_mw=deficit,
            surplus_mw=surplus,
            economic_demand_multiplier=edm,
            generation_multiplier=gmm,
            pre_event_hoard=pre_event_hoard,
            dispatch_hour_hint=dispatch_hour_hint,
            reasoning=str(intelligence.get("narrative", intelligence.get("reasoning", ""))),
            phase_log=phase_log,
        )

    def evaluate_state_position_with_events(
        self,
        forecast_7d_mw: list[float],
        todays_demand_forecast_mw: float,
        hardcoded_supply_mw: float,
        grid_events: list[GridEvent],
        current_import_tariff: float = 10.0,
        dr_clearing_price: float = 6.0,
        max_dr_capacity_mw: float | None = None,
        pre_event_hoard_hour: int = 3,
        normal_dispatch_hour: int = 14,
    ) -> StatePosition:
        """
        Phase 2 + 3 flow:
        - Phase 2: event-aware adjusted supply/demand and net position.
        - Phase 3: DR bounty protocol on deficits.
        """
        ingestion = self._phase2_ingestion_agent.evaluate(
            state_id=self.city_id,
            lightgbm_base_demand_mw=float(todays_demand_forecast_mw),
            hardcoded_supply_mw=float(hardcoded_supply_mw),
            grid_events=grid_events,
        )

        dr = self._phase3_dr_bounty_agent.evaluate(
            deficit_mw=ingestion.deficit_mw,
            current_import_tariff=float(current_import_tariff),
            dr_clearing_price=float(dr_clearing_price),
            total_capacity_mw=float(hardcoded_supply_mw),
            max_dr_capacity_mw=max_dr_capacity_mw,
            auction_seed=abs(hash((self.city_id, int(todays_demand_forecast_mw), int(hardcoded_supply_mw)))) % (2**31),
        )

        deficit_after_dr = max(dr.residual_deficit_mw, 0.0)
        surplus = ingestion.surplus_mw
        net_after_dr = surplus - deficit_after_dr
        dispatch_hour_hint = pre_event_hoard_hour if self.hoard_flag else normal_dispatch_hour

        event_name = ingestion.event_applied.event_name if ingestion.event_applied is not None else "No event"
        phase_log = [
            (
                f"PHASE2 | event={event_name} demand_mult={ingestion.demand_multiplier:.3f} "
                f"supply_mult={ingestion.supply_multiplier:.3f}"
            ),
            (
                f"PHASE2 | demand={ingestion.adjusted_demand_mw:.2f}MW "
                f"supply={ingestion.adjusted_supply_mw:.2f}MW net={ingestion.net_position_mw:+.2f}MW "
                f"is_deficit={ingestion.is_deficit}"
            ),
            (
                f"PHASE3 | tariff={current_import_tariff:.2f} dr_price={dr_clearing_price:.2f} "
                f"dr_activated={dr.dr_activated} dr_mw={dr.dr_activated_mw:.2f} "
                f"residual_deficit={deficit_after_dr:.2f} savings={dr.dr_savings_inr:.2f} "
                f"clearing_price={dr.clearing_price_inr_per_mw:.2f}"
            ),
        ]
        if dr.accepted_bids:
            phase_log.append(
                "PHASE3_AUCTION_BIDS | "
                + "; ".join(
                    f"{bid.bidder_name}:{bid.offered_mw:.2f}MW@{bid.min_price_inr_per_mw:.2f}"
                    for bid in dr.accepted_bids
                )
            )

        avg_forecast = (
            sum(float(v) for v in forecast_7d_mw) / float(len(forecast_7d_mw))
            if forecast_7d_mw
            else float(todays_demand_forecast_mw)
        )
        pre_event_hoard = bool(self.hoard_flag)

        return StatePosition(
            state_id=self.city_id,
            forecast_7d_mw=[float(v) for v in forecast_7d_mw] if forecast_7d_mw else [float(todays_demand_forecast_mw)] * 7,
            avg_forecast_mw=avg_forecast,
            baseline_supply_mw=float(hardcoded_supply_mw),
            todays_demand_forecast_mw=float(todays_demand_forecast_mw),
            adjusted_demand_mw=ingestion.adjusted_demand_mw,
            adjusted_supply_mw=ingestion.adjusted_supply_mw,
            net_position_mw=net_after_dr,
            deficit_mw=deficit_after_dr,
            surplus_mw=surplus,
            economic_demand_multiplier=ingestion.demand_multiplier,
            generation_multiplier=ingestion.supply_multiplier,
            pre_event_hoard=pre_event_hoard,
            dispatch_hour_hint=dispatch_hour_hint,
            is_deficit=deficit_after_dr > 0.0,
            dr_savings_inr=dr.dr_savings_inr,
            dr_activated_mw=dr.dr_activated_mw,
            current_import_tariff=float(current_import_tariff),
            dr_clearing_price=float(dr.clearing_price_inr_per_mw),
            reasoning=str(self.llm_context.get("narrative", self.llm_context.get("reasoning", ""))),
            phase_log=phase_log,
        )

    def apply_phase4_lookahead(
        self,
        *,
        state_position: StatePosition,
        forecast_7d_mw: list[float],
        hardcoded_supply_mw: float,
        confidence_score: float,
        tolerance_mw: float = 500.0,
    ) -> StatePosition:
        result = self._phase4_lookahead_agent.evaluate(
            is_currently_surplus=float(state_position.surplus_mw) > 0.0,
            forecast_7d_mw=forecast_7d_mw,
            hardcoded_supply_mw=float(hardcoded_supply_mw),
            confidence_score=float(confidence_score),
            tolerance_mw=float(tolerance_mw),
        )

        if result.hoard_mode:
            state_position.pre_event_hoard = True
            state_position.surplus_mw = 0.0
            state_position.net_position_mw = -max(float(state_position.deficit_mw), 0.0)
            state_position.phase_log.append(
                (
                    f"PHASE4 | hoard_mode=True expected_risk={result.expected_risk_mw:.2f}MW "
                    f"max_future_deficit={result.max_future_deficit_mw:.2f}MW > tolerance={tolerance_mw:.2f}MW | "
                    "surplus locked from market"
                )
            )
        else:
            state_position.phase_log.append(
                (
                    f"PHASE4 | hoard_mode=False expected_risk={result.expected_risk_mw:.2f}MW "
                    f"max_future_deficit={result.max_future_deficit_mw:.2f}MW"
                )
            )

        return state_position

    def negotiation_line(
        self,
        state_position: StatePosition,
        counterparty: str,
        hard_cap_mw: float,
        role: str,
    ) -> str:
        """
        One-sentence LLM-style negotiation line grounded in math constraints.
        """
        if role.upper() == "BUYER":
            return (
                f"REQUEST | {self.city_id} buying {state_position.deficit_mw:.1f} MW | "
                f"deficit_risk={self.demand_spike_risk.value} dispatch_window={state_position.dispatch_hour_hint:02d}:00 "
                f"dispatcher_cap={hard_cap_mw:.1f} MW"
            )
        return (
            f"OFFER | {self.city_id} selling {hard_cap_mw:.1f} MW | "
            f"available_surplus={state_position.surplus_mw:.1f} MW under current constraint"
        )

    # ------------------------------------------------------------------
    # Backward-compatible order generation
    # ------------------------------------------------------------------

    def generate_order(self) -> Order | None:
        if self.net_mw > 0:
            return self._build_sell_order()
        if self.net_mw < 0:
            return self._build_buy_order()
        logger.info("[%s] Net MW is zero; no order generated.", self.city_id)
        return None

    def _build_sell_order(self) -> Order:
        battery_full = self.battery_soc > BATTERY_FULL_SOC_THRESHOLD

        if battery_full:
            price = DISTRESSED_ASK_PRICE
            reason = (
                f"Battery SoC {self.battery_soc:.1f}% (> {BATTERY_FULL_SOC_THRESHOLD}%). "
                f"Distressed ask {price:.2f} INR/MW."
            )
        else:
            price = BASELINE_ASK_PRICE
            reason = (
                f"Normal surplus {self.net_mw:.1f} MW with battery {self.battery_soc:.1f}%. "
                f"Standard ask {price:.2f} INR/MW."
            )

        return Order(
            city_id=self.city_id,
            order_type=OrderType.SELL,
            quantity_mw=self.net_mw,
            price_per_mw=price,
            reason=reason,
        )

    def _build_buy_order(self) -> Order:
        quantity = abs(self.net_mw)
        panic = self.hoard_flag or (self.demand_spike_risk == RiskLevel.CRITICAL)

        if panic:
            price = PANIC_BID_PRICE
            triggers = []
            if self.hoard_flag:
                triggers.append("pre_event_hoard=True")
            if self.demand_spike_risk == RiskLevel.CRITICAL:
                triggers.append("demand_spike_risk=CRITICAL")
            reason = (
                f"PANIC BID due to {', '.join(triggers)}. "
                f"Max bid {price:.2f} INR/MW."
            )
        else:
            price = BASELINE_BID_PRICE
            reason = (
                f"Normal deficit {quantity:.1f} MW, risk {self.demand_spike_risk.value}. "
                f"Standard bid {price:.2f} INR/MW."
            )

        return Order(
            city_id=self.city_id,
            order_type=OrderType.BUY,
            quantity_mw=quantity,
            price_per_mw=price,
            reason=reason,
        )

    @staticmethod
    def _parse_risk(raw: str) -> RiskLevel:
        try:
            return RiskLevel(str(raw).upper())
        except (ValueError, AttributeError):
            logger.warning("Unrecognized demand_spike_risk '%s'; defaulting to LOW.", raw)
            return RiskLevel.LOW

    def __repr__(self) -> str:
        return (
            f"<StateAgent city={self.city_id} net_mw={self.net_mw:+.1f} "
            f"soc={self.battery_soc:.1f}% hoard={self.hoard_flag} "
            f"risk={self.demand_spike_risk.value}>"
        )
