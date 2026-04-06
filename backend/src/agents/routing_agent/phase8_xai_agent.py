"""
Phase 8 Metrics and XAI Daily Summary Formatter.

SELF-HEALING MEMORY (Feature #4 - Stage 4)
==========================================
At the end of each day, this agent analyzes failures and generates:
1. A human-readable summary line for the audit ledger
2. A memory warning string for the 3-day sliding window
3. Diagnostic insights for the Recursive LLM Parameter Autopsy

This enables Agentic Learning WITHOUT Neural Networks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Phase8Summary:
    """Daily summary with KPIs and self-healing insights."""
    total_deficit_mw: float
    deficit_resolved_via_dr_mw: float
    money_saved_by_dr_inr: float
    power_imported_mw: float
    forced_load_shedding_mw: float
    summary_line: str
    memory_warning: Optional[str] = None
    self_healing_insights: Optional[Dict[str, str]] = None


@dataclass
class FailureAnalysis:
    """Analysis of a single failure event."""
    failure_type: str  # THERMAL_CAP, BATTERY_DEPLETED, DR_INSUFFICIENT, etc.
    affected_states: List[str]
    magnitude_mw: float
    root_cause: str
    recommended_action: str


class Phase8XAIAgent:
    """
    Builds explicit KPI summary required for console and artifacts.
    
    SELF-HEALING CAPABILITIES:
    - Generates memory warnings for the 3-day sliding window
    - Produces diagnostic insights for monthly parameter autopsy
    - Identifies failure patterns for agentic learning
    """
    
    # Thresholds for failure classification
    THERMAL_WARNING_PCT = 0.90  # Edge at 90%+ utilization
    DR_INSUFFICIENT_PCT = 0.50  # DR covered less than 50% of potential
    BATTERY_CRITICAL_SOC = 10.0  # SOC below 10 MW is critical

    def build_summary(
        self,
        *,
        initial_deficit_by_state_mw: Dict[str, float],
        dr_activated_total_mw: float,
        dr_savings_total_inr: float,
        executed_import_total_mw: float,
        load_shedding_total_mw: float,
        edge_utilization: Optional[Dict[Tuple[str, str], float]] = None,
        battery_soc_after: Optional[Dict[str, float]] = None,
        failed_trades: Optional[List[Dict]] = None,
    ) -> Phase8Summary:
        """
        Build daily summary with self-healing insights.
        
        Parameters
        ----------
        initial_deficit_by_state_mw : Dict[str, float]
            Starting deficit by state
        dr_activated_total_mw : float
            Total MW resolved via Demand Response
        dr_savings_total_inr : float
            Money saved by using DR instead of imports
        executed_import_total_mw : float
            Total MW imported from other states
        load_shedding_total_mw : float
            Total MW of forced load shedding
        edge_utilization : Optional[Dict[Tuple[str, str], float]]
            Edge utilization percentages (for thermal analysis)
        battery_soc_after : Optional[Dict[str, float]]
            Battery SOC after day (for depletion analysis)
        failed_trades : Optional[List[Dict]]
            Trades that failed to execute
            
        Returns
        -------
        Phase8Summary
            Complete summary with self-healing insights
        """
        total_deficit = sum(max(float(v), 0.0) for v in initial_deficit_by_state_mw.values())
        
        summary_line = (
            f"[Total Deficit]={total_deficit:.2f} MW | "
            f"[Deficit resolved via DR]={float(dr_activated_total_mw):.2f} MW | "
            f"[Money Saved by DR]={float(dr_savings_total_inr):.2f} INR | "
            f"[Power Imported]={float(executed_import_total_mw):.2f} MW | "
            f"[Forced Load Shedding]={float(load_shedding_total_mw):.2f} MW"
        )
        
        # Generate self-healing insights
        memory_warning = None
        insights = None
        
        if load_shedding_total_mw > 0:
            # Analyze failures to generate memory warning
            failures = self._analyze_failures(
                initial_deficit_by_state_mw,
                load_shedding_total_mw,
                edge_utilization,
                battery_soc_after,
                failed_trades,
            )
            
            memory_warning = self._generate_memory_warning(failures)
            insights = self._generate_healing_insights(failures, total_deficit)
        
        return Phase8Summary(
            total_deficit_mw=total_deficit,
            deficit_resolved_via_dr_mw=float(dr_activated_total_mw),
            money_saved_by_dr_inr=float(dr_savings_total_inr),
            power_imported_mw=float(executed_import_total_mw),
            forced_load_shedding_mw=float(load_shedding_total_mw),
            summary_line=summary_line,
            memory_warning=memory_warning,
            self_healing_insights=insights,
        )
    
    def _analyze_failures(
        self,
        deficit_by_state: Dict[str, float],
        load_shedding_mw: float,
        edge_utilization: Optional[Dict[Tuple[str, str], float]],
        battery_soc: Optional[Dict[str, float]],
        failed_trades: Optional[List[Dict]],
    ) -> List[FailureAnalysis]:
        """Analyze failures to identify root causes."""
        failures = []
        
        # Check for thermal bottlenecks
        if edge_utilization:
            for edge, utilization in edge_utilization.items():
                if utilization >= self.THERMAL_WARNING_PCT:
                    failures.append(FailureAnalysis(
                        failure_type="THERMAL_BOTTLENECK",
                        affected_states=list(edge),
                        magnitude_mw=load_shedding_mw * utilization,
                        root_cause=f"{edge[0]}-{edge[1]} line at {utilization*100:.0f}% capacity",
                        recommended_action=f"Route via alternate path avoiding {edge[0]}-{edge[1]}",
                    ))
        
        # Check for battery depletion
        if battery_soc:
            for state, soc in battery_soc.items():
                if soc <= self.BATTERY_CRITICAL_SOC and state in deficit_by_state:
                    failures.append(FailureAnalysis(
                        failure_type="BATTERY_DEPLETED",
                        affected_states=[state],
                        magnitude_mw=deficit_by_state.get(state, 0),
                        root_cause=f"{state} battery depleted to {soc:.0f} MW",
                        recommended_action=f"Pre-charge {state} battery during low-demand hours",
                    ))
        
        # Check for failed trades
        if failed_trades:
            for trade in failed_trades:
                failures.append(FailureAnalysis(
                    failure_type="TRADE_FAILED",
                    affected_states=[trade.get("buyer", "unknown")],
                    magnitude_mw=trade.get("amount", 0),
                    root_cause=trade.get("reason", "Unknown"),
                    recommended_action="Review edge capacity allocation",
                ))
        
        # If no specific failures found, create generic analysis
        if not failures and load_shedding_mw > 0:
            deficit_states = [s for s, d in deficit_by_state.items() if d > 0]
            failures.append(FailureAnalysis(
                failure_type="INSUFFICIENT_RESOURCES",
                affected_states=deficit_states,
                magnitude_mw=load_shedding_mw,
                root_cause="Combined battery+DR+transmission insufficient",
                recommended_action="Increase DR bounty prices or battery capacity",
            ))
        
        return failures
    
    def _generate_memory_warning(self, failures: List[FailureAnalysis]) -> str:
        """Generate a concise memory warning for the 3-day sliding window."""
        if not failures:
            return ""
        
        # Prioritize by magnitude
        failures.sort(key=lambda f: f.magnitude_mw, reverse=True)
        top_failure = failures[0]
        
        # Generate memory warning (max ~80 chars for readability)
        warning = f"{top_failure.failure_type}: {top_failure.root_cause}"
        
        if len(warning) > 80:
            warning = warning[:77] + "..."
        
        return warning
    
    def _generate_healing_insights(
        self,
        failures: List[FailureAnalysis],
        total_deficit: float,
    ) -> Dict[str, str]:
        """
        Generate healing insights for the monthly parameter autopsy.
        
        These insights will be read by the LLM Overseer at month-end
        to autonomously adjust hyperparameters.
        """
        insights = {
            "failure_count": str(len(failures)),
            "total_deficit_mw": f"{total_deficit:.0f}",
            "primary_failure_type": failures[0].failure_type if failures else "NONE",
        }
        
        # Aggregate failure types
        failure_types = {}
        for f in failures:
            failure_types[f.failure_type] = failure_types.get(f.failure_type, 0) + 1
        insights["failure_breakdown"] = str(failure_types)
        
        # Generate parameter adjustment recommendations
        recommendations = []
        for f in failures:
            if f.failure_type == "THERMAL_BOTTLENECK":
                recommendations.append("INCREASE edge_capacity_buffer_pct by 10%")
            elif f.failure_type == "BATTERY_DEPLETED":
                recommendations.append("INCREASE battery_precharge_threshold by 20%")
            elif f.failure_type == "TRADE_FAILED":
                recommendations.append("REDUCE max_trade_size_mw by 15%")
            elif f.failure_type == "INSUFFICIENT_RESOURCES":
                recommendations.append("INCREASE dr_bounty_price by 25%")
        
        insights["recommended_param_changes"] = "; ".join(set(recommendations))
        
        return insights
    
    def generate_autopsy_report(
        self,
        monthly_summaries: List[Phase8Summary],
        month_str: str,
    ) -> Dict:
        """
        Generate the monthly autopsy report for LLM parameter optimization.
        
        This is the data that feeds into Feature #1: 
        Recursive LLM Parameter Autopsy (Zero-Shot Self-Healing).
        
        Parameters
        ----------
        monthly_summaries : List[Phase8Summary]
            All daily summaries for the month
        month_str : str
            Month identifier (e.g., "2025-01")
            
        Returns
        -------
        Dict
            Autopsy report with aggregated insights and recommendations
        """
        total_deficit = sum(s.total_deficit_mw for s in monthly_summaries)
        total_shedding = sum(s.forced_load_shedding_mw for s in monthly_summaries)
        total_dr = sum(s.deficit_resolved_via_dr_mw for s in monthly_summaries)
        total_imports = sum(s.power_imported_mw for s in monthly_summaries)
        
        # Aggregate failure insights
        all_recommendations = []
        failure_counts = {}
        for s in monthly_summaries:
            if s.self_healing_insights:
                primary = s.self_healing_insights.get("primary_failure_type", "NONE")
                failure_counts[primary] = failure_counts.get(primary, 0) + 1
                if "recommended_param_changes" in s.self_healing_insights:
                    all_recommendations.append(s.self_healing_insights["recommended_param_changes"])
        
        # Deduplicate and prioritize recommendations
        recommendation_counts = {}
        for rec in all_recommendations:
            for r in rec.split("; "):
                if r:
                    recommendation_counts[r] = recommendation_counts.get(r, 0) + 1
        
        # Sort by frequency
        sorted_recs = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "month": month_str,
            "total_days": len(monthly_summaries),
            "total_deficit_mw": total_deficit,
            "total_load_shedding_mw": total_shedding,
            "total_dr_resolved_mw": total_dr,
            "total_imports_mw": total_imports,
            "shedding_rate_pct": (total_shedding / total_deficit * 100) if total_deficit > 0 else 0,
            "failure_breakdown": failure_counts,
            "top_recommendations": [
                {"action": rec, "frequency": count}
                for rec, count in sorted_recs[:5]
            ],
            "autopsy_summary": self._generate_autopsy_summary(
                total_shedding, total_deficit, failure_counts, sorted_recs
            ),
        }
    
    def _generate_autopsy_summary(
        self,
        total_shedding: float,
        total_deficit: float,
        failure_counts: Dict[str, int],
        recommendations: List[Tuple[str, int]],
    ) -> str:
        """Generate human-readable autopsy summary for LLM Overseer."""
        shedding_pct = (total_shedding / total_deficit * 100) if total_deficit > 0 else 0
        
        top_failure = max(failure_counts.items(), key=lambda x: x[1])[0] if failure_counts else "NONE"
        top_rec = recommendations[0][0] if recommendations else "No changes needed"
        
        return (
            f"Monthly autopsy: {shedding_pct:.1f}% of deficit resulted in load shedding. "
            f"Primary failure mode: {top_failure}. "
            f"Recommended parameter change: {top_rec}."
        )
