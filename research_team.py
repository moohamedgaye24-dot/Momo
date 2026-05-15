import random

import json
import os

class ResearchTeam:
    def __init__(self):
        self.bull_weight = 1.0
        self.bear_weight = 1.0
        self._load_weights()

    def _load_weights(self):
        if os.path.exists("research_weights.json"):
            try:
                with open("research_weights.json", "r") as f:
                    weights = json.load(f)
                    self.bull_weight += weights.get("bull_weight_modifier", 0.0)
                    self.bear_weight += weights.get("bear_weight_modifier", 0.0)
            except Exception:
                pass

    def bullish_researcher(self, window_data):
        # Mock logic to find reasons the trade will succeed
        reasons = [
            "Strong upward momentum on higher timeframes.",
            "Clear bounce off critical support level.",
            "Positive news sentiment aligning with technicals.",
            "High institutional volume detected at the sweep."
        ]
        score = random.uniform(0.5, 1.0) * self.bull_weight
        selected_reason = random.choice(reasons)
        return {"score": score, "reason": selected_reason}

    def bearish_researcher(self, window_data):
        # Mock logic to find reasons the trade will fail
        reasons = [
            "Hidden liquidity pool just below entry acting as a magnet.",
            "Upcoming high-impact news divergence expected.",
            "Overextended RSI indicating immediate pullback risk.",
            "VIX spike indicating macro sell-off pressure."
        ]
        score = random.uniform(0.3, 0.9) * self.bear_weight
        selected_reason = random.choice(reasons)
        return {"score": score, "reason": selected_reason}

    def cro_consensus(self, window_data):
        bull_case = self.bullish_researcher(window_data)
        bear_case = self.bearish_researcher(window_data)

        # CRO approves only if the Bullish case is 2x higher than Bearish risks
        approved = bull_case['score'] > (bear_case['score'] * 2.0)

        trace = {
            "bull_score": bull_case['score'],
            "bull_reason": bull_case['reason'],
            "bear_score": bear_case['score'],
            "bear_reason": bear_case['reason'],
            "approved": approved,
            "cro_reasoning": f"Approval={approved}. Bull({bull_case['score']:.2f}) vs Bear({bear_case['score']:.2f})"
        }
        return approved, trace
