"""
Configuration, Models, and Cache layer for Intelligence Agent.

REDESIGNED SYSTEM (2-Tier Architecture):
=========================================
TIER 1 (Day 0): ForwardMarketPlanner
  - Consumes 30-day LightGBM predictions
  - Calculates Base_Deficit and Base_Surplus for each state
  - Creates baseline_schedule dictionary
  - Grid is assumed mathematically balanced

TIER 2 (Daily Loop): DeviationDetector
  - Fetches daily events from TRUSTED sources only
  - Calculates Anomaly_Delta_MW (deviation from baseline)
  - If Anomaly_Delta_MW == 0: Agents stay dormant
  - If Anomaly_Delta_MW > 0: Wake UnifiedRoutingOrchestrator
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

RSS_ITEM_LIMIT = 15  # Max items per RSS feed

# TRUSTED RSS FEEDS ONLY - Government and official grid sources
TRUSTED_RSS_FEEDS: Dict[str, str] = {
    # Official Grid Operators (most reliable)
    "Grid-India (NLDC)": "https://grid-india.in/feed/",
    "NRLDC (North Grid)": "https://nrldc.in/feed/",
    "WRLDC (West Grid)": "https://wrldc.in/feed/",
    "SRLDC (South Grid)": "https://srldc.in/feed/",
    "ERLDC (East Grid)": "https://erldc.in/feed/",
    # Government Press (official announcements)
    "PIB India": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
    "CEA (Central Electricity Authority)": "https://cea.nic.in/rss_feed/",
    # Established Energy News
    "ET Energy": "https://energy.economictimes.indiatimes.com/rss/topstories",
    # Economic / Energy Market (NEW)
    "Moneycontrol Energy": "https://www.moneycontrol.com/rss/energy.xml",
    "LiveMint Energy": "https://www.livemint.com/rss/energy",
    "Business Standard Power": "https://www.business-standard.com/rss/power-102.rss",
    # Coal / Fuel (NEW)
    "Coal India": "https://www.coal.gov.in/rss",
    # Political / General India News (NEW)
    "TOI India News": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "HT India News": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "NDTV India": "https://www.ndtv.com/rss/india",
}

# State/Node Registry
CITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "BHR": {
        "name": "Bihar",
        "state": "Bihar",
        "lat": 25.5941,
        "lon": 85.1376,
        "typical_peak_mw": 7000,
        "primary_discom": ["NBPDCL", "SBPDCL"],
    },
    "UP": {
        "name": "Lucknow",
        "state": "Uttar Pradesh",
        "lat": 26.8467,
        "lon": 80.9462,
        "typical_peak_mw": 28000,
        "primary_discom": ["UPPCL", "MVVNL", "PVVNL"],
    },
    "WB": {
        "name": "Kolkata",
        "state": "West Bengal",
        "lat": 22.5726,
        "lon": 88.3639,
        "typical_peak_mw": 9500,
        "primary_discom": ["CESC", "WBSEDCL"],
    },
    "KAR": {
        "name": "Bengaluru",
        "state": "Karnataka",
        "lat": 12.9716,
        "lon": 77.5946,
        "typical_peak_mw": 16000,
        "primary_discom": ["BESCOM", "GESCOM"],
    },
}


# ============================================================================
# TIER 1: BASELINE PLANNING MODELS
# ============================================================================

@dataclass
class StateBaseline:
    """Baseline demand/supply for a single state on a single day."""
    state_id: str
    day_index: int
    date_str: str
    predicted_demand_mw: float
    base_supply_mw: float
    base_deficit_mw: float  # Positive = needs power
    base_surplus_mw: float  # Positive = can export


@dataclass
class BaselineSchedule:
    """
    30-day baseline schedule computed from LightGBM predictions.
    This is the "mathematically balanced" plan before real-world chaos.
    """
    generated_at: str
    states: List[str]
    daily_baselines: Dict[str, List[StateBaseline]]  # state_id -> 30 days
    scheduled_transfers: List[Dict[str, Any]]  # Pre-planned deficit resolution
    total_deficit_mw: float
    total_surplus_mw: float
    is_balanced: bool


# ============================================================================
# TIER 2: REAL-TIME DEVIATION MODELS
# ============================================================================

@dataclass
class ScrapedEvent:
    """
    An event scraped from trusted RSS sources.
    Simple, structured, no LLM hallucination.
    """
    source: str              # RSS feed name
    title: str               # Headline
    description: str         # Body text (truncated)
    published_date: str      # ISO date
    url: str                 # Original link
    scraped_at: str          # When we fetched it


@dataclass
class GridAnomaly:
    """
    A detected deviation from baseline caused by a real-world event.
    """
    event_type: str          # "weather" | "outage" | "demand_spike" | "supply_drop" | "political" | "disaster"
    description: str         # What happened
    affected_states: List[str]
    anomaly_delta_mw: float  # Deviation from baseline (positive = more demand or less supply)
    confidence: float        # 0.0 to 1.0
    source_events: List[ScrapedEvent]
    detected_at: str


@dataclass 
class DailyDeviationResult:
    """
    Output of DeviationDetector for a single day.
    If anomaly_delta_mw == 0, agents stay dormant.
    """
    day_index: int
    date_str: str
    anomaly_delta_mw: float          # Total deviation across all states
    state_anomalies: Dict[str, float]  # Per-state deviation
    detected_anomalies: List[GridAnomaly]
    should_wake_orchestrator: bool   # True if anomaly_delta_mw > 0
    message: str                     # Human-readable status


# ============================================================================
# BACKWARD COMPATIBILITY: Keep these for existing imports
# ============================================================================

class GridEvent(BaseModel):
    """Structured grid event for downstream phases."""
    event_name: str
    affected_states: List[str] = Field(default_factory=list)
    demand_multiplier: float = Field(ge=0.0, default=1.0)
    supply_multiplier: float = Field(ge=0.0, default=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)


@dataclass
class GridMultipliers:
    """Grid adjustment multipliers (backward compatible)."""
    pre_event_hoard: bool = False
    temperature_anomaly: float = 0.0
    economic_demand_multiplier: float = 1.0
    generation_capacity_multiplier: float = 1.0
    demand_spike_risk: str = "LOW"
    supply_shortfall_risk: str = "LOW"
    seven_day_demand_forecast_mw_delta: int = 0
    confidence: float = 0.5
    key_driver: str = "Baseline"
    reasoning: str = "No anomalies detected"
    severity_level: int = 1


# ============================================================================
# CACHE UTILITIES
# ============================================================================

class BaselineCache:
    """
    Persists BaselineSchedule to disk.
    Recompute only if predictions change or new month starts.
    """

    def __init__(self, cache_dir: Path):
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self) -> Path:
        return self._dir / "baseline_schedule.json"

    def load(self) -> Optional[BaselineSchedule]:
        p = self._path()
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            # Reconstruct StateBaseline objects
            daily_baselines = {}
            for state_id, baselines in data.get("daily_baselines", {}).items():
                daily_baselines[state_id] = [
                    StateBaseline(**b) for b in baselines
                ]
            data["daily_baselines"] = daily_baselines
            return BaselineSchedule(**data)
        except Exception as exc:
            print(f"[CACHE] Baseline load failed: {exc}")
            return None

    def save(self, schedule: BaselineSchedule) -> None:
        p = self._path()
        # Convert StateBaseline objects to dicts
        data = {
            "generated_at": schedule.generated_at,
            "states": schedule.states,
            "daily_baselines": {
                state_id: [asdict(b) for b in baselines]
                for state_id, baselines in schedule.daily_baselines.items()
            },
            "scheduled_transfers": schedule.scheduled_transfers,
            "total_deficit_mw": schedule.total_deficit_mw,
            "total_surplus_mw": schedule.total_surplus_mw,
            "is_balanced": schedule.is_balanced,
        }
        p.write_text(json.dumps(data, indent=2))
        print(f"[CACHE] Saved baseline schedule — {p}")
