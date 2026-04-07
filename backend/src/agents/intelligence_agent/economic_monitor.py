"""
Economic Monitor - Tracks Market Events Affecting Power Grid
=============================================================
Monitors coal prices, fuel markets, electricity auctions, and tariff changes
that could impact state power availability or demand.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..shared.models import StimulusFlag, RiskSeverity

logger = logging.getLogger(__name__)


@dataclass
class EconomicIndicator:
    """Economic data point with grid impact assessment."""
    indicator_type: str  # "coal_price", "spot_price", "forex", "tariff"
    value: float
    unit: str
    change_pct: float  # Change from baseline
    timestamp: str
    source: str
    affected_states: List[str]


# Impact thresholds for economic indicators
COAL_PRICE_THRESHOLD_PCT = 15.0  # >15% increase = HIGH risk
SPOT_PRICE_THRESHOLD_PCT = 20.0  # >20% above normal = HIGH risk
TARIFF_CHANGE_THRESHOLD_PCT = 10.0  # >10% hike = MEDIUM risk

# State → Primary fuel dependency
STATE_FUEL_DEPENDENCY = {
    # Coal-heavy states
    "Chhattisgarh": {"coal": 0.9, "gas": 0.05, "renewable": 0.05},
    "Jharkhand": {"coal": 0.85, "gas": 0.05, "renewable": 0.10},
    "Odisha": {"coal": 0.80, "gas": 0.05, "renewable": 0.15},
    "West Bengal": {"coal": 0.75, "gas": 0.10, "renewable": 0.15},
    "Maharashtra": {"coal": 0.65, "gas": 0.15, "renewable": 0.20},
    "Madhya Pradesh": {"coal": 0.70, "gas": 0.10, "renewable": 0.20},
    
    # Gas-dependent states
    "Gujarat": {"coal": 0.40, "gas": 0.35, "renewable": 0.25},
    "Tamil Nadu": {"coal": 0.50, "gas": 0.20, "renewable": 0.30},
    
    # Hydro/Renewable-heavy states
    "Karnataka": {"coal": 0.35, "gas": 0.10, "renewable": 0.55},
    "Kerala": {"coal": 0.20, "gas": 0.10, "renewable": 0.70},
    "Himachal Pradesh": {"coal": 0.10, "gas": 0.05, "renewable": 0.85},
    
    # Others (default profile)
    "DEFAULT": {"coal": 0.60, "gas": 0.15, "renewable": 0.25},
}


class EconomicMonitor:
    """
    Monitors economic indicators that affect power grid operations.
    
    Sources:
    - IEX (Indian Energy Exchange) day-ahead market prices
    - Coal India pricing
    - Fuel import costs
    - State tariff notifications
    """
    
    def __init__(self):
        self._baseline_coal_price = 5000.0  # INR per tonne (approximate)
        self._baseline_spot_price = 4.5  # INR per kWh (approximate)
        self._last_fetch: Optional[datetime] = None
        self._cache_ttl_hours = 6.0
        self._injected_indicators: List[EconomicIndicator] = []
    
    def fetch_economic_indicators(self) -> List[EconomicIndicator]:
        """
        Fetch current economic indicators.
        
        Note: In production, this would hit actual APIs. For simulation,
        we return placeholder data that can be overridden.
        """
        # Check for injected indicators first (for testing/simulation)
        if self._injected_indicators:
            indicators = list(self._injected_indicators)
            self._injected_indicators.clear()
            return indicators
        
        indicators = []
        
        # Simulated coal price indicator
        indicators.append(EconomicIndicator(
            indicator_type="coal_price",
            value=self._baseline_coal_price,
            unit="INR/tonne",
            change_pct=0.0,
            timestamp=datetime.now().isoformat(),
            source="simulated",
            affected_states=list(STATE_FUEL_DEPENDENCY.keys()),
        ))
        
        # Simulated spot price indicator
        indicators.append(EconomicIndicator(
            indicator_type="spot_price",
            value=self._baseline_spot_price,
            unit="INR/kWh",
            change_pct=0.0,
            timestamp=datetime.now().isoformat(),
            source="simulated",
            affected_states=list(STATE_FUEL_DEPENDENCY.keys()),
        ))
        
        return indicators
    
    def detect_economic_risks(self, indicators: List[EconomicIndicator]) -> List[StimulusFlag]:
        """
        Convert economic indicators to StimulusFlags for risk calculation.
        
        Logic:
        - Coal price spike → HIGH risk for coal-dependent states
        - Spot price spike → MEDIUM risk for importing states
        - Tariff change → LOW-MEDIUM risk for affected state
        """
        flags = []
        
        for indicator in indicators:
            if indicator.indicator_type == "coal_price":
                flags.extend(self._assess_coal_risk(indicator))
            elif indicator.indicator_type == "spot_price":
                flags.extend(self._assess_spot_price_risk(indicator))
            elif indicator.indicator_type == "tariff":
                flags.extend(self._assess_tariff_risk(indicator))
        
        return flags
    
    def _assess_coal_risk(self, indicator: EconomicIndicator) -> List[StimulusFlag]:
        """Assess coal price impact on coal-dependent states."""
        flags = []
        
        if abs(indicator.change_pct) < COAL_PRICE_THRESHOLD_PCT:
            return flags  # No significant change
        
        # Determine severity based on change magnitude
        if indicator.change_pct >= 25.0:
            severity = RiskSeverity.HIGH
        elif indicator.change_pct >= 15.0:
            severity = RiskSeverity.MEDIUM
        else:
            severity = RiskSeverity.LOW
        
        # Apply to coal-dependent states proportionally
        for state, deps in STATE_FUEL_DEPENDENCY.items():
            if state == "DEFAULT":
                continue
            
            coal_dep = deps.get("coal", 0.6)
            if coal_dep >= 0.7:  # Only flag high coal dependency states
                flags.append(StimulusFlag(
                    state_id=state,
                    source="economic",
                    event_type="coal_price_spike",
                    severity=severity,
                    eta_hours=24.0,  # Price impacts take time to affect grid
                    estimated_impact_mw=100.0 * coal_dep,  # Proportional impact
                    description=f"Coal price up {indicator.change_pct:.1f}% - high dependency state",
                    expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
                ))
        
        return flags
    
    def _assess_spot_price_risk(self, indicator: EconomicIndicator) -> List[StimulusFlag]:
        """Assess spot market price impact on deficit states."""
        flags = []
        
        if indicator.change_pct < SPOT_PRICE_THRESHOLD_PCT:
            return flags
        
        severity = RiskSeverity.HIGH if indicator.change_pct >= 30.0 else RiskSeverity.MEDIUM
        
        # Spot price spikes affect states that need to import power
        # This will be populated based on current deficit states during runtime
        return flags
    
    def _assess_tariff_risk(self, indicator: EconomicIndicator) -> List[StimulusFlag]:
        """Assess tariff change impact on affected state."""
        flags = []
        
        if indicator.change_pct < TARIFF_CHANGE_THRESHOLD_PCT:
            return flags
        
        severity = RiskSeverity.MEDIUM if indicator.change_pct >= 15.0 else RiskSeverity.LOW
        
        for state in indicator.affected_states:
            flags.append(StimulusFlag(
                state_id=state,
                source="economic",
                event_type="tariff_hike",
                severity=severity,
                eta_hours=0.0,  # Immediate demand impact
                estimated_impact_mw=50.0,  # Moderate demand reduction
                description=f"Tariff increased by {indicator.change_pct:.1f}%",
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
            ))
        
        return flags
    
    def inject_indicator(self, indicator: EconomicIndicator):
        """
        Inject a custom indicator for testing/simulation.
        
        Usage:
            monitor.inject_indicator(EconomicIndicator(
                indicator_type="coal_price",
                value=6000.0,
                unit="INR/tonne",
                change_pct=20.0,  # 20% spike
                ...
            ))
        """
        self._injected_indicators.append(indicator)
