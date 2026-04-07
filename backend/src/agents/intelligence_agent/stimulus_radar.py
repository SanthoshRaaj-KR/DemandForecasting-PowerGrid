"""
Stimulus Radar - Forward-Looking Risk Detection
===============================================
Aggregates weather forecasts and scraped events into per-state risk scores.
Used by Phase 6 to avoid risky transit paths.

Design: Hybrid query architecture
- Pre-compute risk map at simulation day start
- Selective detailed query only if base risk > threshold
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..shared.models import StimulusFlag, RiskScore, RiskSeverity
from .event_scraper import EventScraper, WeatherScraper
from .economic_monitor import EconomicMonitor
from .political_monitor import PoliticalMonitor
from .setup import CITY_REGISTRY

logger = logging.getLogger(__name__)

# Risk score thresholds
RISK_THRESHOLD_LOW = 0.25
RISK_THRESHOLD_MEDIUM = 0.50
RISK_THRESHOLD_HIGH = 0.75

# Severity weights for score calculation
SEVERITY_WEIGHTS: Dict[RiskSeverity, float] = {
    RiskSeverity.LOW: 0.15,
    RiskSeverity.MEDIUM: 0.35,
    RiskSeverity.HIGH: 0.65,
    RiskSeverity.CRITICAL: 1.0,
}


def time_decay(eta_hours: float) -> float:
    """
    Closer events have higher weight. Max weight at eta=0.
    
    Returns decay factor 0.1-1.0 based on time until event.
    """
    if eta_hours <= 0:
        return 1.0
    elif eta_hours <= 2:
        return 0.9
    elif eta_hours <= 6:
        return 0.7
    elif eta_hours <= 12:
        return 0.5
    elif eta_hours <= 24:
        return 0.3
    else:
        return 0.1


class StimulusRadar:
    """
    Aggregates weather and event data into per-state risk scores.
    
    Usage:
        radar = StimulusRadar()
        risk_map = radar.compute_risk_map()  # Dict[str, RiskScore]
        
        # In Phase 6:
        if risk_map["WB"].total_score > RISK_THRESHOLD_HIGH:
            # Deprioritize paths through WB
    """
    
    def __init__(self):
        self._event_scraper: Optional[EventScraper] = None
        self._weather_scraper: Optional[WeatherScraper] = None
        self._economic_monitor: Optional[EconomicMonitor] = None  # NEW
        self._political_monitor: Optional[PoliticalMonitor] = None  # NEW
        self._cached_risk_map: Optional[Dict[str, RiskScore]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_hours = 1.0  # Refresh cache every hour
    
    def _get_event_scraper(self) -> EventScraper:
        """Lazy initialization of event scraper."""
        if self._event_scraper is None:
            self._event_scraper = EventScraper()
        return self._event_scraper
    
    def _get_weather_scraper(self) -> WeatherScraper:
        """Lazy initialization of weather scraper."""
        if self._weather_scraper is None:
            self._weather_scraper = WeatherScraper()
        return self._weather_scraper
    
    def _get_economic_monitor(self) -> EconomicMonitor:
        """Lazy initialization of economic monitor."""
        if self._economic_monitor is None:
            self._economic_monitor = EconomicMonitor()
        return self._economic_monitor
    
    def _get_political_monitor(self) -> PoliticalMonitor:
        """Lazy initialization of political monitor."""
        if self._political_monitor is None:
            self._political_monitor = PoliticalMonitor()
        return self._political_monitor
    
    def compute_risk_map(self, force_refresh: bool = False) -> Dict[str, RiskScore]:
        """
        Pre-compute risk scores for all states.
        
        This is called at simulation day start by the orchestrator.
        Returns Dict[state_id, RiskScore].
        
        Error handling: Never crashes - returns empty/minimal risk map on failures.
        """
        # Check cache
        if not force_refresh and self._cached_risk_map:
            if self._cache_timestamp:
                age = (datetime.now() - self._cache_timestamp).total_seconds() / 3600
                if age < self._cache_ttl_hours:
                    return self._cached_risk_map
        
        # Collect all stimulus flags
        all_flags: Dict[str, List[StimulusFlag]] = {
            state_id: [] for state_id in CITY_REGISTRY.keys()
        }
        
        # 1. Weather-based flags (with error handling)
        try:
            weather_flags = self._collect_weather_flags()
            for flag in weather_flags:
                if flag.state_id in all_flags:
                    all_flags[flag.state_id].append(flag)
        except Exception as e:
            logger.warning(f"Weather collection failed: {e}")
        
        # 2. Event-based flags (from RSS scraping, with error handling)
        try:
            event_flags = self._collect_event_flags()
            for flag in event_flags:
                if flag.state_id in all_flags:
                    all_flags[flag.state_id].append(flag)
        except Exception as e:
            logger.warning(f"Event collection failed: {e}")
        
        # 3. Economic flags (NEW)
        try:
            economic_flags = self._collect_economic_flags()
            for flag in economic_flags:
                if flag.state_id in all_flags:
                    all_flags[flag.state_id].append(flag)
        except Exception as e:
            logger.warning(f"Economic monitor failed: {e}")
        
        # 4. Political flags (NEW)
        try:
            political_flags = self._collect_political_flags()
            for flag in political_flags:
                if flag.state_id in all_flags:
                    all_flags[flag.state_id].append(flag)
        except Exception as e:
            logger.warning(f"Political monitor failed: {e}")
        
        # 3. Compute aggregate risk scores
        risk_map: Dict[str, RiskScore] = {}
        for state_id, flags in all_flags.items():
            risk_map[state_id] = self._compute_state_risk(state_id, flags)
        
        # Update cache
        self._cached_risk_map = risk_map
        self._cache_timestamp = datetime.now()
        
        return risk_map
    
    def get_detailed_risk(self, state_id: str, hours_ahead: float = 0) -> RiskScore:
        """
        Get detailed risk for a specific state with time projection.
        
        This is the selective query called by Phase 6 only when base risk > threshold.
        """
        risk_map = self.compute_risk_map()
        base_risk = risk_map.get(state_id)
        
        if not base_risk:
            return RiskScore(
                state_id=state_id,
                total_score=0.0,
                severity=RiskSeverity.LOW,
                active_flags=tuple(),
                computed_at=datetime.now().isoformat()
            )
        
        # Adjust flags for time projection
        if hours_ahead > 0:
            projected_flags = []
            for flag in base_risk.active_flags:
                adjusted_eta = max(flag.eta_hours - hours_ahead, 0)
                projected_flags.append(StimulusFlag(
                    state_id=flag.state_id,
                    source=flag.source,
                    event_type=flag.event_type,
                    severity=flag.severity,
                    eta_hours=adjusted_eta,
                    estimated_impact_mw=flag.estimated_impact_mw,
                    description=flag.description,
                    expires_at=flag.expires_at,
                ))
            return self._compute_state_risk(state_id, projected_flags)
        
        return base_risk
    
    def _collect_weather_flags(self) -> List[StimulusFlag]:
        """Convert weather forecasts to StimulusFlags."""
        flags = []
        weather_scraper = self._get_weather_scraper()
        
        for state_id, city_info in CITY_REGISTRY.items():
            try:
                lat = city_info.get("lat", 0)
                lon = city_info.get("lon", 0)
                
                forecast = weather_scraper.fetch_forecast_7d(lat, lon, state_id)
                anomaly = weather_scraper.detect_weather_anomaly(forecast)
                
                if anomaly:
                    severity = RiskSeverity.HIGH if anomaly.get("severity") == "HIGH" else RiskSeverity.MEDIUM
                    flags.append(StimulusFlag(
                        state_id=state_id,
                        source="weather",
                        event_type=anomaly.get("type", "weather_anomaly"),
                        severity=severity,
                        eta_hours=0,  # Weather forecasts are for current/imminent
                        estimated_impact_mw=anomaly.get("estimated_demand_increase_pct", 0) * 100,
                        description=f"{anomaly.get('type')}: {anomaly.get('max_temperature_c', 'N/A')}°C",
                        expires_at=(datetime.now() + timedelta(days=1)).isoformat(),
                    ))
            except Exception as e:
                print(f"[StimulusRadar] Weather flag failed for {state_id}: {e}")
        
        return flags
    
    def _collect_event_flags(self) -> List[StimulusFlag]:
        """Convert scraped events to StimulusFlags."""
        flags = []
        event_scraper = self._get_event_scraper()
        
        try:
            events = event_scraper.scrape_all_feeds()
            grid_events = event_scraper.filter_grid_relevant(events)
            
            for event in grid_events:
                try:
                    affected_states = event_scraper.detect_affected_states(event)
                    event_type = event_scraper.classify_event_type(event)
                    impact_mw = event_scraper.estimate_mw_impact(event)
                    
                    # Map event type to severity
                    severity = self._map_event_to_severity(event_type, impact_mw)
                    
                    for state_id in affected_states:
                        flags.append(StimulusFlag(
                            state_id=state_id,
                            source="grid_event",
                            event_type=event_type,
                            severity=severity,
                            eta_hours=2.0,  # Assume events are imminent (within 2 hours)
                            estimated_impact_mw=impact_mw or 50.0,  # Default 50 MW if unknown
                            description=event.title[:100],
                            expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
                        ))
                except Exception as e:
                    print(f"[StimulusRadar] Event flag parse failed: {e}")
        except Exception as e:
            print(f"[StimulusRadar] Event scraping failed: {e}")
        
        return flags
    
    def _collect_economic_flags(self) -> List[StimulusFlag]:
        """Collect economic risk flags."""
        try:
            economic_monitor = self._get_economic_monitor()
            indicators = economic_monitor.fetch_economic_indicators()
            return economic_monitor.detect_economic_risks(indicators)
        except Exception as e:
            logger.warning(f"Economic monitor failed: {e}")
            return []
    
    def _collect_political_flags(self) -> List[StimulusFlag]:
        """Collect political risk flags from scraped news."""
        try:
            # Get raw scraped events
            event_scraper = self._get_event_scraper()
            political_monitor = self._get_political_monitor()
            
            events = event_scraper.scrape_all_feeds()
            
            # Convert to dict format for political parser
            items = [
                {
                    "title": e.title,
                    "summary": e.description,
                    "published": e.published_date,
                    "source": e.source,
                }
                for e in events
            ]
            
            political_events = political_monitor.parse_political_events(items)
            return political_monitor.convert_to_stimulus_flags(political_events)
        except Exception as e:
            logger.warning(f"Political monitor failed: {e}")
            return []
    
    def _map_event_to_severity(self, event_type: str, impact_mw: float) -> RiskSeverity:
        """Map event type and magnitude to risk severity."""
        if event_type in ["outage", "blackout"]:
            if impact_mw >= 500:
                return RiskSeverity.CRITICAL
            elif impact_mw >= 200:
                return RiskSeverity.HIGH
            else:
                return RiskSeverity.MEDIUM
        elif event_type in ["weather", "cyclone"]:
            return RiskSeverity.HIGH
        elif event_type in ["supply_drop", "demand_spike"]:
            return RiskSeverity.MEDIUM
        elif event_type in ["political", "strike"] or event_type.startswith("political_"):
            return RiskSeverity.MEDIUM
        elif event_type.startswith("economic_"):
            # Economic events severity based on subtype
            if "coal_shortage" in event_type or "fuel_price" in event_type:
                return RiskSeverity.HIGH
            return RiskSeverity.MEDIUM
        else:
            return RiskSeverity.LOW
    
    def _compute_state_risk(self, state_id: str, flags: List[StimulusFlag]) -> RiskScore:
        """Aggregate multiple flags into a single risk score for a state."""
        if not flags:
            return RiskScore(
                state_id=state_id,
                total_score=0.0,
                severity=RiskSeverity.LOW,
                active_flags=tuple(),
                computed_at=datetime.now().isoformat(),
            )
        
        # Compute weighted sum of flag severities with time decay
        total_weight = 0.0
        for flag in flags:
            severity_weight = SEVERITY_WEIGHTS.get(flag.severity, 0.1)
            decay = time_decay(flag.eta_hours)
            total_weight += severity_weight * decay
        
        # Normalize to 0-1 range (cap at 1.0)
        total_score = min(total_weight, 1.0)
        
        # Determine overall severity
        if total_score >= RISK_THRESHOLD_HIGH:
            severity = RiskSeverity.CRITICAL if total_score >= 0.9 else RiskSeverity.HIGH
        elif total_score >= RISK_THRESHOLD_MEDIUM:
            severity = RiskSeverity.MEDIUM
        else:
            severity = RiskSeverity.LOW
        
        return RiskScore(
            state_id=state_id,
            total_score=total_score,
            severity=severity,
            active_flags=tuple(flags),  # Convert to tuple for frozen dataclass compatibility
            computed_at=datetime.now().isoformat(),
        )
