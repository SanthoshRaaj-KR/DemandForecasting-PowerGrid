"""
Political Monitor - Tracks Political/Social Events Affecting Grid
=================================================================
Monitors strikes, protests, elections, and policy changes that could
disrupt power generation, transmission, or demand patterns.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging
import re

from ..shared.models import StimulusFlag, RiskSeverity

logger = logging.getLogger(__name__)


@dataclass
class PoliticalEvent:
    """Political or social event with grid impact potential."""
    event_type: str  # "strike", "protest", "election", "policy"
    title: str
    description: str
    affected_states: List[str]
    scheduled_date: Optional[str]
    duration_hours: float
    source: str
    severity: str  # "low", "medium", "high"


# Keywords indicating grid-impacting political events
STRIKE_PATTERNS = [
    r"power\s+workers?\s+strike",
    r"electricity\s+employees?\s+strike",
    r"bandh\s+in\s+(\w+)",
    r"(\w+)\s+bandh",
    r"general\s+strike",
    r"labor\s+protest",
    r"union\s+strike",
]

ELECTION_PATTERNS = [
    r"polling\s+in\s+(\w+)",
    r"election\s+(in|at)\s+(\w+)",
    r"voting\s+day",
    r"by-election",
    r"assembly\s+election",
]

POLICY_PATTERNS = [
    r"power\s+subsidy",
    r"electricity\s+reform",
    r"privatization",
    r"tariff\s+order",
    r"regulatory\s+commission",
]

# State name normalization
STATE_ALIASES = {
    "bengal": "West Bengal",
    "wb": "West Bengal", 
    "maharashtra": "Maharashtra",
    "mh": "Maharashtra",
    "karnataka": "Karnataka",
    "ka": "Karnataka",
    "tamil": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "up": "Uttar Pradesh",
    "uttar": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "madhya": "Madhya Pradesh",
    "gujarat": "Gujarat",
    "gj": "Gujarat",
    "rajasthan": "Rajasthan",
    "rj": "Rajasthan",
    "kerala": "Kerala",
    "kl": "Kerala",
    "delhi": "Delhi",
    "dl": "Delhi",
    "punjab": "Punjab",
    "pb": "Punjab",
    "haryana": "Haryana",
    "hr": "Haryana",
    "bihar": "Bihar",
    "br": "Bihar",
    "odisha": "Odisha",
    "od": "Odisha",
    "orissa": "Odisha",
    "jharkhand": "Jharkhand",
    "jh": "Jharkhand",
    "chhattisgarh": "Chhattisgarh",
    "cg": "Chhattisgarh",
    "andhra": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "telangana": "Telangana",
    "ts": "Telangana",
    "assam": "Assam",
    "as": "Assam",
    "goa": "Goa",
    "ga": "Goa",
}


class PoliticalMonitor:
    """
    Monitors political and social events that could affect grid operations.
    
    Impact types:
    - Strike at power plant → Supply drop
    - State bandh → Demand surge (everyone at home)
    - Election day → Peak evening demand
    - Policy change → Long-term supply/demand shift
    """
    
    def __init__(self):
        self._event_cache: List[PoliticalEvent] = []
        self._last_scan: Optional[datetime] = None
    
    def parse_political_events(self, scraped_items: List[Dict]) -> List[PoliticalEvent]:
        """
        Parse scraped news items into structured PoliticalEvents.
        
        Input: List of dicts with 'title', 'summary', 'published' keys
        Output: List of PoliticalEvent objects
        """
        events = []
        
        for item in scraped_items:
            title = item.get("title", "").lower()
            summary = item.get("summary", "").lower()
            text = f"{title} {summary}"
            
            event = None
            
            # Check for strikes
            for pattern in STRIKE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    states = self._extract_states(text)
                    event = PoliticalEvent(
                        event_type="strike",
                        title=item.get("title", ""),
                        description=summary[:200],
                        affected_states=states,
                        scheduled_date=item.get("published"),
                        duration_hours=24.0,  # Assume 1-day strike
                        source=item.get("source", "news"),
                        severity="high",
                    )
                    break
            
            # Check for elections
            if not event:
                for pattern in ELECTION_PATTERNS:
                    match = re.search(pattern, text)
                    if match:
                        states = self._extract_states(text)
                        event = PoliticalEvent(
                            event_type="election",
                            title=item.get("title", ""),
                            description=summary[:200],
                            affected_states=states,
                            scheduled_date=item.get("published"),
                            duration_hours=12.0,  # Voting day
                            source=item.get("source", "news"),
                            severity="medium",
                        )
                        break
            
            # Check for policy changes
            if not event:
                for pattern in POLICY_PATTERNS:
                    if re.search(pattern, text):
                        states = self._extract_states(text)
                        event = PoliticalEvent(
                            event_type="policy",
                            title=item.get("title", ""),
                            description=summary[:200],
                            affected_states=states if states else ["ALL"],
                            scheduled_date=item.get("published"),
                            duration_hours=720.0,  # 30 days (policy impact)
                            source=item.get("source", "news"),
                            severity="low",
                        )
                        break
            
            if event:
                events.append(event)
        
        return events
    
    def _extract_states(self, text: str) -> List[str]:
        """Extract state names from text using aliases."""
        found_states: Set[str] = set()
        text_lower = text.lower()
        
        for alias, canonical in STATE_ALIASES.items():
            if alias in text_lower:
                found_states.add(canonical)
        
        return list(found_states) if found_states else []
    
    def convert_to_stimulus_flags(self, events: List[PoliticalEvent]) -> List[StimulusFlag]:
        """Convert PoliticalEvents to StimulusFlags for risk calculation."""
        flags = []
        
        for event in events:
            severity = self._map_severity(event.severity)
            impact_mw = self._estimate_impact(event)
            eta = self._calculate_eta(event)
            
            for state in event.affected_states:
                if state == "ALL":
                    continue  # National events handled separately
                
                flags.append(StimulusFlag(
                    state_id=state,
                    source="political",
                    event_type=f"political_{event.event_type}",
                    severity=severity,
                    eta_hours=eta,
                    estimated_impact_mw=impact_mw,
                    description=event.title[:100],
                    expires_at=(datetime.now() + timedelta(hours=event.duration_hours)).isoformat(),
                ))
        
        return flags
    
    def _map_severity(self, severity_str: str) -> RiskSeverity:
        """Map string severity to RiskSeverity enum."""
        mapping = {
            "low": RiskSeverity.LOW,
            "medium": RiskSeverity.MEDIUM,
            "high": RiskSeverity.HIGH,
            "critical": RiskSeverity.CRITICAL,
        }
        return mapping.get(severity_str.lower(), RiskSeverity.LOW)
    
    def _estimate_impact(self, event: PoliticalEvent) -> float:
        """Estimate MW impact based on event type."""
        impact_map = {
            "strike": 200.0,  # Power worker strike = significant supply drop
            "election": 50.0,  # Election = moderate demand shift
            "policy": 20.0,  # Policy = minimal immediate impact
            "protest": 30.0,  # Protest = some local disruption
        }
        return impact_map.get(event.event_type, 10.0)
    
    def _calculate_eta(self, event: PoliticalEvent) -> float:
        """Calculate hours until event impacts grid."""
        if not event.scheduled_date:
            return 0.0  # Assume immediate
        
        try:
            scheduled = datetime.fromisoformat(event.scheduled_date)
            delta = scheduled - datetime.now()
            return max(delta.total_seconds() / 3600, 0.0)
        except (ValueError, TypeError):
            return 0.0
