"""
Orchestration Engine
=====================
Unified 4-stage orchestration loop with cost accounting and strict Delta triggers.

Usage:
    engine = OrchestrationEngine(config)
    result = engine.run_day(date="2026-04-01", day_index=0)
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from .contracts import (
    OrchestratorState,
    WakeDecision,
    StageResult,
    DailyOrchestrationResult,
    CostMetrics,
    OrchestrationConfig,
    OrchestrationContext,
)

# Import stage agents
from ..agents.intelligence_agent.orchestrator import IntelligenceOrchestrator
from ..agents.intelligence_agent.forward_market_planner import ForwardMarketPlanner
from ..agents.routing_agent.unified_routing_orchestrator import UnifiedRoutingOrchestrator

logger = logging.getLogger(__name__)


# Keep backward compatibility with existing code
@dataclass(frozen=True)
class DayOrchestrationSummary:
    """Legacy summary for backward compatibility."""
    day_index: int
    llm_agents_enabled: bool
    anomaly_detected: bool
    max_state_imbalance_mw: float
    estimated_baseline_cost: float
    estimated_llm_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_index": self.day_index,
            "llm_agents_enabled": self.llm_agents_enabled,
            "anomaly_detected": self.anomaly_detected,
            "max_state_imbalance_mw": self.max_state_imbalance_mw,
            "estimated_baseline_cost": self.estimated_baseline_cost,
            "estimated_llm_cost": self.estimated_llm_cost,
        }


class OrchestrationEngine:
    """
    Unified orchestration engine for the 4-stage pipeline.
    
    Stage 1: A Priori Baseline (ForwardMarketPlanner)
    Stage 2: Intelligence/Delta Detection (IntelligenceOrchestrator)
    Stage 3: Waterfall Resolution (UnifiedRoutingOrchestrator)
    Stage 4: Memory & XAI Export (short-term memory write)
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        self.config = config or OrchestrationConfig()
        self._baseline_planner = ForwardMarketPlanner()
        self._intelligence = IntelligenceOrchestrator()
        self._waterfall = UnifiedRoutingOrchestrator()
        self._daily_results: List[DailyOrchestrationResult] = []
    
    # =========================================================================
    # LEGACY METHOD: Backward compatibility with existing main.py
    # =========================================================================
    
    def evaluate_day(
        self,
        *,
        day_index: int,
        baseline_day: Dict[str, Any] | None,
        delta_event: Dict[str, Any] | None,
        baseline_unit_cost: float = 1.0,
        llm_unit_cost: float = 10.0,
    ) -> DayOrchestrationSummary:
        """Legacy method for backward compatibility."""
        llm_from_baseline = bool((baseline_day or {}).get("llm_agents_enabled", False))
        anomaly_detected = bool(delta_event)
        llm_agents_enabled = llm_from_baseline or anomaly_detected
        imbalance = float((baseline_day or {}).get("max_state_imbalance_mw", 0.0) or 0.0)

        estimated_baseline_cost = baseline_unit_cost
        estimated_llm_cost = baseline_unit_cost + (llm_unit_cost if llm_agents_enabled else 0.0)

        return DayOrchestrationSummary(
            day_index=day_index,
            llm_agents_enabled=llm_agents_enabled,
            anomaly_detected=anomaly_detected,
            max_state_imbalance_mw=imbalance,
            estimated_baseline_cost=estimated_baseline_cost,
            estimated_llm_cost=estimated_llm_cost,
        )
    
    # =========================================================================
    # NEW UNIFIED ORCHESTRATION METHODS
    # =========================================================================
    
    def run_day(
        self,
        date: str,
        day_index: int,
        memory_warnings: Optional[List[str]] = None,
    ) -> DailyOrchestrationResult:
        """
        Run the complete 4-stage orchestration for a single day.
        
        Returns DailyOrchestrationResult with all stage outputs and cost metrics.
        """
        start_time = time.time()
        
        ctx = OrchestrationContext(
            config=self.config,
            current_date=date,
            day_index=day_index,
            state=OrchestratorState.IDLE,
            memory_warnings=memory_warnings or [],
        )
        
        try:
            # Stage 1: Baseline (only on day 0 or if not cached)
            if day_index == 0:
                ctx = self._run_stage_1_baseline(ctx)
            
            # Stage 2: Intelligence & Delta Detection
            ctx = self._run_stage_2_intelligence(ctx)
            
            # Stage 3: Waterfall Resolution (only if WAKE)
            if ctx.wake_decision == WakeDecision.WAKE:
                ctx = self._run_stage_3_waterfall(ctx)
            
            # Stage 4: Memory Write & XAI Export
            ctx = self._run_stage_4_memory(ctx)
            
            ctx.state = OrchestratorState.COMPLETE
            
        except Exception as e:
            ctx.state = OrchestratorState.ERROR
            ctx.error = str(e)
            logger.error(f"Orchestration failed on {date}: {e}")
        
        total_duration = (time.time() - start_time) * 1000
        
        # Calculate cost metrics
        cost_metrics = self._calculate_cost_metrics(ctx)
        
        result = DailyOrchestrationResult(
            date=date,
            day_index=day_index,
            wake_decision=ctx.wake_decision,
            stages_completed=ctx.stage_results,
            total_duration_ms=total_duration,
            cost_metrics=cost_metrics,
            summary=self._generate_summary(ctx),
        )
        
        self._daily_results.append(result)
        return result
    
    def run_simulation(
        self,
        start_date: str = "2026-04-01",
        num_days: int = 30,
    ) -> List[DailyOrchestrationResult]:
        """
        Run orchestration for multiple days.
        
        Returns list of daily results.
        """
        results = []
        current_date = datetime.fromisoformat(start_date)
        memory_warnings: List[str] = []
        
        for day_idx in range(num_days):
            date_str = current_date.strftime("%Y-%m-%d")
            
            result = self.run_day(
                date=date_str,
                day_index=day_idx,
                memory_warnings=memory_warnings,
            )
            results.append(result)
            
            # Collect memory warnings for next day
            if result.stages_completed:
                for stage in result.stages_completed:
                    if stage.stage_name == "memory" and stage.output:
                        new_warnings = stage.output.get("warnings", [])
                        memory_warnings.extend(new_warnings)
                        # Keep only last 3 warnings (72-hour window)
                        memory_warnings = memory_warnings[-3:]
            
            current_date += timedelta(days=1)
        
        return results
    
    def _run_stage_1_baseline(self, ctx: OrchestrationContext) -> OrchestrationContext:
        """Stage 1: Generate 30-day baseline schedule."""
        ctx.state = OrchestratorState.RUNNING_BASELINE
        start = time.time()
        
        try:
            # Try to load cached baseline first
            schedule = self._baseline_planner.load_cached_baseline()
            if schedule is None:
                # Generate new baseline (requires predictions)
                logger.info("No cached baseline found, using default schedule")
                schedule = {}
            ctx.baseline_schedule = schedule
            
            ctx.stage_results.append(StageResult(
                stage_number=1,
                stage_name="baseline",
                success=True,
                duration_ms=(time.time() - start) * 1000,
                output={"schedule_days": len(schedule) if schedule else 0},
            ))
        except Exception as e:
            ctx.stage_results.append(StageResult(
                stage_number=1,
                stage_name="baseline",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                output={},
                error=str(e),
            ))
        
        return ctx
    
    def _run_stage_2_intelligence(self, ctx: OrchestrationContext) -> OrchestrationContext:
        """Stage 2: Detect anomalies and make wake/sleep decision."""
        ctx.state = OrchestratorState.RUNNING_INTELLIGENCE
        start = time.time()
        
        try:
            # Check for deviations on this day
            deviation = self._intelligence.check_day(
                day_index=ctx.day_index,
                baseline=None,  # Uses cached baseline
                force_scrape=False,
            )
            
            ctx.intelligence_output = {
                "anomaly_delta_mw": deviation.anomaly_delta_mw,
                "should_wake": deviation.should_wake_orchestrator,
                "message": deviation.message,
                "state_anomalies": deviation.state_anomalies,
            }
            
            # Make wake/sleep decision
            total_delta_mw = abs(deviation.anomaly_delta_mw)
            
            if total_delta_mw > ctx.config.delta_wake_threshold_mw:
                ctx.wake_decision = WakeDecision.WAKE
                logger.info(f"WAKE: Delta {total_delta_mw:.1f}MW > threshold {ctx.config.delta_wake_threshold_mw}MW")
            else:
                ctx.wake_decision = WakeDecision.SLEEP
                logger.info(f"SLEEP: Delta {total_delta_mw:.1f}MW <= threshold")
            
            ctx.stage_results.append(StageResult(
                stage_number=2,
                stage_name="intelligence",
                success=True,
                duration_ms=(time.time() - start) * 1000,
                output={
                    "total_delta_mw": total_delta_mw,
                    "wake_decision": ctx.wake_decision.value,
                    "message": deviation.message,
                },
            ))
        except Exception as e:
            # On intelligence failure, default to WAKE for safety
            ctx.wake_decision = WakeDecision.WAKE
            ctx.stage_results.append(StageResult(
                stage_number=2,
                stage_name="intelligence",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                output={},
                error=str(e),
            ))
        
        return ctx
    
    def _run_stage_3_waterfall(self, ctx: OrchestrationContext) -> OrchestrationContext:
        """Stage 3: Run waterfall resolution (Battery → DR → BFS → Fallback)."""
        ctx.state = OrchestratorState.RUNNING_WATERFALL
        start = time.time()
        
        try:
            # Build deficit/surplus from intelligence output
            deficit_states = {}
            surplus_states = {}
            
            if ctx.intelligence_output:
                state_anomalies = ctx.intelligence_output.get("state_anomalies", {})
                for state_id, delta_mw in state_anomalies.items():
                    if delta_mw > 0:
                        deficit_states[state_id] = delta_mw
                    elif delta_mw < 0:
                        surplus_states[state_id] = abs(delta_mw)
            
            # Execute waterfall (using existing demo parameters for battery/edge)
            result = self._waterfall.execute_waterfall(
                deficit_states_mw=deficit_states or {"UP": 50.0},
                surplus_states_mw=surplus_states or {"WB": 30.0},
                battery_soc={"UP": 50.0, "Bihar": 30.0, "WB": 40.0, "Karnataka": 60.0},
                battery_capacity={"UP": 100.0, "Bihar": 100.0, "WB": 100.0, "Karnataka": 100.0},
                daily_edge_capacities_mw={
                    ("WB", "Bihar"): 100.0,
                    ("Bihar", "UP"): 80.0,
                    ("Bihar", "WB"): 100.0,
                    ("UP", "Bihar"): 80.0,
                    ("Karnataka", "WB"): 70.0,
                    ("WB", "Karnataka"): 70.0,
                },
                total_grid_capacity_mw=2000.0,
                dr_clearing_price=6.0,
                day_index=ctx.day_index,
                date_str=ctx.current_date,
            )
            
            ctx.waterfall_result = {
                "total_resolved_mw": result.total_resolved_mw,
                "load_shedding_mw": sum(result.load_shedding_mw.values()),
                "memory_warning": result.memory_warning,
                "waterfall_complete": result.waterfall_complete,
                "steps_executed": len(result.steps_executed),
            }
            
            ctx.stage_results.append(StageResult(
                stage_number=3,
                stage_name="waterfall",
                success=True,
                duration_ms=(time.time() - start) * 1000,
                output=ctx.waterfall_result,
            ))
        except Exception as e:
            ctx.stage_results.append(StageResult(
                stage_number=3,
                stage_name="waterfall",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                output={},
                error=str(e),
            ))
        
        return ctx
    
    def _run_stage_4_memory(self, ctx: OrchestrationContext) -> OrchestrationContext:
        """Stage 4: Write to memory and export XAI ledger."""
        ctx.state = OrchestratorState.RUNNING_MEMORY
        start = time.time()
        
        try:
            # Generate memory warning if there was load shedding
            new_warning = None
            if ctx.waterfall_result:
                shedding = ctx.waterfall_result.get("load_shedding_mw", 0)
                if shedding > 0:
                    new_warning = f"WARNING: Load shedding {shedding:.0f}MW on {ctx.current_date}"
            
            ctx.stage_results.append(StageResult(
                stage_number=4,
                stage_name="memory",
                success=True,
                duration_ms=(time.time() - start) * 1000,
                output={
                    "warnings": [new_warning] if new_warning else [],
                    "memory_buffer_size": len(ctx.memory_warnings) + (1 if new_warning else 0),
                },
            ))
        except Exception as e:
            ctx.stage_results.append(StageResult(
                stage_number=4,
                stage_name="memory",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                output={},
                error=str(e),
            ))
        
        return ctx
    
    def _calculate_cost_metrics(self, ctx: OrchestrationContext) -> CostMetrics:
        """Calculate cost metrics for the day."""
        llm_enabled = ctx.wake_decision == WakeDecision.WAKE
        
        # Estimate costs
        baseline_cost = ctx.config.llm_cost_per_call_inr * ctx.config.baseline_calls_per_day
        actual_cost = baseline_cost if llm_enabled else 0.0
        savings = baseline_cost - actual_cost
        savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0
        
        # Get anomaly magnitude from intelligence stage
        anomaly_mw = 0.0
        for stage in ctx.stage_results:
            if stage.stage_name == "intelligence":
                anomaly_mw = stage.output.get("total_delta_mw", 0)
                break
        
        return CostMetrics(
            date=ctx.current_date,
            llm_agents_enabled=llm_enabled,
            anomaly_detected=llm_enabled,
            anomaly_magnitude_mw=anomaly_mw,
            baseline_cost_inr=baseline_cost,
            actual_cost_inr=actual_cost,
            savings_inr=savings,
            savings_pct=savings_pct,
        )
    
    def _generate_summary(self, ctx: OrchestrationContext) -> str:
        """Generate human-readable summary for the day."""
        if ctx.state == OrchestratorState.ERROR:
            return f"❌ Orchestration failed: {ctx.error}"
        
        decision_emoji = "🟢" if ctx.wake_decision == WakeDecision.SLEEP else "🔴"
        decision_text = "SLEEP (baseline)" if ctx.wake_decision == WakeDecision.SLEEP else "WAKE (anomaly)"
        
        stages_ok = sum(1 for s in ctx.stage_results if s.success)
        stages_total = len(ctx.stage_results)
        
        return f"{decision_emoji} {ctx.current_date}: {decision_text} | Stages: {stages_ok}/{stages_total}"
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get aggregated cost summary across all days."""
        if not self._daily_results:
            return {}
        
        total_baseline = sum(r.cost_metrics.baseline_cost_inr for r in self._daily_results)
        total_actual = sum(r.cost_metrics.actual_cost_inr for r in self._daily_results)
        total_savings = total_baseline - total_actual
        
        wake_days = sum(1 for r in self._daily_results if r.wake_decision == WakeDecision.WAKE)
        sleep_days = len(self._daily_results) - wake_days
        
        return {
            "total_days": len(self._daily_results),
            "wake_days": wake_days,
            "sleep_days": sleep_days,
            "sleep_rate_pct": (sleep_days / len(self._daily_results) * 100),
            "total_baseline_cost_inr": total_baseline,
            "total_actual_cost_inr": total_actual,
            "total_savings_inr": total_savings,
            "savings_pct": (total_savings / total_baseline * 100) if total_baseline > 0 else 0,
        }

