"""
Cost Tracker
============
Persists and aggregates cost metrics from orchestration runs.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .contracts import CostMetrics, DailyOrchestrationResult


class CostTracker:
    """
    Tracks and persists orchestration cost metrics.
    
    Outputs:
    - CSV file: outputs/cost_tracking.csv
    - JSON file: outputs/cost_summary.json
    """
    
    def __init__(self, output_dir: Path = Path("outputs")):
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._csv_path = self._output_dir / "cost_tracking.csv"
        self._summary_path = self._output_dir / "cost_summary.json"
        self._metrics: List[CostMetrics] = []
    
    def record(self, metrics: CostMetrics):
        """Record a single day's cost metrics."""
        self._metrics.append(metrics)
        self._append_csv(metrics)
    
    def record_batch(self, results: List[DailyOrchestrationResult]):
        """Record multiple days from orchestration results."""
        for result in results:
            self.record(result.cost_metrics)
    
    def _append_csv(self, metrics: CostMetrics):
        """Append metrics to CSV file."""
        file_exists = self._csv_path.exists()
        
        with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "llm_agents_enabled", "anomaly_detected",
                "anomaly_magnitude_mw", "baseline_cost_inr", "actual_cost_inr",
                "savings_inr", "savings_pct"
            ])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                "date": metrics.date,
                "llm_agents_enabled": metrics.llm_agents_enabled,
                "anomaly_detected": metrics.anomaly_detected,
                "anomaly_magnitude_mw": f"{metrics.anomaly_magnitude_mw:.1f}",
                "baseline_cost_inr": f"{metrics.baseline_cost_inr:.2f}",
                "actual_cost_inr": f"{metrics.actual_cost_inr:.2f}",
                "savings_inr": f"{metrics.savings_inr:.2f}",
                "savings_pct": f"{metrics.savings_pct:.1f}",
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get aggregated cost summary."""
        if not self._metrics:
            return self._load_from_csv()
        
        total_days = len(self._metrics)
        wake_days = sum(1 for m in self._metrics if m.llm_agents_enabled)
        sleep_days = total_days - wake_days
        
        total_baseline = sum(m.baseline_cost_inr for m in self._metrics)
        total_actual = sum(m.actual_cost_inr for m in self._metrics)
        total_savings = total_baseline - total_actual
        
        return {
            "total_days": total_days,
            "wake_days": wake_days,
            "sleep_days": sleep_days,
            "sleep_rate_pct": round(sleep_days / total_days * 100, 1) if total_days > 0 else 0,
            "total_baseline_cost_inr": round(total_baseline, 2),
            "total_actual_cost_inr": round(total_actual, 2),
            "total_savings_inr": round(total_savings, 2),
            "savings_pct": round(total_savings / total_baseline * 100, 1) if total_baseline > 0 else 0,
            "daily_metrics": [asdict(m) for m in self._metrics],
        }
    
    def _load_from_csv(self) -> Dict[str, Any]:
        """Load metrics from existing CSV file."""
        if not self._csv_path.exists():
            return {"total_days": 0, "daily_metrics": []}
        
        with open(self._csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {"total_days": 0, "daily_metrics": []}
        
        # Parse rows into metrics
        metrics = []
        for row in rows:
            metrics.append({
                "date": row["date"],
                "llm_agents_enabled": row["llm_agents_enabled"] == "True",
                "anomaly_detected": row["anomaly_detected"] == "True",
                "anomaly_magnitude_mw": float(row.get("anomaly_magnitude_mw", 0)),
                "baseline_cost_inr": float(row["baseline_cost_inr"]),
                "actual_cost_inr": float(row["actual_cost_inr"]),
                "savings_inr": float(row["savings_inr"]),
                "savings_pct": float(row["savings_pct"]),
            })
        
        total_days = len(metrics)
        wake_days = sum(1 for m in metrics if m["llm_agents_enabled"])
        sleep_days = total_days - wake_days
        
        total_baseline = sum(m["baseline_cost_inr"] for m in metrics)
        total_actual = sum(m["actual_cost_inr"] for m in metrics)
        total_savings = total_baseline - total_actual
        
        return {
            "total_days": total_days,
            "wake_days": wake_days,
            "sleep_days": sleep_days,
            "sleep_rate_pct": round(sleep_days / total_days * 100, 1) if total_days > 0 else 0,
            "total_baseline_cost_inr": round(total_baseline, 2),
            "total_actual_cost_inr": round(total_actual, 2),
            "total_savings_inr": round(total_savings, 2),
            "savings_pct": round(total_savings / total_baseline * 100, 1) if total_baseline > 0 else 0,
            "daily_metrics": metrics,
        }
    
    def save_summary(self):
        """Save summary to JSON file."""
        summary = self.get_summary()
        with open(self._summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    
    def clear(self):
        """Clear in-memory metrics and CSV file."""
        self._metrics.clear()
        if self._csv_path.exists():
            self._csv_path.unlink()
        if self._summary_path.exists():
            self._summary_path.unlink()
