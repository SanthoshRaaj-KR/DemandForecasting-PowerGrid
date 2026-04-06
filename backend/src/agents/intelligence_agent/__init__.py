"""
intelligence_agent package - REDESIGNED

2-TIER ARCHITECTURE:
====================
TIER 1 (Day 0): ForwardMarketPlanner
  - Computes 30-day baseline from LightGBM predictions
  - Calculates Base_Deficit and Base_Surplus per state
  - Creates scheduled_transfers to balance the grid

TIER 2 (Daily): DeviationDetector
  - Scrapes events from TRUSTED sources only (no LLM)
  - Calculates Anomaly_Delta_MW (deviation from baseline)
  - If Anomaly_Delta_MW == 0: Agents dormant
  - If Anomaly_Delta_MW > 0: Wake UnifiedRoutingOrchestrator

Key Components:
  ForwardMarketPlanner    — TIER 1: Pre-simulation baseline planning
  EventScraper            — Reliable RSS scraping from trusted sources
  WeatherScraper          — Free weather data from Open-Meteo
  DeviationDetector       — TIER 2: Real-time anomaly detection
  IntelligenceOrchestrator — Main orchestrator (2-tier wrapper)
  SmartGridIntelligenceAgent — Backward compatibility alias
"""

# TIER 1: Baseline Planning
from .forward_market_planner import ForwardMarketPlanner

# TIER 2: Event Scraping and Deviation Detection  
from .event_scraper import EventScraper, WeatherScraper
from .deviation_detector import DeviationDetector

# Orchestration
from .orchestrator import IntelligenceOrchestrator, SmartGridIntelligenceAgent

# Data Models (from setup.py)
from .setup import (
    CITY_REGISTRY,
    TRUSTED_RSS_FEEDS,
    BaselineSchedule,
    StateBaseline,
    ScrapedEvent,
    GridAnomaly,
    DailyDeviationResult,
    GridEvent,
    GridMultipliers,
)

__all__ = [
    # TIER 1
    "ForwardMarketPlanner",
    # TIER 2
    "EventScraper",
    "WeatherScraper",
    "DeviationDetector",
    # Orchestration
    "IntelligenceOrchestrator",
    "SmartGridIntelligenceAgent",
    # Models
    "CITY_REGISTRY",
    "TRUSTED_RSS_FEEDS",
    "BaselineSchedule",
    "StateBaseline",
    "ScrapedEvent",
    "GridAnomaly",
    "DailyDeviationResult",
    "GridEvent",
    "GridMultipliers",
]
