import math
import requests
import os

class NewsAnalyst:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.marketaux.com/v1/news/all"

    def fetch_real_time_news(self, symbol="XAUUSD"):
        if self.api_key == "DEMO_KEY":
            import random
            return random.choice([True, False, False, False]), random.choice([True, False])
        try:
            params = {"symbols": symbol, "filter_entities": "true", "limit": 10, "api_token": self.api_key}
            data = requests.get(self.base_url, params=params).json()
            is_high_impact_soon = len(data.get('data', [])) > 5
            sentiment_score = sum([a.get('entities', [{}])[0].get('sentiment_score', 0) for a in data.get('data', [])])
            return is_high_impact_soon, sentiment_score > 0
        except: return False, False

    def check_news_impact(self, symbol, trade_direction):
        is_high_impact_soon, sentiment_bullish = self.fetch_real_time_news(symbol)
        if is_high_impact_soon: return 0.5
        sentiment_matches_trend = (trade_direction == "BUY" and sentiment_bullish) or (trade_direction == "SELL" and not sentiment_bullish)
        if sentiment_matches_trend: return 1.25
        return 1.0

    def calculate_sentiment_z_score(self, positive_count, negative_count):
        return math.log((1 + positive_count) / (1 + negative_count))
