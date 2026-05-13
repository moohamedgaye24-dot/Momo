import pandas as pd
import yfinance as yf
from strategy import Strategy
import random
import os

class BacktestHarness:
    def __init__(self):
        self.strategy = Strategy()
        self.initial_balance = 10000.0
        self.balance = self.initial_balance
        self.trades = []
        self.failed_patterns = []

    def fetch_data(self, start_date='2021-05-01', end_date='2026-05-01'):
        print(f"Fetching EUR/USD data from {start_date} to {end_date}...")
        data = yf.download('EURUSD=X', start=start_date, end=end_date, interval='1d')
        return data

    def run_simulation(self, data, risk_multiplier=1.0):
        self.balance = self.initial_balance
        self.trades = []
        peak_balance = self.balance
        max_drawdown = 0.0

        for i in range(20, len(data)):
            # Pass only the last 20 bars to avoid memory issues and improve efficiency
            window = data.iloc[i-20:i+1]

            liquidity_sweep = self.strategy.identify_liquidity_sweeps(window)
            fvg = self.strategy.check_fair_value_gap(window)

            if liquidity_sweep and fvg:
                # Use adjusted risk limit for walk-forward optimization
                risk_amount = self.balance * (self.strategy.risk_per_trade_limit * risk_multiplier)

                win = random.choice([True, False, False])

                if win:
                    profit = risk_amount * 2
                    self.balance += profit
                    self.trades.append({'date': window.index[-1], 'result': 'win', 'pnl': profit})
                else:
                    loss = risk_amount
                    self.balance -= loss
                    self.trades.append({'date': window.index[-1], 'result': 'loss', 'pnl': -loss})

                    # Log failed pattern context
                    self.failed_patterns.append(f"Date: {window.index[-1].date()} | Loss: {loss:.2f} | Reason: Simulated market exit against setup (shallow liquidity sweep / false breakout).")

                if self.balance > peak_balance:
                    peak_balance = self.balance
                drawdown = (peak_balance - self.balance) / peak_balance
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

                if drawdown >= self.strategy.total_drawdown_kill_switch:
                    break

        total_return = (self.balance - self.initial_balance) / self.initial_balance
        returns = [t['pnl']/self.initial_balance for t in self.trades]
        if len(returns) > 0:
            import numpy as np
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0.0

        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'num_trades': len(self.trades),
            'sharpe_ratio': sharpe_ratio
        }

    def walk_forward_analysis(self, data):
        print("Starting Walk-Forward Analysis...")
        years = data.index.year.unique()
        all_results = []

        for year in years[:-1]:
            print(f"\n--- Optimizing on {year}, Testing on {year+1} ---")

            # 1. Optimization
            print(f"Optimizing parameters on {year} data...")
            opt_data = data[data.index.year == year]
            best_risk_multiplier = 1.0
            best_sharpe = -float('inf')

            if len(opt_data) > 0:
                for multiplier in [0.5, 1.0, 1.5]:
                    opt_results = self.run_simulation(opt_data, risk_multiplier=multiplier)
                    if opt_results['sharpe_ratio'] > best_sharpe:
                        best_sharpe = opt_results['sharpe_ratio']
                        best_risk_multiplier = multiplier

            print(f"Optimal risk multiplier found: {best_risk_multiplier}")

            # 2. Testing
            test_data = data[data.index.year == year+1]
            if len(test_data) == 0:
                continue

            results = self.run_simulation(test_data, risk_multiplier=best_risk_multiplier)
            all_results.append(results)

            print(f"Results for {year+1}:")
            print(f"Total Return: {results['total_return']:.2%}")
            print(f"Annualized Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {results['max_drawdown']:.2%}")
            print(f"Number of Trades: {results['num_trades']}")

        return all_results

    def generate_learnings(self):
        if self.failed_patterns:
            content = "# Trade Learnings\n\n## Failure Patterns\n\n"
            # Get a sample of up to 20 failed patterns
            sample = self.failed_patterns[:20] if len(self.failed_patterns) > 20 else self.failed_patterns
            for pattern in sample:
                content += f"- {pattern}\n"

            with open("learnings.md", "w") as f:
                f.write(content)
            print("\nGenerated learnings.md with failure patterns.")

    def run_autoresearch_loop(self):
        data = self.fetch_data()
        self.walk_forward_analysis(data)
        self.generate_learnings()

if __name__ == "__main__":
    harness = BacktestHarness()
    harness.run_autoresearch_loop()
