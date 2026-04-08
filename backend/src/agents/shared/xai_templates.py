"""
XAI Template Engine - Human-Readable Summary Generation
=========================================================
Converts technical grid data into plain-language explanations
for executives, regulators, and general public.

Design: Backend returns both plain_summary and technical_details (D-15)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class PanelData:
    """Data for a single dashboard panel."""
    title: str  # "NOW", "PREDICTED", "RISK WATCH"
    icon: str  # "🔴", "🟡", "⚠️"
    headline: str  # Main message (1-2 sentences)
    bullet_points: List[str]  # Supporting details
    severity: str  # "info", "warning", "critical"
    timestamp: str  # When this was computed


@dataclass
class XAIOutput:
    """Complete XAI output for frontend consumption."""
    plain_summary: str  # 2-3 sentence executive summary
    technical_details: str  # Full technical breakdown
    panels: Dict[str, PanelData]  # "now", "predicted", "risk_watch"
    computed_at: str


# Template patterns for human-readable text
TRADE_TEMPLATES = {
    "export": "{seller} is sending {mw}MW to {buyer}",
    "import": "{buyer} is receiving {mw}MW from {seller}",
    "auction": "{buyer} won {mw}MW at ₹{price}/kWh in demand response auction",
    "battery": "{state} is discharging {mw}MW from battery storage",
}

PREDICTION_TEMPLATES = {
    "deficit": "{state} likely to face {mw}MW shortfall by {time}",
    "surplus": "{state} expected to have {mw}MW excess by {time}",
    "peak": "Peak demand in {state} projected at {time} ({mw}MW)",
}

RISK_TEMPLATES = {
    "weather": "Weather alert in {state}: {event} may impact {mw}MW capacity",
    "maintenance": "Scheduled maintenance in {state} at {time} - {mw}MW offline",
    "overload": "Transmission line {line} at {pct}% capacity - rerouting recommended",
    "stimulus": "{event_type} in {state}: {description}",
}

LIFEBOAT_TEMPLATES = {
    "warning": "⚡ Frequency dropped to {freq}Hz - monitoring closely",
    "active": "🚨 LIFEBOAT PROTOCOL ACTIVE: {state} isolated to protect grid stability",
    "recovered": "✅ Frequency recovered to {freq}Hz - normal operations resumed",
}


class XAITemplateEngine:
    """
    Generates human-readable summaries from technical grid data.
    
    Usage:
        engine = XAITemplateEngine()
        output = engine.generate(
            trades=[...],
            predictions=[...],
            risk_flags=[...],
            frequency=49.8,
        )
        # output.plain_summary = "Karnataka is exporting 200MW to UP..."
        # output.panels["now"].headline = "Active power trades in progress"
    """
    
    def __init__(self):
        self._audience = "executive"  # or "regulator", "technical"
    
    def generate(
        self,
        trades: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        risk_flags: List[Dict[str, Any]],
        frequency: float,
        lifeboat_status: Optional[str] = None,
    ) -> XAIOutput:
        """Generate complete XAI output with all panels."""
        
        # Generate NOW panel
        now_panel = self._generate_now_panel(trades, frequency, lifeboat_status)
        
        # Generate PREDICTED panel
        predicted_panel = self._generate_predicted_panel(predictions)
        
        # Generate RISK WATCH panel
        risk_panel = self._generate_risk_panel(risk_flags)
        
        # Generate plain summary (2-3 sentences)
        plain_summary = self._generate_plain_summary(now_panel, predicted_panel, risk_panel)
        
        # Generate technical details (full breakdown)
        technical_details = self._generate_technical_details(
            trades, predictions, risk_flags, frequency
        )
        
        return XAIOutput(
            plain_summary=plain_summary,
            technical_details=technical_details,
            panels={
                "now": now_panel,
                "predicted": predicted_panel,
                "risk_watch": risk_panel,
            },
            computed_at=datetime.now().isoformat(),
        )
    
    def _generate_now_panel(
        self,
        trades: List[Dict[str, Any]],
        frequency: float,
        lifeboat_status: Optional[str],
    ) -> PanelData:
        """Generate the NOW panel showing current state."""
        bullet_points = []
        severity = "info"
        
        # Check lifeboat status first (highest priority)
        if lifeboat_status == "active":
            headline = "⚡ Emergency Protocol Active"
            severity = "critical"
            bullet_points.append(LIFEBOAT_TEMPLATES["active"].format(
                state="affected region"
            ))
        elif frequency < 49.5:
            headline = "⚠️ Grid Frequency Below Normal"
            severity = "warning"
            bullet_points.append(LIFEBOAT_TEMPLATES["warning"].format(freq=frequency))
        else:
            headline = "Grid Operating Normally"
        
        # Add active trades
        if trades:
            total_mw = sum(t.get("mw", 0) for t in trades)
            headline = f"{len(trades)} Active Power Transfers ({total_mw:.0f}MW total)"
            
            for trade in trades[:3]:  # Show top 3
                bullet_points.append(TRADE_TEMPLATES["export"].format(
                    seller=trade.get("seller", "Unknown"),
                    buyer=trade.get("buyer", "Unknown"),
                    mw=trade.get("mw", 0),
                ))
        
        return PanelData(
            title="NOW",
            icon="🔴",
            headline=headline,
            bullet_points=bullet_points,
            severity=severity,
            timestamp=datetime.now().strftime("%H:%M"),
        )
    
    def _generate_predicted_panel(self, predictions: List[Dict[str, Any]]) -> PanelData:
        """Generate the PREDICTED panel showing forecasts."""
        bullet_points = []
        severity = "info"
        
        if not predictions:
            return PanelData(
                title="PREDICTED",
                icon="🟡",
                headline="No significant changes expected",
                bullet_points=["All states within normal operating range"],
                severity="info",
                timestamp=datetime.now().strftime("%H:%M"),
            )
        
        # Find the most significant prediction
        deficits = [p for p in predictions if p.get("type") == "deficit"]
        surpluses = [p for p in predictions if p.get("type") == "surplus"]
        
        if deficits:
            worst = max(deficits, key=lambda x: x.get("mw", 0))
            headline = f"{worst.get('state', 'Unknown')} may need {worst.get('mw', 0):.0f}MW by {worst.get('time', 'soon')}"
            severity = "warning"
            
            for pred in deficits[:3]:
                bullet_points.append(PREDICTION_TEMPLATES["deficit"].format(
                    state=pred.get("state", "Unknown"),
                    mw=pred.get("mw", 0),
                    time=pred.get("time", "soon"),
                ))
        else:
            headline = "Adequate supply forecasted for all states"
            for pred in surpluses[:3]:
                bullet_points.append(PREDICTION_TEMPLATES["surplus"].format(
                    state=pred.get("state", "Unknown"),
                    mw=pred.get("mw", 0),
                    time=pred.get("time", "soon"),
                ))
        
        return PanelData(
            title="PREDICTED",
            icon="🟡",
            headline=headline,
            bullet_points=bullet_points,
            severity=severity,
            timestamp=datetime.now().strftime("%H:%M"),
        )
    
    def _generate_risk_panel(self, risk_flags: List[Dict[str, Any]]) -> PanelData:
        """Generate the RISK WATCH panel showing potential issues."""
        bullet_points = []
        severity = "info"
        
        if not risk_flags:
            return PanelData(
                title="RISK WATCH",
                icon="⚠️",
                headline="No active risk indicators",
                bullet_points=["All monitored conditions normal"],
                severity="info",
                timestamp=datetime.now().strftime("%H:%M"),
            )
        
        # Group by severity
        high_risks = [r for r in risk_flags if r.get("severity") in ["HIGH", "CRITICAL"]]
        
        if high_risks:
            headline = f"{len(high_risks)} High-Priority Risks Detected"
            severity = "warning" if len(high_risks) < 3 else "critical"
        else:
            headline = f"{len(risk_flags)} Potential Issues Being Monitored"
        
        for risk in risk_flags[:4]:  # Show top 4
            template_key = risk.get("source", "stimulus")
            template = RISK_TEMPLATES.get(template_key, RISK_TEMPLATES["stimulus"])
            
            try:
                bullet_points.append(template.format(
                    state=risk.get("state", "Unknown"),
                    event=risk.get("event_type", "event"),
                    event_type=risk.get("event_type", "Event"),
                    mw=risk.get("impact_mw", 0),
                    description=risk.get("description", "")[:50],
                    pct=risk.get("capacity_pct", 0),
                    line=risk.get("line", "Unknown"),
                    time=risk.get("time", "soon"),
                ))
            except KeyError:
                bullet_points.append(f"{risk.get('event_type', 'Risk')} in {risk.get('state', 'Unknown')}")
        
        return PanelData(
            title="RISK WATCH",
            icon="⚠️",
            headline=headline,
            bullet_points=bullet_points,
            severity=severity,
            timestamp=datetime.now().strftime("%H:%M"),
        )
    
    def _generate_plain_summary(
        self,
        now: PanelData,
        predicted: PanelData,
        risk: PanelData,
    ) -> str:
        """Generate a 2-3 sentence executive summary."""
        sentences = []
        
        # Current state
        if now.severity == "critical":
            sentences.append(f"⚡ ALERT: {now.headline}.")
        elif now.severity == "warning":
            sentences.append(f"⚠️ {now.headline}.")
        else:
            sentences.append(f"{now.headline}.")
        
        # Add prediction if significant
        if predicted.severity != "info":
            sentences.append(predicted.headline + ".")
        
        # Add top risk if present
        if risk.severity != "info" and risk.bullet_points:
            sentences.append(f"Key risk: {risk.bullet_points[0]}.")
        
        return " ".join(sentences)
    
    def _generate_technical_details(
        self,
        trades: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        risk_flags: List[Dict[str, Any]],
        frequency: float,
    ) -> str:
        """Generate full technical breakdown for "Show Details" view."""
        lines = []
        
        lines.append(f"=== GRID STATUS @ {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
        lines.append(f"Frequency: {frequency:.2f} Hz")
        lines.append("")
        
        # Trades section
        lines.append("--- ACTIVE TRADES ---")
        if trades:
            for t in trades:
                lines.append(
                    f"  {t.get('seller')} → {t.get('buyer')}: "
                    f"{t.get('mw', 0):.1f}MW @ ₹{t.get('price', 0):.2f}/kWh"
                )
        else:
            lines.append("  (none)")
        lines.append("")
        
        # Predictions section
        lines.append("--- FORECASTS ---")
        if predictions:
            for p in predictions:
                lines.append(
                    f"  {p.get('state')}: {p.get('type')} "
                    f"{p.get('mw', 0):.1f}MW by {p.get('time')}"
                )
        else:
            lines.append("  (no significant changes)")
        lines.append("")
        
        # Risk flags section
        lines.append("--- RISK FLAGS ---")
        if risk_flags:
            for r in risk_flags:
                lines.append(
                    f"  [{r.get('severity', 'LOW')}] {r.get('state')}: "
                    f"{r.get('event_type')} - {r.get('description', '')[:60]}"
                )
        else:
            lines.append("  (none)")
        
        return "\n".join(lines)
