"""
orchestrator.py
===============
REDESIGNED Intelligence Agent Orchestrator

2-TIER ARCHITECTURE:
====================
TIER 1 (Day 0 - BEFORE simulation loop):
    ForwardMarketPlanner computes 30-day baseline from LightGBM predictions.
    Creates baseline_schedule with scheduled transfers.
    Grid is assumed mathematically balanced.

TIER 2 (Daily - INSIDE simulation loop):
    DeviationDetector fetches events from trusted sources.
    Calculates Anomaly_Delta_MW (deviation from baseline).
    
    If Anomaly_Delta_MW == 0:
        Print "Day [X]: Baseline plan executed flawlessly. No anomalies. Agents dormant."
        Skip to next day.
    
    If Anomaly_Delta_MW > 0:
        Wake UnifiedRoutingOrchestrator with ONLY the Anomaly_Delta_MW.
        Orchestrator passes delta into 3-step waterfall:
            1. Temporal Battery
            2. DR Bounties
            3. Spatial BFS

NO LLM AGENTS - Pure mathematical/deterministic logic with reliable web scraping.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .setup import (
    CITY_REGISTRY,
    BaselineSchedule,
    DailyDeviationResult,
    GridEvent,
    GridMultipliers,
)
from .forward_market_planner import ForwardMarketPlanner
from .deviation_detector import DeviationDetector


class IntelligenceOrchestrator:
    """
    Main orchestrator for the redesigned 2-tier intelligence system.
    
    Usage:
    ------
    # Day 0 - Before simulation loop
    orchestrator = IntelligenceOrchestrator()
    baseline = orchestrator.compute_baseline(predictions_30d, base_generation)
    
    # Daily loop
    for day in range(30):
        result = orchestrator.check_day(day, baseline)
        if result.should_wake_orchestrator:
            # Pass ONLY the anomaly delta to routing
            anomaly_mw = result.anomaly_delta_mw
            # -> Temporal Battery -> DR Bounties -> Spatial BFS
        else:
            print(result.message)  # Agents dormant
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or Path("outputs/context_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # TIER 1 component
        self._planner = ForwardMarketPlanner(cache_dir=self._cache_dir)
        
        # TIER 2 component
        self._detector = DeviationDetector(cache_dir=self._cache_dir)
        
        # State
        self._baseline: Optional[BaselineSchedule] = None
    
    # =========================================================================
    # TIER 1: DAY 0 BASELINE PLANNING
    # =========================================================================
    
    def compute_baseline(
        self,
        predictions_30d: Dict[str, Dict[str, Any]],
        base_generation: Dict[str, float],
        simulation_days: int = 30,
    ) -> BaselineSchedule:
        """
        TIER 1: Compute 30-day baseline BEFORE simulation loop begins.
        
        This should be called ONCE at day 0, before for day in range(1, 31).
        
        Parameters
        ----------
        predictions_30d : Dict[str, Dict[str, Any]]
            30-day LightGBM predictions keyed by state_id.
            Each dict should have 'predicted_mw' or 'adjusted_mw' list.
        base_generation : Dict[str, float]
            Base generation capacity per state in MW.
        simulation_days : int
            Number of days to plan (default 30).
            
        Returns
        -------
        BaselineSchedule
            Complete baseline with deficits/surpluses and scheduled transfers.
        """
        print("\n" + "=" * 70)
        print("TIER 1: FORWARD MARKET PLANNER")
        print("=" * 70)
        
        self._baseline = self._planner.compute_baseline(
            predictions_30d=predictions_30d,
            base_generation=base_generation,
            simulation_days=simulation_days,
        )
        
        # Print summary
        ForwardMarketPlanner.print_baseline_summary(self._baseline)
        
        return self._baseline
    
    def load_cached_baseline(self) -> Optional[BaselineSchedule]:
        """Load baseline from cache if available."""
        self._baseline = self._planner.load_cached_baseline()
        return self._baseline
    
    # =========================================================================
    # TIER 2: DAILY DEVIATION DETECTION
    # =========================================================================
    
    def check_day(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
        force_scrape: bool = False,
    ) -> DailyDeviationResult:
        """
        TIER 2: Check for deviations on a specific day.
        
        This should be called INSIDE the daily simulation loop.
        
        Parameters
        ----------
        day_index : int
            Day index (0-29 for 30-day simulation).
        baseline : BaselineSchedule, optional
            The baseline schedule. If None, uses the one from compute_baseline().
        force_scrape : bool
            Force re-scrape events even if already scraped today.
            
        Returns
        -------
        DailyDeviationResult
            Contains:
            - anomaly_delta_mw: Total deviation from baseline
            - should_wake_orchestrator: True if anomaly_delta_mw > threshold
            - state_anomalies: Per-state deviations
            - message: Human-readable status
        """
        if baseline is None:
            baseline = self._baseline
        
        if baseline is None:
            # No baseline - return dormant result
            return DailyDeviationResult(
                day_index=day_index,
                date_str=date.today().isoformat(),
                anomaly_delta_mw=0.0,
                state_anomalies={},
                detected_anomalies=[],
                should_wake_orchestrator=False,
                message=f"Day {day_index}: No baseline computed. Run compute_baseline() first.",
            )
        
        result = self._detector.detect_deviations(
            day_index=day_index,
            baseline_schedule=baseline,
            force_scrape=force_scrape,
        )
        
        # Print summary
        DeviationDetector.print_deviation_summary(result)
        
        return result
    
    # =========================================================================
    # BACKWARD COMPATIBILITY: Methods for existing code
    # =========================================================================
    
    def get_grid_event_for_day(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
    ) -> Optional[GridEvent]:
        """
        Get GridEvent for backward compatibility with existing simulation code.
        
        Returns None if no significant anomaly detected.
        """
        result = self.check_day(day_index, baseline, force_scrape=False)
        return self._detector.generate_grid_event(result)
    
    def get_grid_multipliers_for_day(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
    ) -> GridMultipliers:
        """
        Get GridMultipliers for backward compatibility.
        """
        result = self.check_day(day_index, baseline, force_scrape=False)
        return self._detector.generate_grid_multipliers(result)
    
    def get_anomaly_delta_mw(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
    ) -> float:
        """
        Get just the anomaly delta MW for a day.
        
        This is what gets passed to UnifiedRoutingOrchestrator
        when should_wake_orchestrator is True.
        """
        result = self.check_day(day_index, baseline, force_scrape=False)
        return result.anomaly_delta_mw
    
    def export_delta_json(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Export Delta calculation as structured JSON.
        
        This JSON file is ONLY created when anomalies are detected.
        If Delta == 0, no file is created (LLMs stay asleep).
        
        Parameters
        ----------
        day_index : int
            Day index (0-29)
        baseline : BaselineSchedule, optional
            Baseline schedule
        output_dir : Path, optional
            Output directory for JSON file
            
        Returns
        -------
        dict
            Delta information (empty dict if no anomaly)
        """
        from datetime import datetime
        
        result = self.check_day(day_index, baseline, force_scrape=False)
        
        # If no anomaly, return empty and don't write file
        if not result.should_wake_orchestrator:
            return {}
        
        # Build delta JSON
        delta_data = {
            "generated_at": datetime.now().isoformat(),
            "day_index": day_index,
            "date": result.date_str,
            "anomaly_delta_mw": result.anomaly_delta_mw,
            "severity": self._get_severity_level(result.anomaly_delta_mw),
            "should_wake_orchestrator": result.should_wake_orchestrator,
            "state_anomalies": result.state_anomalies,
            "detected_events": [
                {
                    "event_type": a.event_type,
                    "affected_states": a.affected_states,
                    "delta_mw": a.anomaly_delta_mw,
                    "confidence": a.confidence,
                    "source": a.source_event.source if a.source_event else "unknown",
                }
                for a in result.detected_anomalies
            ],
            "message": result.message,
            "waterfall_trigger": {
                "step1_temporal_battery": True,
                "step2_economic_dr": True if result.anomaly_delta_mw > 100 else False,
                "step3_spatial_routing": True if result.anomaly_delta_mw > 200 else False,
                "step4_fallback": True if result.anomaly_delta_mw > 500 else False,
            }
        }
        
        # Write file only if anomaly detected
        if output_dir:
            output_path = output_dir / f"delta_{result.date_str}.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            output_path.write_text(json.dumps(delta_data, indent=2), encoding="utf-8")
            print(f"[IntelligenceOrchestrator] Delta JSON -> {output_path}")
        
        return delta_data
    
    def _get_severity_level(self, anomaly_mw: float) -> str:
        """Get severity level from anomaly magnitude."""
        abs_mw = abs(anomaly_mw)
        if abs_mw < 50:
            return "NONE"
        elif abs_mw < 200:
            return "LOW"
        elif abs_mw < 500:
            return "MEDIUM"
        elif abs_mw < 1000:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def get_scheduled_transfers_for_day(
        self,
        day_index: int,
        baseline: Optional[BaselineSchedule] = None,
    ) -> List[Dict[str, Any]]:
        """Get baseline scheduled transfers for a specific day."""
        if baseline is None:
            baseline = self._baseline
        if baseline is None:
            return []
        return self._planner.get_scheduled_transfers_for_day(baseline, day_index)


# =============================================================================
# BACKWARD COMPATIBILITY: SmartGridIntelligenceAgent alias
# =============================================================================

class SmartGridIntelligenceAgent(IntelligenceOrchestrator):
    """
    Backward compatibility alias for existing imports.
    
    The old 7-phase LLM pipeline is replaced with the 2-tier system.
    This class provides the same interface for existing code.
    """
    
    def run_all_regions(
        self,
        predictions_30d: Optional[Dict[str, Dict[str, Any]]] = None,
        base_generation: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run intelligence for all regions.
        
        Returns dict compatible with old NodeResult format.
        """
        # Use defaults if not provided
        if base_generation is None:
            base_generation = {
                state_id: info["typical_peak_mw"]
                for state_id, info in CITY_REGISTRY.items()
            }
        
        if predictions_30d is None:
            # Fallback: use typical peaks as predictions
            predictions_30d = {
                state_id: {
                    "predicted_mw": [info["typical_peak_mw"]] * 30,
                    "adjusted_mw": [info["typical_peak_mw"]] * 30,
                }
                for state_id, info in CITY_REGISTRY.items()
            }
        
        # Compute baseline (TIER 1)
        baseline = self.compute_baseline(
            predictions_30d=predictions_30d,
            base_generation=base_generation,
        )
        
        # Check day 0 (TIER 2)
        deviation = self.check_day(day_index=0, baseline=baseline, force_scrape=True)
        
        # Build result compatible with old format
        results: Dict[str, Dict[str, Any]] = {}
        
        for state_id in CITY_REGISTRY:
            grid_multipliers = self._detector.generate_grid_multipliers(deviation)
            grid_event = self._detector.generate_grid_event(deviation)
            
            results[state_id] = {
                "node_id": state_id,
                "city": CITY_REGISTRY[state_id]["name"],
                "generated_at": date.today().isoformat(),
                "grid_multipliers": asdict(grid_multipliers),
                "phase_1_grid_events": [grid_event.model_dump()] if grid_event else [],
                "deviation_result": {
                    "anomaly_delta_mw": deviation.anomaly_delta_mw,
                    "should_wake_orchestrator": deviation.should_wake_orchestrator,
                    "message": deviation.message,
                },
            }
        
        return results
    
    @staticmethod
    def print_summary_table(results: Dict[str, Dict[str, Any]]) -> None:
        """Print summary table of intelligence results."""
        print("\n" + "=" * 70)
        print("INTELLIGENCE SUMMARY")
        print("=" * 70)
        print(f"{'State':<6} {'Anomaly MW':<12} {'Risk':<10} {'Wake Agents':<12}")
        print("-" * 50)
        
        for state_id, data in results.items():
            gm = data.get("grid_multipliers", {})
            dev = data.get("deviation_result", {})
            
            anomaly = dev.get("anomaly_delta_mw", 0)
            risk = gm.get("demand_spike_risk", "LOW")
            wake = "YES" if dev.get("should_wake_orchestrator", False) else "NO"
            
            print(f"{state_id:<6} {anomaly:>+10.0f} MW {risk:<10} {wake:<12}")
        
        print("=" * 70)
