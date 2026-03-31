"""
routing_agent/syndicate_xai.py
==============================
Human-readable impact narratives for dashboard logs using LLM.
"""

from __future__ import annotations
import logging
from typing import Any
from openai import OpenAI

from ..intelligence_agent.setup import LLM_MODEL

logger = logging.getLogger(__name__)


class SyndicateXAI:
    def __init__(self):
        self._client = OpenAI()

    def dispatch_narrative(
        self,
        record: Any,
        buyer_deficit_before_mw: float,
        line_cap_mw: float,
        residual_deficit_mw: float,
        trigger_summary: str,
    ) -> str:
        hour = getattr(record, "dispatch_hour", None)
        hour_str = f"{int(hour):02d}:00 HRS" if hour is not None else "scheduled window"
        
        # Original fallback string
        fallback_msg = (
            f"Routed {record.transfer_mw:.2f} MW from {record.seller_city_id} to {record.buyer_city_id} "
            f"at {hour_str}. Reasoning: {record.buyer_city_id} faced an intelligence-adjusted deficit of "
            f"{buyer_deficit_before_mw:.2f} MW ({trigger_summary}). Dispatcher capped interconnector at "
            f"{line_cap_mw:.2f} MW under limits. Residual deficit: {residual_deficit_mw:.2f} MW."
        )

        sys_prompt = (
            "You are a Senior Grid Control Room Operator explaining a recent inter-state power transfer to the National Security Council. "
            "Write a single, tense, highly dramatic yet very formal 3-4 sentence narrative explaining this event. "
            "Include these exact numbers explicitly: The amount transferred, the line cap (DLR), the buyer's original deficit, and their remaining residual deficit. "
            "Never use the word 'AI', 'simulate', or 'fiction'."
        )

        user_prompt = (
            f"Transfer details:\n"
            f"- Buyer: {record.buyer_city_id}\n"
            f"- Seller: {record.seller_city_id}\n"
            f"- Time: {hour_str}\n"
            f"- Amount transferred: {record.transfer_mw:.2f} MW\n"
            f"- Buyer's deficit before trade: {buyer_deficit_before_mw:.2f} MW\n"
            f"- Cause of buyer's deficit: {trigger_summary}\n"
            f"- Interconnector (DLR) Max Line Capacity: {line_cap_mw:.2f} MW\n"
            f"- Buyer's residual deficit after trade: {residual_deficit_mw:.2f} MW\n"
        )
        
        # Add negotiation lines if available (they are logged in decision_trace)
        trace = list(getattr(record, "decision_trace", []))
        neg_line = next((t for t in trace if "NEGOTIATION buyer" in t), None)
        if neg_line:
            user_prompt += f"\n- Negotiation transcript snippet: {neg_line}"

        try:
            resp = self._client.chat.completions.create(
                model=LLM_MODEL,
                temperature=0.6,
                max_tokens=150,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            narrative = resp.choices[0].message.content.strip()
            return f"[LLM] {narrative}"
        except Exception as e:
            logger.warning(f"Failed to generate LLM dispatch narrative: {e}")
            return fallback_msg

    def load_shedding_narrative(self, load_shed: dict[str, Any]) -> str:
        hour = load_shed.get("dispatch_hour")
        hour_str = f"{int(hour):02d}:00 HRS" if hour is not None else "current window"
        state = load_shed.get('state_id', 'UNKNOWN')
        shed_mw = float(load_shed.get('shed_mw', 0.0))
        level = load_shed.get('level', 'LEVEL_1')
        
        fallback_msg = (
            f"Syndicate Decider mandated {level} load-shedding of "
            f"{shed_mw:.2f} MW in {state} at {hour_str} to preserve macro-grid stability."
        )
        
        sys_prompt = (
            "You are the National Grid Commander issuing a severe alert regarding controlled rolling blackouts (load-shedding). "
            "Write a dramatic, urgent, yet formal 2-3 sentence Situation Report. "
            "Mention the exact state, the severity level, and the exact amount of MW being cut off from the public to prevent a total grid collapse. "
            "Do not sound robotic. Sound like a serious engineer making a tough call."
        )

        user_prompt = (
            f"Incident details:\n"
            f"- State: {state}\n"
            f"- Time: {hour_str}\n"
            f"- Power Cut Amount: {shed_mw:.2f} MW\n"
            f"- Severity: {level}\n"
            f"Write the situation report."
        )

        try:
            resp = self._client.chat.completions.create(
                model=LLM_MODEL,
                temperature=0.7,
                max_tokens=100,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            narrative = resp.choices[0].message.content.strip()
            return f"[LLM ALERT] {narrative}"
        except Exception as e:
            logger.warning(f"Failed to generate LLM load shed narrative: {e}")
            return fallback_msg

