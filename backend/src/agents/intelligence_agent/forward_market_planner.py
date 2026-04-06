"""
forward_market_planner.py
=========================
TIER 1: DAY 0 BASELINE PLANNER

This runs BEFORE the simulation loop begins. It:
1. Takes 30-day LightGBM predictions for all states
2. Calculates Base_Deficit and Base_Surplus for each state per day
3. Mathematically resolves deficits using scheduled transfers
4. Creates a baseline_schedule dictionary

After this, the grid is assumed to be mathematically balanced.
The daily simulation loop ONLY handles deviations from this baseline.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .setup import (
    BaselineSchedule,
    StateBaseline,
    BaselineCache,
    CITY_REGISTRY,
)


class ForwardMarketPlanner:
    """
    Computes 30-day baseline schedule from LightGBM predictions.
    
    This is pure mathematical planning - no LLM, no external APIs.
    Just takes predictions and calculates who needs power and who has surplus.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or Path("outputs/context_cache")
        self._cache = BaselineCache(self._cache_dir)
    
    def compute_baseline(
        self,
        predictions_30d: Dict[str, Dict[str, Any]],
        base_generation: Dict[str, float],
        simulation_days: int = 30,
    ) -> BaselineSchedule:
        """
        Compute 30-day baseline schedule from ML predictions.
        
        Parameters
        ----------
        predictions_30d : Dict[str, Dict[str, Any]]
            LightGBM 30-day predictions keyed by state_id.
            Each value should have 'predicted_mw' or 'adjusted_mw' list.
        base_generation : Dict[str, float]
            Base generation capacity per state in MW.
        simulation_days : int
            Number of days to plan (default 30).
            
        Returns
        -------
        BaselineSchedule
            Complete baseline with per-state daily deficits/surpluses
            and scheduled transfers to balance the grid.
        """
        today = date.today()
        states = list(CITY_REGISTRY.keys())
        
        # Build daily baselines per state
        daily_baselines: Dict[str, List[StateBaseline]] = {s: [] for s in states}
        
        total_deficit = 0.0
        total_surplus = 0.0
        
        for day_idx in range(simulation_days):
            day_date = (today + timedelta(days=day_idx)).isoformat()
            
            for state_id in states:
                # Get predicted demand for this day
                state_preds = predictions_30d.get(state_id, {})
                pred_list = state_preds.get("adjusted_mw") or state_preds.get("predicted_mw", [])
                
                if day_idx < len(pred_list):
                    predicted_demand = float(pred_list[day_idx])
                else:
                    # Fallback: use typical peak as baseline
                    predicted_demand = float(CITY_REGISTRY[state_id]["typical_peak_mw"])
                
                # Get base supply for this state
                base_supply = float(base_generation.get(state_id, predicted_demand))
                
                # Calculate deficit/surplus
                balance = base_supply - predicted_demand
                
                if balance < 0:
                    deficit = abs(balance)
                    surplus = 0.0
                    total_deficit += deficit
                else:
                    deficit = 0.0
                    surplus = balance
                    total_surplus += surplus
                
                baseline = StateBaseline(
                    state_id=state_id,
                    day_index=day_idx,
                    date_str=day_date,
                    predicted_demand_mw=round(predicted_demand, 2),
                    base_supply_mw=round(base_supply, 2),
                    base_deficit_mw=round(deficit, 2),
                    base_surplus_mw=round(surplus, 2),
                )
                daily_baselines[state_id].append(baseline)
        
        # Schedule transfers to resolve deficits
        scheduled_transfers = self._resolve_deficits(daily_baselines, simulation_days)
        
        # Check if grid is balanced
        is_balanced = total_deficit <= total_surplus * 1.05  # 5% tolerance
        
        schedule = BaselineSchedule(
            generated_at=today.isoformat(),
            states=states,
            daily_baselines=daily_baselines,
            scheduled_transfers=scheduled_transfers,
            total_deficit_mw=round(total_deficit, 2),
            total_surplus_mw=round(total_surplus, 2),
            is_balanced=is_balanced,
        )
        
        # Cache the baseline
        self._cache.save(schedule)
        
        return schedule
    
    def _resolve_deficits(
        self,
        daily_baselines: Dict[str, List[StateBaseline]],
        simulation_days: int,
    ) -> List[Dict[str, Any]]:
        """
        Mathematically schedule transfers from surplus to deficit states.
        
        Simple greedy algorithm:
        1. For each day, identify deficit and surplus states
        2. Match deficit to nearest surplus (by capacity)
        3. Schedule transfer to cover as much deficit as possible
        """
        transfers: List[Dict[str, Any]] = []
        
        for day_idx in range(simulation_days):
            # Get today's deficits and surpluses
            deficits: List[Tuple[str, float]] = []
            surpluses: List[Tuple[str, float]] = []
            
            for state_id, baselines in daily_baselines.items():
                if day_idx < len(baselines):
                    bl = baselines[day_idx]
                    if bl.base_deficit_mw > 0:
                        deficits.append((state_id, bl.base_deficit_mw))
                    elif bl.base_surplus_mw > 0:
                        surpluses.append((state_id, bl.base_surplus_mw))
            
            # Sort by magnitude (largest first for efficient matching)
            deficits.sort(key=lambda x: x[1], reverse=True)
            surpluses.sort(key=lambda x: x[1], reverse=True)
            
            # Greedy matching
            remaining_surpluses = {s: amt for s, amt in surpluses}
            
            for deficit_state, deficit_mw in deficits:
                needed = deficit_mw
                
                for surplus_state in list(remaining_surpluses.keys()):
                    if needed <= 0:
                        break
                    
                    available = remaining_surpluses[surplus_state]
                    if available <= 0:
                        continue
                    
                    transfer_mw = min(needed, available)
                    
                    transfers.append({
                        "day_index": day_idx,
                        "from_state": surplus_state,
                        "to_state": deficit_state,
                        "transfer_mw": round(transfer_mw, 2),
                        "type": "baseline_scheduled",
                    })
                    
                    remaining_surpluses[surplus_state] -= transfer_mw
                    needed -= transfer_mw
        
        return transfers
    
    def get_baseline_for_day(
        self,
        schedule: BaselineSchedule,
        day_index: int,
    ) -> Dict[str, StateBaseline]:
        """
        Get baseline for a specific day across all states.
        
        Returns dict keyed by state_id.
        """
        result = {}
        for state_id, baselines in schedule.daily_baselines.items():
            if day_index < len(baselines):
                result[state_id] = baselines[day_index]
        return result
    
    def get_scheduled_transfers_for_day(
        self,
        schedule: BaselineSchedule,
        day_index: int,
    ) -> List[Dict[str, Any]]:
        """Get all scheduled transfers for a specific day."""
        return [
            t for t in schedule.scheduled_transfers
            if t["day_index"] == day_index
        ]
    
    def load_cached_baseline(self) -> Optional[BaselineSchedule]:
        """Load baseline from cache if available."""
        return self._cache.load()
    
    @staticmethod
    def print_baseline_summary(schedule: BaselineSchedule) -> None:
        """Print human-readable summary of baseline schedule."""
        print("\n" + "=" * 70)
        print("TIER 1: FORWARD MARKET PLANNER - BASELINE SCHEDULE")
        print("=" * 70)
        print(f"Generated: {schedule.generated_at}")
        print(f"States: {', '.join(schedule.states)}")
        print(f"Total Deficit: {schedule.total_deficit_mw:,.0f} MW")
        print(f"Total Surplus: {schedule.total_surplus_mw:,.0f} MW")
        print(f"Grid Balanced: {'YES ✓' if schedule.is_balanced else 'NO ✗'}")
        print(f"Scheduled Transfers: {len(schedule.scheduled_transfers)}")
        print("-" * 70)
        
        # Summary per state
        print("\nPer-State 30-Day Summary:")
        print(f"{'State':<6} {'Avg Demand':<12} {'Avg Supply':<12} {'Avg Deficit':<12} {'Avg Surplus':<12}")
        print("-" * 54)
        
        for state_id in schedule.states:
            baselines = schedule.daily_baselines[state_id]
            avg_demand = sum(b.predicted_demand_mw for b in baselines) / len(baselines)
            avg_supply = sum(b.base_supply_mw for b in baselines) / len(baselines)
            avg_deficit = sum(b.base_deficit_mw for b in baselines) / len(baselines)
            avg_surplus = sum(b.base_surplus_mw for b in baselines) / len(baselines)
            
            print(f"{state_id:<6} {avg_demand:>10,.0f} MW {avg_supply:>10,.0f} MW {avg_deficit:>10,.0f} MW {avg_surplus:>10,.0f} MW")
        
        print("=" * 70)
