"""
DEPRECATED - No longer used.

The new 2-tier system (ForwardMarketPlanner + DeviationDetector)
doesn't use LLM agents. See deviation_detector.py for event impact analysis.
"""

class ImpactNarratorAgent:
    """DEPRECATED - Use DeviationDetector instead."""
    
    def __init__(self, *args, **kwargs):
        print("[DEPRECATED] ImpactNarratorAgent - Use DeviationDetector instead")
    
    def narrate_impact(self, *args, **kwargs):
        return "No narrative - system uses deterministic anomaly detection."
    
    def deep_impact_analysis(self, *args, **kwargs):
        return "No narrative - system uses deterministic anomaly detection."
