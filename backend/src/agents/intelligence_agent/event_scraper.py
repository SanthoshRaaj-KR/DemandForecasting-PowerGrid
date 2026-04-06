"""
event_scraper.py
================
Reliable web scraping from TRUSTED SOURCES ONLY.

This scraper:
1. Only uses official RSS feeds (Grid-India, NLDC, PIB, etc.)
2. Uses proper error handling and retries
3. Deduplicates and normalizes data
4. NO LLM - just clean structured scraping

Trusted Sources:
- Grid-India (NLDC) - National Load Dispatch Center
- NRLDC, WRLDC, SRLDC, ERLDC - Regional Load Dispatch Centers
- PIB India - Press Information Bureau
- ET Energy - Economic Times Energy vertical
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup
from urllib3.util.ssl_ import create_urllib3_context

from .setup import TRUSTED_RSS_FEEDS, RSS_ITEM_LIMIT, ScrapedEvent, CITY_REGISTRY


class LegacySSLAdapter(requests.adapters.HTTPAdapter):
    """
    Adapter for legacy SSL/TLS servers (common on Indian government domains).
    Enables unsafe legacy renegotiation for compatibility.
    """
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.options |= 0x4  # ssl.OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


class EventScraper:
    """
    Scrapes events from trusted RSS feeds only.
    
    Design principles:
    - Only official/government sources
    - Proper error handling (never crashes)
    - Automatic deduplication
    - No external API keys required
    """
    
    # Keywords for grid-relevant events
    GRID_KEYWORDS = [
        # Power/Grid
        "power", "electricity", "grid", "load", "demand", "supply",
        "generation", "transmission", "outage", "blackout", "tripping",
        "frequency", "voltage", "mw", "gw", "megawatt", "gigawatt",
        # Fuel
        "coal", "thermal", "hydro", "solar", "wind", "renewable",
        "gas", "fuel", "shortage", "stock",
        # Infrastructure
        "plant", "substation", "transformer", "line", "corridor",
        "commissioning", "maintenance", "shutdown",
        # Events that affect demand
        "heatwave", "coldwave", "monsoon", "cyclone", "flood",
        "festival", "election", "holiday", "industrial",
    ]
    
    # State name variations for detection
    STATE_ALIASES = {
        "BHR": ["bihar", "patna", "nbpdcl", "sbpdcl"],
        "UP": ["uttar pradesh", "lucknow", "uppcl", "mvvnl", "pvvnl", "noida", "agra"],
        "WB": ["west bengal", "kolkata", "cesc", "wbsedcl", "bengal"],
        "KAR": ["karnataka", "bengaluru", "bangalore", "bescom", "gescom"],
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or Path("outputs/context_cache/events")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = self._create_session()
        self._seen_hashes: Set[str] = set()
    
    def _create_session(self) -> requests.Session:
        """Create session with proper headers and SSL adapters."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (SmartGrid-Intel/2.0; +https://grid.example.com)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        })
        
        # Mount legacy SSL adapter for government domains
        legacy_adapter = LegacySSLAdapter()
        for domain in ["nrldc.in", "wrldc.in", "srldc.in", "erldc.in", 
                       "posoco.in", "grid-india.in", "pib.gov.in"]:
            session.mount(f"https://{domain}", legacy_adapter)
        
        return session
    
    def scrape_all_feeds(self) -> List[ScrapedEvent]:
        """
        Scrape all trusted RSS feeds and return deduplicated events.
        
        Returns list of ScrapedEvent objects, sorted by publish date (newest first).
        """
        all_events: List[ScrapedEvent] = []
        self._seen_hashes.clear()
        
        print("\n[EventScraper] Scraping trusted RSS feeds...")
        
        for feed_name, feed_url in TRUSTED_RSS_FEEDS.items():
            events = self._scrape_single_feed(feed_name, feed_url)
            all_events.extend(events)
            # Rate limiting - be nice to servers
            time.sleep(0.3)
        
        # Sort by date (newest first)
        all_events.sort(key=lambda e: e.published_date, reverse=True)
        
        print(f"[EventScraper] Total events scraped: {len(all_events)}")
        
        return all_events
    
    def _scrape_single_feed(self, feed_name: str, feed_url: str) -> List[ScrapedEvent]:
        """Scrape a single RSS feed with error handling."""
        events: List[ScrapedEvent] = []
        
        try:
            response = self._session.get(feed_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item", limit=RSS_ITEM_LIMIT)
            
            for item in items:
                event = self._parse_rss_item(item, feed_name, feed_url)
                if event and self._is_unique(event):
                    events.append(event)
            
            print(f"  ✓ {feed_name}: {len(events)} items")
            
        except requests.exceptions.Timeout:
            print(f"  ✗ {feed_name}: Timeout")
        except requests.exceptions.SSLError as e:
            print(f"  ✗ {feed_name}: SSL Error - {str(e)[:50]}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ {feed_name}: Request failed - {str(e)[:50]}")
        except Exception as e:
            print(f"  ✗ {feed_name}: Parse error - {str(e)[:50]}")
        
        return events
    
    def _parse_rss_item(
        self,
        item: Any,
        feed_name: str,
        feed_url: str,
    ) -> Optional[ScrapedEvent]:
        """Parse a single RSS item into ScrapedEvent."""
        try:
            title_elem = item.find("title")
            desc_elem = item.find("description")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            url = link_elem.get_text(strip=True) if link_elem else feed_url
            
            # Clean HTML from description
            if description:
                description = BeautifulSoup(description, "html.parser").get_text()
                description = description[:500]  # Truncate
            
            # Parse publication date
            pub_date = datetime.now().isoformat()
            if pub_date_elem:
                try:
                    # Common RSS date formats
                    date_str = pub_date_elem.get_text(strip=True)
                    for fmt in [
                        "%a, %d %b %Y %H:%M:%S %z",
                        "%a, %d %b %Y %H:%M:%S %Z",
                        "%Y-%m-%dT%H:%M:%S%z",
                        "%Y-%m-%d",
                    ]:
                        try:
                            parsed = datetime.strptime(date_str[:30], fmt)
                            pub_date = parsed.isoformat()
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
            
            if not title:
                return None
            
            return ScrapedEvent(
                source=feed_name,
                title=title,
                description=description,
                published_date=pub_date,
                url=url,
                scraped_at=datetime.now().isoformat(),
            )
            
        except Exception:
            return None
    
    def _is_unique(self, event: ScrapedEvent) -> bool:
        """Check if event is unique (not already seen)."""
        # Hash based on title (first 80 chars)
        hash_key = hashlib.md5(event.title[:80].lower().encode()).hexdigest()
        if hash_key in self._seen_hashes:
            return False
        self._seen_hashes.add(hash_key)
        return True
    
    def filter_grid_relevant(self, events: List[ScrapedEvent]) -> List[ScrapedEvent]:
        """Filter events to only those relevant to power grid."""
        relevant = []
        for event in events:
            text = (event.title + " " + event.description).lower()
            if any(kw in text for kw in self.GRID_KEYWORDS):
                relevant.append(event)
        return relevant
    
    def detect_affected_states(self, event: ScrapedEvent) -> List[str]:
        """Detect which states are affected by an event."""
        text = (event.title + " " + event.description).lower()
        affected = []
        
        for state_id, aliases in self.STATE_ALIASES.items():
            if any(alias in text for alias in aliases):
                affected.append(state_id)
        
        return affected
    
    def classify_event_type(self, event: ScrapedEvent) -> str:
        """Classify event into category."""
        text = (event.title + " " + event.description).lower()
        
        if any(kw in text for kw in ["outage", "tripping", "failure", "blackout", "shutdown"]):
            return "outage"
        elif any(kw in text for kw in ["heatwave", "coldwave", "cyclone", "flood", "monsoon"]):
            return "weather"
        elif any(kw in text for kw in ["coal", "fuel", "shortage", "supply"]):
            return "supply_drop"
        elif any(kw in text for kw in ["demand", "peak", "record", "surge"]):
            return "demand_spike"
        elif any(kw in text for kw in ["election", "festival", "holiday", "bandh"]):
            return "political"
        elif any(kw in text for kw in ["commissioning", "new", "capacity", "addition"]):
            return "capacity_addition"
        else:
            return "general"
    
    def estimate_mw_impact(self, event: ScrapedEvent) -> float:
        """
        Estimate MW impact from event text.
        
        This is a simple heuristic - looks for numbers followed by MW/GW.
        Returns 0 if no impact can be estimated.
        """
        text = event.title + " " + event.description
        
        # Look for patterns like "500 MW", "1.5 GW", etc.
        mw_pattern = r"(\d+(?:\.\d+)?)\s*(?:mw|megawatt)"
        gw_pattern = r"(\d+(?:\.\d+)?)\s*(?:gw|gigawatt)"
        
        mw_matches = re.findall(mw_pattern, text.lower())
        gw_matches = re.findall(gw_pattern, text.lower())
        
        total_mw = 0.0
        for match in mw_matches:
            total_mw += float(match)
        for match in gw_matches:
            total_mw += float(match) * 1000
        
        return total_mw
    
    def save_events_to_cache(self, events: List[ScrapedEvent]) -> Path:
        """Save scraped events to cache file."""
        cache_file = self._cache_dir / f"events_{datetime.now().strftime('%Y%m%d')}.json"
        
        import json
        data = [asdict(e) for e in events]
        cache_file.write_text(json.dumps(data, indent=2))
        
        return cache_file
    
    def load_events_from_cache(self, date_str: Optional[str] = None) -> List[ScrapedEvent]:
        """Load events from cache file."""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        
        cache_file = self._cache_dir / f"events_{date_str}.json"
        
        if not cache_file.exists():
            return []
        
        import json
        try:
            data = json.loads(cache_file.read_text())
            return [ScrapedEvent(**e) for e in data]
        except Exception:
            return []


# ─── Weather Scraping (Open-Meteo, FREE, no API key) ────────────────────────

WEATHER_CODE_LABELS = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "rime fog", 51: "light drizzle", 53: "drizzle",
    55: "dense drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    82: "violent rain showers", 95: "thunderstorm", 96: "thunderstorm with hail",
}


class WeatherScraper:
    """
    Fetch 7-day weather forecast from Open-Meteo (FREE, no API key).
    
    This is useful for detecting weather-related anomalies:
    - Heatwaves (high temperature → AC demand spike)
    - Cold waves (heating demand)
    - Heavy rain/cyclones (infrastructure risk)
    """
    
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (SmartGrid-Weather/1.0)",
        })
    
    def fetch_forecast_7d(
        self,
        lat: float,
        lon: float,
        city_name: str = "Unknown",
    ) -> Dict[str, Any]:
        """
        Fetch 7-day weather forecast from Open-Meteo.
        
        Returns dict with daily_forecast_7d list and metadata.
        """
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
            "apparent_temperature_min,precipitation_sum,weathercode"
            "&forecast_days=7"
            "&timezone=auto"
        )
        
        try:
            r = self._session.get(url, timeout=12)
            r.raise_for_status()
            raw = r.json()
            
            daily = raw.get("daily", {})
            times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            max_apparent = daily.get("apparent_temperature_max", [])
            precip = daily.get("precipitation_sum", [])
            codes = daily.get("weathercode", [])
            
            forecasts = []
            for i, day in enumerate(times):
                forecasts.append({
                    "date": day,
                    "max_c": round(max_temps[i], 1) if i < len(max_temps) else None,
                    "min_c": round(min_temps[i], 1) if i < len(min_temps) else None,
                    "heat_index_c": round(max_apparent[i], 1) if i < len(max_apparent) else None,
                    "precipitation_mm": round(precip[i], 1) if i < len(precip) else 0.0,
                    "condition": WEATHER_CODE_LABELS.get(codes[i], "unknown") if i < len(codes) else "unknown",
                })
            
            return {
                "source": "open-meteo",
                "city": city_name,
                "daily_forecast_7d": forecasts,
                "week_max_c": max(max_temps) if max_temps else None,
                "week_max_heat_index": max(max_apparent) if max_apparent else None,
                "week_total_rain_mm": round(sum(precip), 1) if precip else 0.0,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "city": city_name,
                "daily_forecast_7d": [],
            }
    
    def detect_weather_anomaly(
        self,
        forecast: Dict[str, Any],
        heatwave_threshold_c: float = 40.0,
        heavy_rain_threshold_mm: float = 50.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect weather anomalies that could impact the grid.
        
        Returns anomaly dict or None if no significant anomaly.
        """
        if "error" in forecast:
            return None
        
        max_temp = forecast.get("week_max_c")
        max_heat = forecast.get("week_max_heat_index")
        total_rain = forecast.get("week_total_rain_mm", 0)
        
        # Check for heatwave
        if max_temp and max_temp >= heatwave_threshold_c:
            return {
                "type": "heatwave",
                "severity": "HIGH" if max_temp >= 45 else "MEDIUM",
                "max_temperature_c": max_temp,
                "estimated_demand_increase_pct": min(20, (max_temp - 35) * 2),
            }
        
        # Check for heat index anomaly
        if max_heat and max_heat >= heatwave_threshold_c + 5:
            return {
                "type": "heat_stress",
                "severity": "MEDIUM",
                "max_heat_index_c": max_heat,
                "estimated_demand_increase_pct": min(15, (max_heat - 40) * 1.5),
            }
        
        # Check for heavy rain / cyclone risk
        if total_rain >= heavy_rain_threshold_mm:
            return {
                "type": "heavy_precipitation",
                "severity": "HIGH" if total_rain >= 100 else "MEDIUM",
                "total_precipitation_mm": total_rain,
                "estimated_supply_impact_pct": -5,  # Negative = risk
            }
        
        return None
