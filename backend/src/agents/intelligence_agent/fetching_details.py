"""
DEPRECATED - No longer used.

Weather fetching has been moved to event_scraper.py (WeatherScraper class).
News fetching (GNews, NewsData) has been removed - we only use trusted RSS now.

Use:
- EventScraper for RSS scraping from trusted sources
- WeatherScraper for Open-Meteo weather data (free, no API key)
"""

# Backward compatibility - import from new location
from .event_scraper import WeatherScraper


class DataFetcher:
    """DEPRECATED - Use EventScraper and WeatherScraper instead."""
    
    def __init__(self, *args, **kwargs):
        print("[DEPRECATED] DataFetcher - Use EventScraper and WeatherScraper instead")
        self._weather = WeatherScraper()
    
    def fetch_hourly_forecast_7d(self, city: str, lat: float, lon: float):
        """Redirect to WeatherScraper."""
        return self._weather.fetch_forecast_7d(lat, lon, city)
    
    def fetch_owm_forecast(self, city: str, lat: float, lon: float):
        """Redirect to WeatherScraper."""
        return self._weather.fetch_forecast_7d(lat, lon, city)
    
    def fetch_gnews(self, *args, **kwargs):
        """GNews removed - use EventScraper for RSS scraping."""
        return []
    
    def fetch_newsdata(self, *args, **kwargs):
        """NewsData removed - use EventScraper for RSS scraping."""
        return []
    
    def scrape_rss_feeds(self):
        """Use EventScraper instead."""
        from .event_scraper import EventScraper
        scraper = EventScraper()
        events = scraper.scrape_all_feeds()
        return {e.source: [e.title] for e in events}
