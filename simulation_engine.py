import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class ScenarioGenerator:
    def __init__(self, current_price=1.0500):
        self.current_price = current_price

    def generate_paths(self, num_paths=1000, hours=24, volatility=0.005, jump_prob=0.05, jump_size=0.02):
        dt = 1.0
        paths = []
        base_time = datetime.now()
        timestamps = [base_time + timedelta(hours=i) for i in range(hours)]
        for p in range(num_paths):
            prices = [self.current_price]
            for t in range(1, hours):
                shock = np.random.normal(0, volatility)
                jump = 0.0
                if np.random.random() < jump_prob: jump = np.random.choice([-1, 1]) * np.random.normal(jump_size, jump_size * 0.5)
                prices.append(prices[-1] * np.exp(shock + jump))
            df = pd.DataFrame({
                'Open': prices,
                'High': [p * (1 + abs(np.random.normal(0, volatility*0.5))) for p in prices],
                'Low': [p * (1 - abs(np.random.normal(0, volatility*0.5))) for p in prices],
                'Close': prices
            }, index=timestamps)
            paths.append(df)
        return paths
