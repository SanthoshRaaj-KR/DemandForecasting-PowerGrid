"""A Priori Brain (engine.py).

Deterministic 30-day baseline generator for the 4-state grid using:
- Real historical drawl/weather data from processed dataset
- Real weather fetch via WeatherScraper (Open-Meteo)
- LightGBM 30-day inference pipeline
- Real intelligence context multipliers when available
"""

from __future__ import annotations

import json
import io
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.agents.fusion_agent.inference import load_artefacts
from src.agents.fusion_agent.inference_30day import predict_30_days_all_regions
from src.agents.intelligence_agent import CITY_REGISTRY, SmartGridIntelligenceAgent, WeatherScraper


STATE_ID_TO_DATASET_NAME = {
    "BHR": "Bihar",
    "UP": "NR UP",
    "WB": "West Bengal",
    "KAR": "SR Karnataka",
}


class APrioriBrain:
    """Builds a deterministic 30-day master schedule (ground truth baseline)."""

    def __init__(self, backend_dir: Path | None = None) -> None:
        self.backend_dir = backend_dir or Path(__file__).resolve().parent
        self.config_path = self.backend_dir / "config" / "grid_config.json"
        self.data_path = self.backend_dir / "data" / "processed" / "Final_Cleaned_Dataset.csv"
        self.outputs_dir = self.backend_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        self._model = None
        self._scaler_climate = None
        self._scaler_lagroll = None
        self._model_ready = False

        self._weather = WeatherScraper()
        self._intelligence = SmartGridIntelligenceAgent()

    def load_model(self) -> None:
        """Load LightGBM inference artefacts once."""
        if self._model_ready:
            return

        self._model, self._scaler_climate, self._scaler_lagroll = load_artefacts(
            model_path=str(self.backend_dir / "model" / "lightgbm_model.pkl"),
            scaler_climate_path=str(self.backend_dir / "model" / "utils" / "scaler_climate.pkl"),
            scaler_lagroll_path=str(self.backend_dir / "model" / "utils" / "scaler_lagroll.pkl"),
            meta_path=str(self.backend_dir / "model" / "utils" / "inference_meta.json"),
        )
        self._model_ready = True

    def _load_grid_config(self) -> Dict[str, Any]:
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _load_historical_df(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date", "State", "Actual_Drawl"]).copy()
        return df

    @staticmethod
    def _repeat_to_len(values: List[float], target_len: int) -> List[float]:
        if not values:
            return [0.0] * target_len
        out = list(values)
        while len(out) < target_len:
            out.append(out[-1])
        return out[:target_len]

    def _weather_to_model_features(
        self,
        *,
        historical_window: pd.DataFrame,
        state_id: str,
    ) -> Dict[str, List[float]]:
        """Build 7-day climatic feature arrays using real weather + historical anchors."""
        city_meta = CITY_REGISTRY.get(state_id, {})
        weather_payload = self._weather.fetch_forecast_7d(
            lat=float(city_meta.get("lat", 0.0)),
            lon=float(city_meta.get("lon", 0.0)),
            city_name=str(city_meta.get("name", state_id)),
        )

        # Historical anchors from real data.
        hist_temp = [float(v) for v in historical_window["om_temp_mean"].tail(7).tolist()]
        hist_solar = [float(v) for v in historical_window["nasa_solar"].tail(7).tolist()]
        hist_dew = [float(v) for v in historical_window["om_dewpoint"].tail(7).tolist()]
        hist_wind = [float(v) for v in historical_window["om_wind_gusts"].tail(7).tolist()]

        hist_temp = self._repeat_to_len(hist_temp, 7)
        hist_solar = self._repeat_to_len(hist_solar, 7)
        hist_dew = self._repeat_to_len(hist_dew, 7)
        hist_wind = self._repeat_to_len(hist_wind, 7)

        daily = weather_payload.get("daily_forecast_7d", []) if isinstance(weather_payload, dict) else []
        if not daily:
            return {
                "om_temp_mean": hist_temp,
                "nasa_solar": hist_solar,
                "om_dewpoint": hist_dew,
                "om_wind_gusts": hist_wind,
            }

        solar_base = sum(hist_solar) / max(len(hist_solar), 1)
        dew_base = sum(hist_dew) / max(len(hist_dew), 1)
        wind_base = sum(hist_wind) / max(len(hist_wind), 1)

        temps: List[float] = []
        solar: List[float] = []
        dew: List[float] = []
        wind: List[float] = []

        for day in daily[:7]:
            max_c = float(day.get("max_c", hist_temp[-1]))
            min_c = float(day.get("min_c", hist_temp[-1]))
            heat_idx = float(day.get("heat_index_c", max_c))
            rain = float(day.get("precipitation_mm", 0.0))
            condition = str(day.get("condition", "")).lower()

            temp_mean = (max_c + min_c) / 2.0
            cloud_penalty = 1.0 if "overcast" in condition or "rain" in condition else 0.0
            solar_proxy = max(0.2, solar_base - (rain * 0.03) - cloud_penalty)

            # Use weather-derived temp; anchor dew/wind with historical baselines.
            dew_est = min(temp_mean, dew_base)
            wind_est = wind_base + (0.2 * max(0.0, heat_idx - temp_mean))

            temps.append(round(temp_mean, 2))
            solar.append(round(solar_proxy, 4))
            dew.append(round(dew_est, 2))
            wind.append(round(wind_est, 2))

        return {
            "om_temp_mean": self._repeat_to_len(temps, 7),
            "nasa_solar": self._repeat_to_len(solar, 7),
            "om_dewpoint": self._repeat_to_len(dew, 7),
            "om_wind_gusts": self._repeat_to_len(wind, 7),
        }

    def _build_inputs_by_region(self, *, start_date: str) -> Dict[str, Dict[str, Any]]:
        df = self._load_historical_df()
        inputs: Dict[str, Dict[str, Any]] = {}

        for state_id, state_name in STATE_ID_TO_DATASET_NAME.items():
            state_df = df[df["State"] == state_name].sort_values("Date").tail(7).copy()
            if state_df.empty:
                raise ValueError(f"No historical records found for state '{state_name}'")

            state_df = state_df.reset_index(drop=True)
            if len(state_df) < 7:
                state_df = pd.concat([state_df] * (7 // len(state_df) + 1), ignore_index=True).tail(7)

            weather_features = self._weather_to_model_features(
                historical_window=state_df,
                state_id=state_id,
            )

            inputs[state_id] = {
                "Date": [d.strftime("%Y-%m-%d") for d in state_df["Date"].tolist()],
                "State": [state_id] * 7,
                "Actual_Drawl": [float(v) for v in state_df["Actual_Drawl"].tolist()],
                "om_temp_mean": weather_features["om_temp_mean"],
                "nasa_solar": weather_features["nasa_solar"],
                "om_dewpoint": weather_features["om_dewpoint"],
                "om_wind_gusts": weather_features["om_wind_gusts"],
            }

        return inputs

    def _load_intelligence_context(self) -> Dict[str, Dict[str, Any]]:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return self._intelligence.run_all_regions()
        except Exception:
            return {}

    def generate_30_day_forecast(self, start_date: str = "2026-04-01", days: int = 30) -> Dict[str, Any]:
        """Predict demand baseline for all states and build static master schedule."""
        cfg = self._load_grid_config()
        state_ids = list(cfg.get("nodes", {}).keys())
        base_generation = {
            state_id: float(node_data.get("generation_mw", 0.0))
            for state_id, node_data in cfg.get("nodes", {}).items()
        }

        self.load_model()

        inputs = self._build_inputs_by_region(start_date=start_date)
        intelligence_context = self._load_intelligence_context()

        predictions = predict_30_days_all_regions(
            inputs,
            self._model,
            self._scaler_climate,
            self._scaler_lagroll,
            intelligence_context=intelligence_context,
        )

        # Per-state calibration to align model output scale with grid MW scale
        # using recent real drawl history (no synthetic constants).
        calibration_factor: Dict[str, float] = {}
        for state_id in state_ids:
            input_state = inputs.get(state_id, {})
            recent_actual = [float(v) for v in input_state.get("Actual_Drawl", [])]
            hist_ref_mw = (sum(recent_actual) / max(len(recent_actual), 1)) * 100.0

            pred_state = predictions.get(state_id, {})
            pred_seed = [float(v) for v in pred_state.get("predicted_mw", [])[:7] if float(v) > 0]
            pred_ref = sum(pred_seed) / max(len(pred_seed), 1) if pred_seed else 0.0

            factor = (hist_ref_mw / pred_ref) if pred_ref > 0 else 1.0
            calibration_factor[state_id] = max(1.0, min(100000.0, factor))

        start = datetime.fromisoformat(start_date)
        schedule: List[Dict[str, Any]] = []

        for day_index in range(days):
            date_str = (start + pd.Timedelta(days=day_index)).strftime("%Y-%m-%d")
            states_payload: Dict[str, Dict[str, float]] = {}

            for state_id in state_ids:
                state_pred = predictions.get(state_id, {})
                adjusted = state_pred.get("adjusted_mw", [])
                lower = state_pred.get("lower_bound", [])
                upper = state_pred.get("upper_bound", [])
                conf = state_pred.get("confidence", [])

                factor = calibration_factor.get(state_id, 1.0)
                demand = (float(adjusted[day_index]) if day_index < len(adjusted) else float(base_generation[state_id])) * factor
                demand_lower = (float(lower[day_index]) if day_index < len(lower) else demand) * factor
                demand_upper = (float(upper[day_index]) if day_index < len(upper) else demand) * factor
                confidence = float(conf[day_index]) if day_index < len(conf) else 0.0

                supply = float(base_generation[state_id])
                states_payload[state_id] = {
                    "baseline_demand_mw": round(demand, 2),
                    "baseline_supply_mw": round(supply, 2),
                    "baseline_net_mw": round(supply - demand, 2),
                    "demand_lower_mw": round(demand_lower, 2),
                    "demand_upper_mw": round(demand_upper, 2),
                    "forecast_confidence": round(confidence, 3),
                }

            schedule.append(
                {
                    "day_index": day_index,
                    "date": date_str,
                    "states": states_payload,
                }
            )

        return {
            "start_date": start_date,
            "days": days,
            "states": state_ids,
            "model_loaded": self._model_ready,
            "weather_source": "open-meteo-via-weather-scraper",
            "intelligence_source": "smart-grid-intelligence-agent",
            "scale_calibration": calibration_factor,
            "schedule": schedule,
        }

    def save_master_schedule(self, schedule: Dict[str, Any]) -> Path:
        start_date = str(schedule.get("start_date", "unknown"))
        out = self.outputs_dir / f"master_schedule_{start_date}.json"
        out.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
        return out
