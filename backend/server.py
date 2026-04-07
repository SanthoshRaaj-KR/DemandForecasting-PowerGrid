"""backend/server.py
=================
FastAPI entrypoint and server startup.

All legacy routes are loaded from routes.py, and v2 orchestration routes are
added here for direct frontend integration of engine.py/intelligence.py/simulator.py.

Run:
    uvicorn server:app --reload --port 8000
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Query

from routes import app
from engine import APrioriBrain
from intelligence import StochasticTrigger
from simulator import UnifiedOrchestrator

_BACKEND_DIR = Path(__file__).resolve().parent
_BRAIN = APrioriBrain(_BACKEND_DIR)
_TRIGGER = StochasticTrigger(_BACKEND_DIR)
_SIMULATOR = UnifiedOrchestrator(_BACKEND_DIR)


@app.get("/api/v2/health")
def health_v2():
    return {
        "status": "ok",
        "service": "v2_orchestration",
    }


@app.post("/api/v2/master-schedule")
def generate_master_schedule(
    start_date: str = Query(default="2026-04-01"),
    days: int = Query(default=30, ge=1, le=90),
):
    schedule = _BRAIN.generate_30_day_forecast(start_date=start_date, days=days)
    saved = _BRAIN.save_master_schedule(schedule)
    return {
        "status": "success",
        "data": schedule,
        "saved_path": str(saved),
    }


@app.get("/api/v2/intelligence/{day_index}")
def get_daily_intelligence(
    day_index: int,
    start_date: str = Query(default="2026-04-01"),
    force_refresh: bool = Query(default=False),
):
    if day_index < 0:
        return {"status": "error", "message": "day_index must be >= 0"}

    cfg = _BRAIN._load_grid_config()  # intentional internal reuse for consistency
    state_ids = list(cfg.get("nodes", {}).keys())
    date_str = (datetime.fromisoformat(start_date) + timedelta(days=day_index)).strftime("%Y-%m-%d")

    report = _TRIGGER.generate_daily_report(
        day_index=day_index,
        date_str=date_str,
        state_ids=state_ids,
        force_refresh=force_refresh,
    )
    return {
        "status": "success",
        "data": report,
    }


@app.post("/api/v2/simulate")
def run_unified_simulator(
    start_date: str = Query(default="2026-04-01"),
    days: int = Query(default=30, ge=1, le=90),
):
    result = _SIMULATOR.run(start_date=start_date, days=days)
    return {
        "status": "success",
        "data": result,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
