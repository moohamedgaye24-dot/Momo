import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class ScenarioGenerator:
    def __init__(self, current_price=1.0500):
        self.current_price = current_price

    def generate_paths(self, num_paths=1000, hours=24, volatility=0.005, jump_prob=0.05, jump_size=0.02):
        """
        Generates 'what-if' market paths using a Jump-Diffusion model to simulate
        standard market movements alongside Flash Crashes and News Gaps.
        """
        dt = 1.0 # 1 hour per step
        paths = []

        base_time = datetime.now()
        timestamps = [base_time + timedelta(hours=i) for i in range(hours)]

        for p in range(num_paths):
            prices = [self.current_price]
            for t in range(1, hours):
                # Standard Geometric Brownian Motion
                drift = 0.0 # Assuming neutral drift over 24 hours
                shock = np.random.normal(0, volatility)

                # Jump Diffusion (Extreme Scenarios)
                jump = 0.0
                if np.random.random() < jump_prob:
                    # 50/50 chance of flash crash vs news spike
                    direction = np.random.choice([-1, 1])
                    jump = direction * np.random.normal(jump_size, jump_size * 0.5)

                next_price = prices[-1] * np.exp(drift + shock + jump)
                prices.append(next_price)

            # Construct a DataFrame mimicking the yfinance output format
            df = pd.DataFrame({
                'Open': prices,
                'High': [p * (1 + abs(np.random.normal(0, volatility*0.5))) for p in prices],
                'Low': [p * (1 - abs(np.random.normal(0, volatility*0.5))) for p in prices],
                'Close': prices
            }, index=timestamps)
            paths.append(df)

        return paths

if __name__ == "__main__":
    sg = ScenarioGenerator()
    paths = sg.generate_paths(num_paths=5)
    print(f"Generated {len(paths)} simulated 24-hour scenarios.")
    print("Sample Output (Path 1):")
    print(paths[0].head())
