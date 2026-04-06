"""
LLM Parameter Autopsy: Recursive Hyperparameter Optimization
============================================================

PATENT FEATURE #1: "Agentic Recursive Hyperparameter Optimization"

Industry Standard Problem:
- Grids use Reinforcement Learning or Neural Networks to "learn"
- Requires millions of data rows, backpropagation
- Acts as a completely unexplainable black box

Our Novelty:
- Pure Agentic Reflection (no neural networks)
- At end of 30-day cycle, LLM Overseer reads XAI plain-text logs
- Reasons about WHY the grid failed
- Autonomously outputs JSON that rewrites Python hyperparameters
- Self-learning WITHOUT neural networks

This is the "brain" that closes the loop on the 4-stage workflow,
using plain-text reasoning to evolve the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


@dataclass
class HyperParameter:
    """A tunable hyperparameter in the grid system."""
    name: str
    current_value: float
    min_value: float
    max_value: float
    step_size: float
    description: str
    last_modified: Optional[str] = None
    modification_reason: Optional[str] = None


@dataclass
class FailurePattern:
    """A detected failure pattern from XAI logs."""
    pattern_type: str
    frequency: int  # How many times it occurred
    severity: float  # 0-10 scale
    affected_states: List[str]
    root_causes: List[str]
    suggested_param_changes: List[str]


@dataclass
class AutopsyReport:
    """Monthly autopsy report with reasoning and recommendations."""
    month: str
    total_days_analyzed: int
    total_failures: int
    total_load_shedding_mw: float
    failure_rate_pct: float
    detected_patterns: List[FailurePattern]
    recommended_changes: List[Dict[str, Any]]
    reasoning_chain: List[str]  # Chain-of-thought reasoning
    json_output_path: Optional[str] = None


@dataclass
class ParameterPatch:
    """A patch to apply to hyperparameters."""
    param_name: str
    old_value: float
    new_value: float
    change_pct: float
    reasoning: str
    confidence: float  # 0-1


class LLMParameterAutopsy:
    """
    Implements Agentic Recursive Hyperparameter Optimization.
    
    This is the "Overseer" that performs monthly autopsy of grid failures
    and autonomously generates parameter adjustments without using
    neural networks or gradient-based optimization.
    
    Process:
    1. Collect XAI logs from the month
    2. Parse failure patterns from plain-text
    3. Apply rule-based reasoning to identify root causes
    4. Generate parameter patches with chain-of-thought rationale
    5. Export JSON that can be applied to system configuration
    
    Key Innovation:
    - No backpropagation or gradient descent
    - No training data requirements
    - Fully explainable via chain-of-thought
    - Human-reviewable before application
    """
    
    def __init__(self, config_path: str = "config/hyperparameters.json"):
        self.config_path = config_path
        self.parameters: Dict[str, HyperParameter] = {}
        self.autopsy_history: List[AutopsyReport] = []
        self._initialize_default_parameters()
    
    def _initialize_default_parameters(self) -> None:
        """Initialize the tunable hyperparameters."""
        defaults = [
            HyperParameter(
                name="dr_bounty_price_inr",
                current_value=6.0,
                min_value=2.0,
                max_value=15.0,
                step_size=0.5,
                description="Base price for DR bounty auctions (INR/MW)",
            ),
            HyperParameter(
                name="battery_precharge_threshold_pct",
                current_value=50.0,
                min_value=30.0,
                max_value=90.0,
                step_size=5.0,
                description="Minimum SOC to maintain before peak hours (%)",
            ),
            HyperParameter(
                name="edge_capacity_buffer_pct",
                current_value=10.0,
                min_value=5.0,
                max_value=25.0,
                step_size=2.5,
                description="Buffer to leave on transmission edges (%)",
            ),
            HyperParameter(
                name="lifeboat_frequency_threshold_hz",
                current_value=49.7,
                min_value=49.5,
                max_value=49.9,
                step_size=0.05,
                description="Frequency threshold to trigger Lifeboat Protocol",
            ),
            HyperParameter(
                name="max_trade_size_mw",
                current_value=100.0,
                min_value=50.0,
                max_value=200.0,
                step_size=10.0,
                description="Maximum single trade size in MW",
            ),
            HyperParameter(
                name="memory_window_days",
                current_value=3.0,
                min_value=1.0,
                max_value=7.0,
                step_size=1.0,
                description="Days of memory to retain for learning",
            ),
            HyperParameter(
                name="dr_participation_target_pct",
                current_value=60.0,
                min_value=40.0,
                max_value=90.0,
                step_size=5.0,
                description="Target prosumer participation rate (%)",
            ),
            HyperParameter(
                name="deficit_alert_threshold_mw",
                current_value=50.0,
                min_value=20.0,
                max_value=100.0,
                step_size=10.0,
                description="Deficit level to trigger LLM orchestrator wake",
            ),
        ]
        
        for param in defaults:
            self.parameters[param.name] = param
    
    def analyze_month(
        self,
        month_str: str,
        daily_summaries: List[Dict[str, Any]],
        xai_traces: List[Dict[str, Any]],
        memory_warnings: List[str],
    ) -> AutopsyReport:
        """
        Perform monthly autopsy analysis.
        
        This is the core "Agentic Reflection" that reads plain-text logs
        and reasons about why the grid failed.
        
        Parameters
        ----------
        month_str : str
            Month identifier (e.g., "2025-01")
        daily_summaries : List[Dict]
            Daily Phase8Summary data
        xai_traces : List[Dict]
            XAI Phase Trace JSON data
        memory_warnings : List[str]
            Memory warnings from the 3-day sliding window
            
        Returns
        -------
        AutopsyReport
            Complete autopsy with detected patterns and recommendations
        """
        print("\n" + "🧠" * 30)
        print(f"LLM PARAMETER AUTOPSY - Month: {month_str}")
        print("🧠" * 30)
        
        # Phase 1: Aggregate metrics
        total_days = len(daily_summaries)
        total_shedding = sum(s.get("load_shedding_mw", 0) for s in daily_summaries)
        failure_days = sum(1 for s in daily_summaries if s.get("load_shedding_mw", 0) > 0)
        failure_rate = (failure_days / total_days * 100) if total_days > 0 else 0
        
        print(f"\n  [PHASE 1] Metrics aggregation")
        print(f"    Days analyzed: {total_days}")
        print(f"    Failure days: {failure_days}")
        print(f"    Total load shedding: {total_shedding:.0f} MW")
        print(f"    Failure rate: {failure_rate:.1f}%")
        
        # Phase 2: Pattern detection
        print(f"\n  [PHASE 2] Pattern detection from {len(memory_warnings)} warnings")
        patterns = self._detect_failure_patterns(
            daily_summaries, xai_traces, memory_warnings
        )
        
        for pattern in patterns:
            print(f"    - {pattern.pattern_type}: {pattern.frequency} occurrences, severity {pattern.severity:.1f}")
        
        # Phase 3: Chain-of-thought reasoning
        print(f"\n  [PHASE 3] Chain-of-thought reasoning")
        reasoning_chain = self._generate_reasoning_chain(
            patterns, total_shedding, failure_rate
        )
        
        for i, step in enumerate(reasoning_chain):
            print(f"    {i+1}. {step}")
        
        # Phase 4: Generate parameter recommendations
        print(f"\n  [PHASE 4] Generating parameter patches")
        recommended_changes = self._generate_parameter_patches(patterns, reasoning_chain)
        
        for change in recommended_changes:
            print(f"    - {change['param']}: {change['old']} → {change['new']} ({change['reasoning'][:50]}...)")
        
        report = AutopsyReport(
            month=month_str,
            total_days_analyzed=total_days,
            total_failures=failure_days,
            total_load_shedding_mw=total_shedding,
            failure_rate_pct=failure_rate,
            detected_patterns=patterns,
            recommended_changes=recommended_changes,
            reasoning_chain=reasoning_chain,
        )
        
        self.autopsy_history.append(report)
        
        print("\n" + "=" * 60)
        print("AUTOPSY COMPLETE")
        print("=" * 60)
        print(f"  Patterns detected: {len(patterns)}")
        print(f"  Parameters to adjust: {len(recommended_changes)}")
        print("🧠" * 30 + "\n")
        
        return report
    
    def _detect_failure_patterns(
        self,
        summaries: List[Dict],
        traces: List[Dict],
        warnings: List[str],
    ) -> List[FailurePattern]:
        """Detect failure patterns from XAI data using rule-based analysis."""
        patterns: List[FailurePattern] = []
        
        # Pattern 1: Thermal bottleneck
        thermal_warnings = [w for w in warnings if "THERMAL" in w.upper() or "thermal" in w]
        if thermal_warnings:
            patterns.append(FailurePattern(
                pattern_type="THERMAL_BOTTLENECK",
                frequency=len(thermal_warnings),
                severity=min(len(thermal_warnings) * 2, 10),
                affected_states=self._extract_states_from_warnings(thermal_warnings),
                root_causes=["Edge capacity exceeded", "Insufficient transmission buffer"],
                suggested_param_changes=["INCREASE edge_capacity_buffer_pct by 10%"],
            ))
        
        # Pattern 2: Battery depletion
        battery_warnings = [w for w in warnings if "BATTERY" in w.upper() or "SOC" in w.upper()]
        if battery_warnings:
            patterns.append(FailurePattern(
                pattern_type="BATTERY_DEPLETION",
                frequency=len(battery_warnings),
                severity=min(len(battery_warnings) * 1.5, 10),
                affected_states=self._extract_states_from_warnings(battery_warnings),
                root_causes=["Battery not pre-charged", "Peak demand exceeded storage"],
                suggested_param_changes=["INCREASE battery_precharge_threshold_pct by 20%"],
            ))
        
        # Pattern 3: DR insufficient
        dr_failures = sum(
            1 for s in summaries 
            if s.get("dr_resolved_mw", 0) < s.get("total_deficit_mw", 1) * 0.15
        )
        if dr_failures > len(summaries) * 0.2:  # More than 20% of days
            patterns.append(FailurePattern(
                pattern_type="DR_INSUFFICIENT",
                frequency=dr_failures,
                severity=min(dr_failures / len(summaries) * 10, 10) if summaries else 0,
                affected_states=["ALL"],
                root_causes=["DR bounty price too low", "Low prosumer participation"],
                suggested_param_changes=[
                    "INCREASE dr_bounty_price_inr by 25%",
                    "INCREASE dr_participation_target_pct by 15%",
                ],
            ))
        
        # Pattern 4: Frequent load shedding
        shedding_days = sum(1 for s in summaries if s.get("load_shedding_mw", 0) > 0)
        if shedding_days > len(summaries) * 0.1:  # More than 10% of days
            patterns.append(FailurePattern(
                pattern_type="FREQUENT_SHEDDING",
                frequency=shedding_days,
                severity=min(shedding_days / len(summaries) * 15, 10) if summaries else 0,
                affected_states=["MULTIPLE"],
                root_causes=["Waterfall sequence insufficient", "Delta detection too late"],
                suggested_param_changes=[
                    "DECREASE deficit_alert_threshold_mw by 20%",
                    "INCREASE memory_window_days by 1",
                ],
            ))
        
        # Pattern 5: Trade failures (from XAI traces)
        trade_failures = sum(
            1 for t in traces 
            if any(
                step.get("success") is False 
                for step in t.get("phase_trace", [])
            )
        )
        if trade_failures > 0:
            patterns.append(FailurePattern(
                pattern_type="TRADE_EXECUTION_FAILURE",
                frequency=trade_failures,
                severity=min(trade_failures * 3, 10),
                affected_states=["MULTIPLE"],
                root_causes=["Trade size too large", "Edge capacity mismatch"],
                suggested_param_changes=["DECREASE max_trade_size_mw by 15%"],
            ))
        
        return patterns
    
    def _extract_states_from_warnings(self, warnings: List[str]) -> List[str]:
        """Extract state names from warning strings."""
        states = ["UP", "Bihar", "WB", "Karnataka"]
        found = set()
        for warning in warnings:
            for state in states:
                if state in warning:
                    found.add(state)
        return list(found) if found else ["UNKNOWN"]
    
    def _generate_reasoning_chain(
        self,
        patterns: List[FailurePattern],
        total_shedding: float,
        failure_rate: float,
    ) -> List[str]:
        """Generate chain-of-thought reasoning about failures."""
        reasoning = []
        
        # Step 1: Assess overall health
        if failure_rate < 5:
            reasoning.append(f"The grid performed well with only {failure_rate:.1f}% failure rate. Minor optimizations possible.")
        elif failure_rate < 15:
            reasoning.append(f"The grid had moderate issues with {failure_rate:.1f}% failure rate. Several parameters need adjustment.")
        else:
            reasoning.append(f"The grid had significant problems with {failure_rate:.1f}% failure rate. Major parameter changes required.")
        
        # Step 2: Identify primary failure mode
        if patterns:
            primary = max(patterns, key=lambda p: p.severity)
            reasoning.append(f"Primary failure mode identified: {primary.pattern_type} (severity: {primary.severity:.1f}/10)")
            reasoning.append(f"Root causes: {', '.join(primary.root_causes)}")
        else:
            reasoning.append("No significant failure patterns detected.")
        
        # Step 3: Analyze shedding impact
        if total_shedding > 0:
            reasoning.append(f"Total load shedding of {total_shedding:.0f} MW indicates resource allocation gaps.")
            if total_shedding > 500:
                reasoning.append("CRITICAL: High shedding volume suggests systemic issues requiring aggressive parameter changes.")
        
        # Step 4: Cross-pattern analysis
        pattern_types = [p.pattern_type for p in patterns]
        if "THERMAL_BOTTLENECK" in pattern_types and "DR_INSUFFICIENT" in pattern_types:
            reasoning.append("Combined thermal and DR issues suggest need for both transmission buffering AND higher DR incentives.")
        
        if "BATTERY_DEPLETION" in pattern_types and "FREQUENT_SHEDDING" in pattern_types:
            reasoning.append("Battery issues leading to shedding - prioritize pre-charging optimization.")
        
        # Step 5: Recommendation synthesis
        reasoning.append("Synthesizing parameter adjustments based on above analysis...")
        
        return reasoning
    
    def _generate_parameter_patches(
        self,
        patterns: List[FailurePattern],
        reasoning: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate concrete parameter patches based on patterns."""
        patches: List[Dict[str, Any]] = []
        
        # Deduplicate suggested changes across patterns
        all_suggestions: Dict[str, int] = {}  # suggestion -> frequency
        for pattern in patterns:
            for suggestion in pattern.suggested_param_changes:
                all_suggestions[suggestion] = all_suggestions.get(suggestion, 0) + 1
        
        # Parse suggestions and create patches
        for suggestion, freq in all_suggestions.items():
            patch = self._parse_suggestion_to_patch(suggestion)
            if patch:
                patch["frequency"] = freq
                patch["confidence"] = min(freq / len(patterns), 1.0) if patterns else 0.5
                patches.append(patch)
        
        # Sort by confidence
        patches.sort(key=lambda p: p.get("confidence", 0), reverse=True)
        
        return patches
    
    def _parse_suggestion_to_patch(self, suggestion: str) -> Optional[Dict[str, Any]]:
        """Parse a natural language suggestion into a parameter patch."""
        # Parse patterns like "INCREASE edge_capacity_buffer_pct by 10%"
        parts = suggestion.split()
        
        if len(parts) < 4:
            return None
        
        action = parts[0].upper()  # INCREASE or DECREASE
        param_name = parts[1]
        
        if param_name not in self.parameters:
            return None
        
        param = self.parameters[param_name]
        
        # Extract percentage change
        try:
            change_pct = float(parts[-1].replace("%", ""))
        except ValueError:
            change_pct = 10.0  # Default 10%
        
        # Calculate new value
        if action == "INCREASE":
            change = param.current_value * (change_pct / 100)
            new_value = min(param.current_value + change, param.max_value)
        elif action == "DECREASE":
            change = param.current_value * (change_pct / 100)
            new_value = max(param.current_value - change, param.min_value)
        else:
            return None
        
        # Round to step size
        new_value = round(new_value / param.step_size) * param.step_size
        
        return {
            "param": param_name,
            "old": param.current_value,
            "new": new_value,
            "change_pct": (new_value - param.current_value) / param.current_value * 100,
            "reasoning": suggestion,
            "description": param.description,
        }
    
    def apply_patches(
        self,
        patches: List[Dict[str, Any]],
        require_approval: bool = True,
    ) -> Dict[str, ParameterPatch]:
        """
        Apply parameter patches to the system.
        
        Parameters
        ----------
        patches : List[Dict]
            Patches to apply
        require_approval : bool
            If True, just export for human review. If False, apply directly.
            
        Returns
        -------
        Dict[str, ParameterPatch]
            Applied patches
        """
        applied: Dict[str, ParameterPatch] = {}
        
        for patch in patches:
            param_name = patch["param"]
            if param_name not in self.parameters:
                continue
            
            param = self.parameters[param_name]
            
            applied_patch = ParameterPatch(
                param_name=param_name,
                old_value=param.current_value,
                new_value=patch["new"],
                change_pct=patch["change_pct"],
                reasoning=patch["reasoning"],
                confidence=patch.get("confidence", 0.5),
            )
            
            if not require_approval:
                # Apply the change
                param.current_value = patch["new"]
                param.last_modified = datetime.now().isoformat()
                param.modification_reason = patch["reasoning"]
            
            applied[param_name] = applied_patch
        
        return applied
    
    def export_autopsy_json(
        self,
        report: AutopsyReport,
        output_dir: str = "outputs",
    ) -> str:
        """
        Export autopsy report and parameter patches to JSON.
        
        This JSON can be:
        1. Reviewed by humans before application
        2. Applied automatically to update system config
        3. Audited for regulatory compliance
        """
        output = {
            "protocol": "LLM Parameter Autopsy - Agentic Recursive Hyperparameter Optimization",
            "patent_claim": "Self-learning without neural networks via plain-text reasoning",
            "metadata": {
                "month": report.month,
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
            },
            "summary": {
                "days_analyzed": report.total_days_analyzed,
                "failure_days": report.total_failures,
                "failure_rate_pct": report.failure_rate_pct,
                "total_load_shedding_mw": report.total_load_shedding_mw,
            },
            "detected_patterns": [
                {
                    "type": p.pattern_type,
                    "frequency": p.frequency,
                    "severity": p.severity,
                    "affected_states": p.affected_states,
                    "root_causes": p.root_causes,
                }
                for p in report.detected_patterns
            ],
            "reasoning_chain": report.reasoning_chain,
            "parameter_patches": report.recommended_changes,
            "current_parameters": {
                name: {
                    "current_value": param.current_value,
                    "min": param.min_value,
                    "max": param.max_value,
                    "description": param.description,
                }
                for name, param in self.parameters.items()
            },
            "application_status": "PENDING_HUMAN_REVIEW",
            "compliance_note": "All changes derived from explainable chain-of-thought reasoning. No black-box optimization.",
        }
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"parameter_autopsy_{report.month}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        report.json_output_path = filepath
        
        print(f"  [AUTOPSY] Report exported: {filepath}")
        return filepath
    
    def get_parameters_dict(self) -> Dict[str, float]:
        """Get current parameter values as a simple dict."""
        return {name: param.current_value for name, param in self.parameters.items()}
