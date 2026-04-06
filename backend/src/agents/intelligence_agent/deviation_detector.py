"""
deviation_detector.py
=====================
TIER 2: REAL-TIME DEVIATION LOOP

This runs INSIDE the daily simulation loop. For each day it:
1. Fetches events from trusted sources (via EventScraper)
2. Compares actual conditions against baseline
3. Calculates Anomaly_Delta_MW (deviation from baseline)
4. Returns whether orchestrator should wake up

Key Logic:
- If Anomaly_Delta_MW == 0: "Baseline plan executed flawlessly. Agents dormant."
- If Anomaly_Delta_MW > 0: Wake UnifiedRoutingOrchestrator with ONLY the delta

The orchestrator then passes ONLY the Anomaly_Delta_MW into the strict
3-step waterfall: Temporal Battery -> DR Bounties -> Spatial BFS
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .setup import (
    BaselineSchedule,
    StateBaseline,
    ScrapedEvent,
    GridAnomaly,
    DailyDeviationResult,
    GridEvent,
    GridMultipliers,
    CITY_REGISTRY,
)
from .event_scraper import EventScraper


class DeviationDetector:
    """
    Detects deviations from the baseline schedule using real-world events.
    
    This is the "intelligence" layer that decides whether agents need to wake up.
    If everything matches baseline predictions, agents stay dormant.
    """
    
    # Anomaly thresholds
    MIN_ANOMALY_MW = 50.0       # Ignore deviations below 50 MW
    HIGH_ANOMALY_MW = 500.0     # High severity above 500 MW
    CRITICAL_ANOMALY_MW = 1000.0  # Critical above 1000 MW
    
    # Event impact multipliers (conservative estimates)
    EVENT_IMPACT_MULTIPLIERS = {
        "outage": 1.0,           # Direct MW impact if mentioned
        "weather": 0.05,         # 5% of state typical peak
        "supply_drop": 0.08,     # 8% of state typical peak
        "demand_spike": 0.06,    # 6% of state typical peak
        "political": 0.03,       # 3% of state typical peak (holidays/elections)
        "capacity_addition": -0.05,  # Negative = helps (new capacity)
        "general": 0.02,         # 2% conservative estimate
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or Path("outputs/context_cache")
        self._scraper = EventScraper(cache_dir=self._cache_dir / "events")
        self._last_scrape_date: Optional[str] = None
        self._cached_events: List[ScrapedEvent] = []
    
    def detect_deviations(
        self,
        day_index: int,
        baseline_schedule: BaselineSchedule,
        force_scrape: bool = False,
    ) -> DailyDeviationResult:
        """
        Detect deviations from baseline for a specific day.
        
        Parameters
        ----------
        day_index : int
            Day index (0 = today, 1 = tomorrow, etc.)
        baseline_schedule : BaselineSchedule
            The TIER 1 baseline from ForwardMarketPlanner
        force_scrape : bool
            Force re-scrape even if already scraped today
            
        Returns
        -------
        DailyDeviationResult
            Contains anomaly_delta_mw and whether to wake orchestrator
        """
        today = date.today()
        date_str = today.isoformat()
        
        # Scrape events (once per day unless forced)
        if force_scrape or self._last_scrape_date != date_str:
            self._cached_events = self._scraper.scrape_all_feeds()
            self._cached_events = self._scraper.filter_grid_relevant(self._cached_events)
            self._scraper.save_events_to_cache(self._cached_events)
            self._last_scrape_date = date_str
            print(f"[DeviationDetector] Grid-relevant events: {len(self._cached_events)}")
        
        # Get baseline for this day
        day_baselines = self._get_day_baselines(baseline_schedule, day_index)
        
        if not day_baselines:
            return DailyDeviationResult(
                day_index=day_index,
                date_str=date_str,
                anomaly_delta_mw=0.0,
                state_anomalies={},
                detected_anomalies=[],
                should_wake_orchestrator=False,
                message=f"Day {day_index}: No baseline data. Using default plan.",
            )
        
        # Analyze events and calculate anomalies
        anomalies = self._analyze_events_for_anomalies(
            self._cached_events,
            day_baselines,
        )
        
        # Calculate total anomaly
        state_anomalies: Dict[str, float] = {}
        total_anomaly = 0.0
        
        for anomaly in anomalies:
            for state_id in anomaly.affected_states:
                if state_id not in state_anomalies:
                    state_anomalies[state_id] = 0.0
                state_anomalies[state_id] += anomaly.anomaly_delta_mw
                total_anomaly += anomaly.anomaly_delta_mw
        
        # Round to avoid floating point noise
        total_anomaly = round(total_anomaly, 2)
        state_anomalies = {k: round(v, 2) for k, v in state_anomalies.items()}
        
        # Determine if we should wake orchestrator
        should_wake = abs(total_anomaly) >= self.MIN_ANOMALY_MW
        
        # Generate message
        if total_anomaly == 0 or not should_wake:
            message = f"Day {day_index}: Baseline plan executed flawlessly. No anomalies. Agents dormant."
        else:
            severity = self._get_severity(total_anomaly)
            message = f"Day {day_index}: {severity} anomaly detected. Anomaly_Delta_MW = {total_anomaly:+.0f} MW. Waking orchestrator."
        
        return DailyDeviationResult(
            day_index=day_index,
            date_str=date_str,
            anomaly_delta_mw=total_anomaly,
            state_anomalies=state_anomalies,
            detected_anomalies=anomalies,
            should_wake_orchestrator=should_wake,
            message=message,
        )
    
    def _get_day_baselines(
        self,
        schedule: BaselineSchedule,
        day_index: int,
    ) -> Dict[str, StateBaseline]:
        """Get baseline for all states on a specific day."""
        result = {}
        for state_id, baselines in schedule.daily_baselines.items():
            if day_index < len(baselines):
                result[state_id] = baselines[day_index]
        return result
    
    def _analyze_events_for_anomalies(
        self,
        events: List[ScrapedEvent],
        day_baselines: Dict[str, StateBaseline],
    ) -> List[GridAnomaly]:
        """
        Analyze events and convert to GridAnomaly objects.
        
        This is the core intelligence - determining actual MW impact
        from event descriptions without hallucinating.
        """
        anomalies: List[GridAnomaly] = []
        
        for event in events:
            # Detect affected states
            affected_states = self._scraper.detect_affected_states(event)
            
            if not affected_states:
                # If no specific state mentioned, could be national
                # Skip for now - focus on state-specific events
                continue
            
            # Classify event type
            event_type = self._scraper.classify_event_type(event)
            
            # Estimate MW impact
            explicit_mw = self._scraper.estimate_mw_impact(event)
            
            if explicit_mw > 0:
                # Use explicit MW if mentioned in text
                total_impact = explicit_mw
            else:
                # Estimate based on event type and state size
                multiplier = self.EVENT_IMPACT_MULTIPLIERS.get(event_type, 0.02)
                total_impact = 0.0
                
                for state_id in affected_states:
                    if state_id in CITY_REGISTRY:
                        typical_peak = CITY_REGISTRY[state_id]["typical_peak_mw"]
                        total_impact += typical_peak * multiplier
            
            # Skip negligible impacts
            if total_impact < self.MIN_ANOMALY_MW / 2:
                continue
            
            # Calculate confidence based on source
            confidence = self._calculate_confidence(event)
            
            anomaly = GridAnomaly(
                event_type=event_type,
                description=event.title[:200],
                affected_states=affected_states,
                anomaly_delta_mw=round(total_impact, 2),
                confidence=confidence,
                source_events=[event],
                detected_at=datetime.now().isoformat(),
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_confidence(self, event: ScrapedEvent) -> float:
        """Calculate confidence score based on source reliability."""
        source = event.source.lower()
        
        # Official grid sources = highest confidence
        if any(s in source for s in ["nldc", "nrldc", "wrldc", "srldc", "erldc", "grid-india"]):
            return 0.95
        # Government sources = high confidence
        elif "pib" in source:
            return 0.90
        # Established energy news = good confidence
        elif "et energy" in source or "economic times" in source:
            return 0.80
        # Other trusted sources
        else:
            return 0.70
    
    def _get_severity(self, anomaly_mw: float) -> str:
        """Get severity level string."""
        abs_mw = abs(anomaly_mw)
        if abs_mw >= self.CRITICAL_ANOMALY_MW:
            return "CRITICAL"
        elif abs_mw >= self.HIGH_ANOMALY_MW:
            return "HIGH"
        elif abs_mw >= self.MIN_ANOMALY_MW:
            return "MEDIUM"
        else:
            return "LOW"
    
    def generate_grid_event(
        self,
        deviation: DailyDeviationResult,
    ) -> Optional[GridEvent]:
        """
        Convert deviation result to GridEvent for backward compatibility.
        
        This bridges the new system to existing downstream code.
        """
        if not deviation.should_wake_orchestrator:
            return None
        
        # Find the most significant anomaly
        if not deviation.detected_anomalies:
            return None
        
        primary_anomaly = max(
            deviation.detected_anomalies,
            key=lambda a: abs(a.anomaly_delta_mw),
        )
        
        # Calculate multipliers based on anomaly
        base_demand = sum(
            CITY_REGISTRY[s]["typical_peak_mw"]
            for s in primary_anomaly.affected_states
            if s in CITY_REGISTRY
        )
        
        if base_demand > 0:
            demand_mult = 1.0 + (primary_anomaly.anomaly_delta_mw / base_demand)
        else:
            demand_mult = 1.0
        
        # Supply multiplier (inverse if supply drop)
        if primary_anomaly.event_type in ["outage", "supply_drop"]:
            supply_mult = max(0.5, 1.0 - (primary_anomaly.anomaly_delta_mw / base_demand)) if base_demand > 0 else 0.9
        else:
            supply_mult = 1.0
        
        return GridEvent(
            event_name=primary_anomaly.description,
            affected_states=primary_anomaly.affected_states,
            demand_multiplier=round(min(1.5, max(0.5, demand_mult)), 3),
            supply_multiplier=round(min(1.2, max(0.5, supply_mult)), 3),
            confidence_score=primary_anomaly.confidence,
        )
    
    def generate_grid_multipliers(
        self,
        deviation: DailyDeviationResult,
    ) -> GridMultipliers:
        """
        Generate GridMultipliers for backward compatibility.
        """
        if not deviation.should_wake_orchestrator:
            return GridMultipliers(
                pre_event_hoard=False,
                temperature_anomaly=0.0,
                economic_demand_multiplier=1.0,
                generation_capacity_multiplier=1.0,
                demand_spike_risk="LOW",
                supply_shortfall_risk="LOW",
                seven_day_demand_forecast_mw_delta=0,
                confidence=0.9,
                key_driver="Baseline on track",
                reasoning="No significant deviations from baseline detected.",
                severity_level=1,
            )
        
        # Calculate from anomalies
        total_anomaly = deviation.anomaly_delta_mw
        severity = self._get_severity(total_anomaly)
        
        # Demand spike risk
        if total_anomaly > self.CRITICAL_ANOMALY_MW:
            demand_risk = "CRITICAL"
            severity_level = 5
        elif total_anomaly > self.HIGH_ANOMALY_MW:
            demand_risk = "HIGH"
            severity_level = 4
        elif total_anomaly > self.MIN_ANOMALY_MW:
            demand_risk = "MEDIUM"
            severity_level = 3
        else:
            demand_risk = "LOW"
            severity_level = 1
        
        # Check for supply-side anomalies
        supply_anomalies = [
            a for a in deviation.detected_anomalies
            if a.event_type in ["outage", "supply_drop"]
        ]
        supply_risk = "HIGH" if supply_anomalies else "LOW"
        
        # Pre-event hoard if high-confidence, high-impact event
        should_hoard = (
            severity_level >= 4 and
            any(a.confidence >= 0.8 for a in deviation.detected_anomalies)
        )
        
        # Key driver
        if deviation.detected_anomalies:
            key_driver = deviation.detected_anomalies[0].description[:100]
        else:
            key_driver = "Unknown deviation"
        
        return GridMultipliers(
            pre_event_hoard=should_hoard,
            temperature_anomaly=0.0,  # Would need weather data
            economic_demand_multiplier=1.0 + (total_anomaly / 10000),  # Rough estimate
            generation_capacity_multiplier=0.95 if supply_anomalies else 1.0,
            demand_spike_risk=demand_risk,
            supply_shortfall_risk=supply_risk,
            seven_day_demand_forecast_mw_delta=int(total_anomaly),
            confidence=max((a.confidence for a in deviation.detected_anomalies), default=0.5),
            key_driver=key_driver,
            reasoning=deviation.message,
            severity_level=severity_level,
        )
    
    @staticmethod
    def print_deviation_summary(deviation: DailyDeviationResult) -> None:
        """Print human-readable deviation summary."""
        print("\n" + "-" * 60)
        print(f"TIER 2: DEVIATION DETECTOR - DAY {deviation.day_index}")
        print("-" * 60)
        print(deviation.message)
        
        if deviation.should_wake_orchestrator:
            print(f"\nState-level anomalies:")
            for state_id, mw in deviation.state_anomalies.items():
                print(f"  {state_id}: {mw:+.0f} MW")
            
            print(f"\nDetected anomalies ({len(deviation.detected_anomalies)}):")
            for anomaly in deviation.detected_anomalies[:5]:  # Show top 5
                print(f"  [{anomaly.event_type.upper()}] {anomaly.description[:60]}...")
                print(f"    Impact: {anomaly.anomaly_delta_mw:+.0f} MW | Confidence: {anomaly.confidence:.0%}")
        
        print("-" * 60)
