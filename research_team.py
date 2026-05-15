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
            except: pass

    def bullish_researcher(self, window_data):
        score = random.uniform(0.5, 1.0) * self.bull_weight
        return {"score": score, "reason": "Bullish signals."}

    def bearish_researcher(self, window_data):
        score = random.uniform(0.3, 0.9) * self.bear_weight
        return {"score": score, "reason": "Bearish risks."}

    def cro_consensus(self, window_data):
        bull_case = self.bullish_researcher(window_data)
        bear_case = self.bearish_researcher(window_data)
        approved = bull_case['score'] > (bear_case['score'] * 2.0)
        trace = {
            "bull_score": bull_case['score'], "bull_reason": bull_case['reason'],
            "bear_score": bear_case['score'], "bear_reason": bear_case['reason'],
            "approved": approved
        }
        return approved, trace
