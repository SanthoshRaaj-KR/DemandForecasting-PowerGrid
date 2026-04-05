"""Phase 8 metrics and XAI daily summary formatter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Phase8Summary:
    total_deficit_mw: float
    deficit_resolved_via_dr_mw: float
    money_saved_by_dr_inr: float
    power_imported_mw: float
    forced_load_shedding_mw: float
    summary_line: str


class Phase8XAIAgent:
    """
    Builds explicit KPI summary required for console and artifacts.
    """

    def build_summary(
        self,
        *,
        initial_deficit_by_state_mw: Dict[str, float],
        dr_activated_total_mw: float,
        dr_savings_total_inr: float,
        executed_import_total_mw: float,
        load_shedding_total_mw: float,
    ) -> Phase8Summary:
        total_deficit = sum(max(float(v), 0.0) for v in initial_deficit_by_state_mw.values())
        summary_line = (
            f"[Total Deficit]={total_deficit:.2f} MW | "
            f"[Deficit resolved via DR]={float(dr_activated_total_mw):.2f} MW | "
            f"[Money Saved by DR]={float(dr_savings_total_inr):.2f} INR | "
            f"[Power Imported]={float(executed_import_total_mw):.2f} MW | "
            f"[Forced Load Shedding]={float(load_shedding_total_mw):.2f} MW"
        )
        return Phase8Summary(
            total_deficit_mw=total_deficit,
            deficit_resolved_via_dr_mw=float(dr_activated_total_mw),
            money_saved_by_dr_inr=float(dr_savings_total_inr),
            power_imported_mw=float(executed_import_total_mw),
            forced_load_shedding_mw=float(load_shedding_total_mw),
            summary_line=summary_line,
        )
