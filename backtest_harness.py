import pandas as pd
import yfinance as yf
from strategy import Strategy
from research_team import ResearchTeam
import random
import os

class BacktestHarness:
    def __init__(self):
        self.strategy = Strategy()
        self.research_team = ResearchTeam()
        self.initial_balance = 10000.0
        self.balance = self.initial_balance
        self.trades = []
        self.failed_patterns = []

    def fetch_data(self):
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=720) # Max 730 days for 1h data
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        print(f"Fetching XAU/USD data from {start_str} to {end_str} at 1-hour intervals...")
        data = yf.download('GC=F', start=start_str, end=end_str, interval='1h')
        return data

    def run_simulation(self, data, risk_multiplier=1.0):
        self.balance = self.initial_balance
        self.trades = []
        peak_balance = self.balance
        max_drawdown = 0.0

        # Position-Aware Reasoning: Track continuous risk exposure
        open_positions = []

        # Reflexivity Sensor: Track consecutive consensus rounds
        consensus_streak = 0

        for i in range(20, len(data)):
            # Process mock position exits for Position-Aware Reasoning
            # In a real engine, we'd check if current price hits SL or TP
            active_positions = []
            for pos in open_positions:
                pos['duration'] -= 1
                if pos['duration'] <= 0:
                    # Position resolves
                    self.balance += pos['pnl']
                    self.trades.append({'date': data.index[i], 'result': 'win' if pos['pnl'] > 0 else 'loss', 'pnl': pos['pnl']})

                    # Surprise Ratio Check
                    if pos['pnl'] > 0:
                        surprise_ratio = abs(pos['pnl'] - pos['expected_pnl'])
                        if surprise_ratio > (pos['expected_pnl'] * 0.5):
                            self.failed_patterns.append(f"Date: {data.index[i].date()} | PnL: {pos['pnl']:.2f} | Reason: Lucky/Unpredictable Win (Surprise Ratio high). Do not over-optimize on this.")
                    else:
                        self.failed_patterns.append(f"Date: {data.index[i].date()} | Loss: {abs(pos['pnl']):.2f} | Reason: Simulated market exit against setup.")
                else:
                    active_positions.append(pos)
            open_positions = active_positions

            # Drawdown check based on realized balance (in reality would include unrealized)
            if self.balance > peak_balance:
                peak_balance = self.balance
            drawdown = (peak_balance - self.balance) / peak_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            if drawdown >= self.strategy.total_drawdown_kill_switch:
                break

            # Pass only the last 20 bars to avoid memory issues and improve efficiency
            window = data.iloc[i-20:i+1]

            sweep_dir = self.strategy.identify_liquidity_sweeps(window)
            fvg_dir = self.strategy.check_fair_value_gap(window)

            is_liquidity_sweep = sweep_dir is not None
            is_fvg = fvg_dir is not None
            trade_direction = sweep_dir if sweep_dir else "BUY"

            trend_aligned = self.strategy.check_trend_filter(window, trade_direction)
            news_clear = self.strategy.check_news_filter()

            has_primary = is_liquidity_sweep and is_fvg and (sweep_dir == fvg_dir) and trend_aligned and news_clear

            if has_primary:
                # Meta-Learning Pattern Recognition check (Block setup if last 10 trades failed similarly)
                if len(self.failed_patterns) >= 10:
                    recent_fails = self.failed_patterns[-10:]
                    # Simple mock matching to simulate pattern blocking
                    if sum(["Simulated market exit against setup" in f for f in recent_fails]) >= 8:
                        continue # Block setup autonomously

                # Trigger debate for setups
                cro_approved, trace = self.research_team.cro_consensus(window)

                # Check 100% consensus (Bear score is very low, Bull is very high)
                # For mock simplicity, we define 100% consensus as approval where Bull > 2 * Bear
                if cro_approved and trace['bull_score'] > trace['bear_score'] * 2.0:
                    consensus_streak += 1
                else:
                    consensus_streak = 0

                if cro_approved:
                    # Calculate available balance (Position-Aware)
                    exposure = sum([abs(p['pnl']) for p in open_positions if p['pnl'] < 0]) # Mock max loss exposure
                    available_balance = self.balance - exposure

                    # Base risk amount
                    risk_amount = available_balance * (self.strategy.risk_per_trade_limit * risk_multiplier)

                    # Reflexivity Sensor execution
                    if consensus_streak >= 3:
                        # "Crowded Trade" -> reduce risk by 50%
                        risk_amount *= 0.5

                    expected_pnl = risk_amount * 2 # Assuming 1:2 RR
                    win = random.choice([True, False, False])

                    if win:
                        realized_profit = random.choice([expected_pnl * 0.8, expected_pnl, expected_pnl * 3.0])
                        open_positions.append({'duration': random.randint(1, 5), 'pnl': realized_profit, 'expected_pnl': expected_pnl})
                    else:
                        open_positions.append({'duration': random.randint(1, 5), 'pnl': -risk_amount, 'expected_pnl': expected_pnl})

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

        baseline_sharpe = None

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

            # Rollback Trigger Logic
            if baseline_sharpe is None and results['sharpe_ratio'] > 0:
                baseline_sharpe = results['sharpe_ratio']
                print(f"Baseline Sharpe established at {baseline_sharpe:.2f}")
            elif baseline_sharpe is not None:
                if results['sharpe_ratio'] < (baseline_sharpe * 0.8):
                    print(f"CRITICAL: Sharpe Ratio dropped by >20% (from {baseline_sharpe:.2f} to {results['sharpe_ratio']:.2f}). Triggering Rollback!")
                    import subprocess
                    try:
                        subprocess.run(["git", "reset", "--hard", "HEAD~1"], check=True)
                        print("Rollback successful. The last evolution has been reverted.")
                    except Exception as e:
                        print(f"Rollback failed: {e}")
                else:
                    # Update baseline if improved
                    if results['sharpe_ratio'] > baseline_sharpe:
                        baseline_sharpe = results['sharpe_ratio']

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

    def apply_meta_learning(self):
        """
        Analyzes the /traces directory to see which researcher was right during failed trades.
        Adjusts Darwinian Weights in a mocked 'research_weights.json' output.
        """
        print("\nApplying Meta-Learning via Darwinian Weight Adjustment...")
        traces_dir = "traces"
        if not os.path.exists(traces_dir):
            print("No traces directory found. Skipping meta-learning.")
            return

        import json
        import glob

        trace_files = glob.glob(os.path.join(traces_dir, "*.json"))
        if not trace_files:
            print("No trace files found in /traces. Skipping meta-learning.")
            return

        bull_weight_adjustment = 0.0
        bear_weight_adjustment = 0.0

        for file in trace_files:
            try:
                with open(file, 'r') as f:
                    trace = json.load(f)
                    # If CRO approved but it ended up failing (which we infer from it being here in a basic mock)
                    if trace.get("approved"):
                        # Bear was right to be bearish, Bull was wrong
                        bear_weight_adjustment += 0.05
                        bull_weight_adjustment -= 0.05
                    else:
                        # Setup rejected. If it was a missed winner (hard to know without future data),
                        # but if we assume rejected trades were safe calls:
                        pass
            except Exception as e:
                pass

        weights = {
            "bull_weight_modifier": round(bull_weight_adjustment, 2),
            "bear_weight_modifier": round(bear_weight_adjustment, 2)
        }

        with open("research_weights.json", "w") as f:
            json.dump(weights, f, indent=4)
        print(f"Meta-learning complete. Adjusted weights: {weights}")

    def run_autoresearch_loop(self):
        data = self.fetch_data()
        self.walk_forward_analysis(data)
        self.generate_learnings()
        self.apply_meta_learning()

if __name__ == "__main__":
    harness = BacktestHarness()
    harness.run_autoresearch_loop()
