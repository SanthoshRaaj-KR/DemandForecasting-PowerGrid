# External Integrations

**Analysis Date:** 2026-04-05

## APIs & External Services

**AI/LLM Services:**
- OpenAI API - used for all intelligence sub-agent chat completions
  - SDK/Client: `openai` (`backend/requirements.txt`)
  - Evidence: `from openai import OpenAI` in `backend/src/agents/intelligence_agent/base_agent.py` and `backend/src/agents/intelligence_agent/orchestrator.py`
  - Auth: environment-managed via OpenAI SDK default behavior (explicit key variable name not hardcoded in repository code)

**Weather Data Services:**
- OpenWeatherMap Forecast API (`api.openweathermap.org`) - 5-day weather and heat index context for regions
  - SDK/Client: `requests` session in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Evidence: `fetch_owm_forecast()` URL construction in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Auth: `OWM_API_KEY` loaded in `backend/src/agents/intelligence_agent/orchestrator.py`
- Open-Meteo Forecast API (`api.open-meteo.com`) - 7-day hourly forecast enrichment
  - SDK/Client: `requests` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Evidence: `fetch_hourly_forecast_7d()` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Auth: none (endpoint used without API key in code)

**News & Signal Ingestion Services:**
- GNews API (`gnews.io`) - multi-query headline ingestion for city/grid/fuel/event signals
  - SDK/Client: `requests` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Evidence: `fetch_gnews()` and query calls from `backend/src/agents/intelligence_agent/orchestrator.py`
  - Auth: `GNEWS_API_KEY` in `backend/src/agents/intelligence_agent/orchestrator.py`
- NewsData.io API (`newsdata.io`) - supplementary India news ingestion
  - SDK/Client: `requests` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Evidence: `fetch_newsdata()` and orchestrator usage in `backend/src/agents/intelligence_agent/orchestrator.py`
  - Auth: `NEWSDATA_API_KEY` in `backend/src/agents/intelligence_agent/orchestrator.py`
- RSS feeds (Times of India, The Hindu, ET Energy, PIB, Grid-India, NRLDC/WRLDC/SRLDC/ERLDC, etc.)
  - SDK/Client: `requests` + `BeautifulSoup` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Evidence: `RSS_FEEDS` registry in `backend/src/agents/intelligence_agent/setup.py` and `scrape_rss_feeds()` in `backend/src/agents/intelligence_agent/fetching_details.py`
  - Auth: none detected

## Data Storage

**Databases:**
- Not detected (no ORM setup, DB connection strings, or database clients found in inspected backend/frontend source)

**File Storage:**
- Local filesystem only
  - Intelligence cache and raw API dumps: `backend/outputs/context_cache/` (written in `backend/src/agents/intelligence_agent/orchestrator.py`)
  - Intelligence export: `backend/outputs/grid_intelligence_*.json` from `backend/main.py` and `backend/routes.py`
  - Simulation output: `outputs/simulation_result_*.json` and `backend/outputs/simulation_result_*.json` via `backend/run_simulation.py` and read in `backend/routes.py`

**Caching:**
- File-based cache only (daily node cache and city intelligence cache)
  - Evidence: `CityIntelligenceCache` in `backend/src/agents/intelligence_agent/setup.py`
  - Paths: `backend/outputs/context_cache/city_intel/` and `backend/outputs/context_cache/node_*_YYYY-MM-DD.json`

## Authentication & Identity

**Auth Provider:**
- Custom/none for application API endpoints (no user auth middleware found in `backend/routes.py`)
  - Implementation: API key auth is used only for outbound third-party service calls (env keys in orchestrator), not for end-user identity

## Monitoring & Observability

**Error Tracking:**
- Not found (no Sentry, Datadog, Rollbar, or equivalent SDK imports in inspected files)

**Logs:**
- Python logging and print-based operational logs
  - Evidence: `logging.basicConfig(...)` in `backend/run_simulation.py`
  - Raw integration dump logging to file in `backend/src/agents/intelligence_agent/orchestrator.py` (`raw_api_dump_*.txt`)

## CI/CD & Deployment

**Hosting:**
- Not found (no explicit cloud hosting config, container config, or IaC files detected)

**CI Pipeline:**
- Not found (no GitHub Actions, GitLab CI, Azure Pipelines, or similar config detected in inspected directories)

## Environment Configuration

**Required env vars:**
- `GNEWS_API_KEY` (`backend/src/agents/intelligence_agent/orchestrator.py`)
- `NEWSDATA_API_KEY` (`backend/src/agents/intelligence_agent/orchestrator.py`)
- `OWM_API_KEY` (`backend/src/agents/intelligence_agent/orchestrator.py`)
- `NEXT_PUBLIC_API_URL` optional frontend API base override (`frontend/src/hooks/useApi.js`)
- OpenAI key variable name not directly referenced in code; required implicitly by `OpenAI()` client in `backend/src/agents/intelligence_agent/orchestrator.py`

**Secrets location:**
- `backend/.env` present (contents intentionally not read)
- `frontend/.env.local` present (contents intentionally not read)

## Webhooks & Callbacks

**Incoming:**
- None detected for third-party webhook callbacks (FastAPI routes in `backend/routes.py` are app/frontend-consumed endpoints, not vendor callback handlers)

**Outgoing:**
- HTTPS outbound calls to OpenAI, OpenWeatherMap, Open-Meteo, GNews, NewsData.io, and RSS feed URLs via `requests` in `backend/src/agents/intelligence_agent/fetching_details.py`

---

*Integration audit: 2026-04-05*
