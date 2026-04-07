"""
Orchestration Contracts
=======================
Defines dataclasses for orchestration state, stage results, and cost accounting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class OrchestratorState(str, Enum):
    """Current state of the orchestration engine."""
    IDLE = "IDLE"
    RUNNING_BASELINE = "RUNNING_BASELINE"
    RUNNING_INTELLIGENCE = "RUNNING_INTELLIGENCE"
    RUNNING_WATERFALL = "RUNNING_WATERFALL"
    RUNNING_MEMORY = "RUNNING_MEMORY"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class WakeDecision(str, Enum):
    """Decision on whether to wake LLM agents."""
    SLEEP = "SLEEP"  # Use baseline, no LLM agents
    WAKE = "WAKE"    # Anomaly detected, run full orchestration


@dataclass
class StageResult:
    """Result from a single orchestration stage."""
    stage_number: int
    stage_name: str
    success: bool
    duration_ms: float
    output: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class CostMetrics:
    """Cost accounting for a single day."""
    date: str
    llm_agents_enabled: bool
    anomaly_detected: bool
    anomaly_magnitude_mw: float
    baseline_cost_inr: float  # Estimated cost if baseline only
    actual_cost_inr: float    # Actual cost (higher if LLM woke)
    savings_inr: float        # baseline_cost - actual_cost (if slept)
    savings_pct: float        # savings / baseline_cost * 100


@dataclass
class DailyOrchestrationResult:
    """Complete result from a single day's orchestration run."""
    date: str
    day_index: int
    wake_decision: WakeDecision
    stages_completed: List[StageResult]
    total_duration_ms: float
    cost_metrics: CostMetrics
    summary: str


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration engine."""
    delta_wake_threshold_mw: float = 50.0  # Wake LLM if Delta > 50 MW
    llm_cost_per_call_inr: float = 2.0     # Estimated cost per LLM call
    baseline_calls_per_day: int = 10       # Estimated LLM calls if awake
    enable_memory_write: bool = True
    enable_cost_tracking: bool = True
    simulation_days: int = 30


@dataclass
class OrchestrationContext:
    """Mutable context passed between stages."""
    config: OrchestrationConfig
    current_date: str
    day_index: int
    state: OrchestratorState = OrchestratorState.IDLE
    wake_decision: WakeDecision = WakeDecision.SLEEP
    baseline_schedule: Optional[Dict] = None
    intelligence_output: Optional[Dict] = None
    waterfall_result: Optional[Dict] = None
    memory_warnings: List[str] = field(default_factory=list)
    stage_results: List[StageResult] = field(default_factory=list)
    error: Optional[str] = None
