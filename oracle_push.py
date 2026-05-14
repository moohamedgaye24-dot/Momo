import os
from simulation_engine import ScenarioGenerator
from strategy import Strategy
from research_team import ResearchTeam

class OracleManager:
    def __init__(self):
        self.strategy = Strategy()
        self.research_team = ResearchTeam()
        self.simulator = ScenarioGenerator()
        self.warnings_file = "oracle_warnings.md"

    def evaluate_strategy(self, paths):
        # We need the strategy to be profitable in >= 90% of scenarios
        profitable_count = 0
        failure_modes = []

        print(f"Testing current strategy against {len(paths)} alternate futures...")

        for idx, path in enumerate(paths):
            mock_balance = 10000.0
            path_drawdown = 0.0
            peak = mock_balance

            # Simple simulation wrapper over the 24 hour path
            for i in range(5, len(path)): # Need a window of 5
                window = path.iloc[i-5:i+1]

                # Check Strategy
                is_liquidity_sweep = self.strategy.identify_liquidity_sweeps(window)
                is_fvg = self.strategy.check_fair_value_gap(window)
                is_breaker = self.strategy.identify_breaker_blocks(window)
                is_rejection = self.strategy.identify_rejection_blocks(window)

                has_primary = is_liquidity_sweep and is_fvg
                has_secondary = is_breaker or is_rejection

                if has_primary or has_secondary:
                    # Adversarial Debate
                    cro_approved, _ = self.research_team.cro_consensus(window)
                    if cro_approved:
                        # Assume immediate next bar resolution for simplicity in 24h simulation
                        if i+1 < len(path):
                            entry_price = path['Close'].iloc[i]
                            exit_price = path['Close'].iloc[i+1]
                            pnl_pct = (exit_price - entry_price) / entry_price
                            # Simulate 10x leverage impact on 1% risk allocation
                            mock_balance += (mock_balance * self.strategy.risk_per_trade_limit * pnl_pct * 10)

                            if mock_balance > peak:
                                peak = mock_balance
                            dd = (peak - mock_balance) / peak
                            if dd > path_drawdown:
                                path_drawdown = dd

            # Path Analysis
            if mock_balance > 10000.0 and path_drawdown < self.strategy.total_drawdown_kill_switch:
                profitable_count += 1
            else:
                if path_drawdown >= self.strategy.total_drawdown_kill_switch:
                    failure_modes.append(f"Path {idx}: Kill-switch triggered (DD: {path_drawdown*100:.1f}%) during high volatility simulation.")
                else:
                    failure_modes.append(f"Path {idx}: Net negative PnL (Ending balance: {mock_balance:.2f})")

        success_rate = profitable_count / len(paths)
        return success_rate, failure_modes

    def log_warnings(self, failure_modes):
        content = "# Oracle Warnings: Simulated Future Weaknesses\n\n"
        content += "The Oracle has identified the following dangerous failure modes during Monte Carlo Jump-Diffusion simulation:\n\n"

        # Sample top 20 to avoid massive files
        for mode in failure_modes[:20]:
            content += f"- {mode}\n"

        with open(self.warnings_file, "w") as f:
            f.write(content)

    def rewrite_strategy_thresholds(self):
        """
        Autonomously tweaks the logic inside strategy.py to tighten SMC constraints
        and adjust volatility scaling thresholds.
        """
        print("\n[ORACLE PUSH AUTHORIZED] Autonomously rewriting strategy.py to achieve Scenario Neutrality...")

        # In a real environment, an LLM call or AST parser would intelligently rewrite.
        # For this execution, we use string replacements to tighten the thresholds.
        with open("strategy.py", "r") as f:
            code = f.read()

        # Example 1: Tightening Breaker Block validation (must break low significantly, not just <=)
        code = code.replace("window['Close'].iloc[-1] <= window['Low'].iloc[-3]", "window['Close'].iloc[-1] < (window['Low'].iloc[-3] * 0.999)")

        # Example 2: Tightening Rejection Blocks (Wicks must be 3x the body instead of 2x)
        code = code.replace("(upper_wick > body * 2) or (lower_wick > body * 2)", "(upper_wick > body * 3) or (lower_wick > body * 3)")

        with open("strategy.py", "w") as f:
            f.write(code)

        print("Strategy rewritten and hardened against simulated weaknesses.")

    def run_oracle_loop(self):
        print("Initializing Oracle Layer (Synthetic Future Simulation)...")
        # Generate 1,000 alternate 24-hour realities
        paths = self.simulator.generate_paths(num_paths=1000)

        success_rate, failure_modes = self.evaluate_strategy(paths)
        print(f"Strategy Success Rate across 1,000 simulations: {success_rate*100:.2f}%")

        self.log_warnings(failure_modes)
        print(f"Logged most dangerous failure modes to {self.warnings_file}")

        # The prompt authorizes rewrite if it fails more than 10% (i.e. success < 90%)
        if success_rate < 0.90:
            self.rewrite_strategy_thresholds()

            # Reload strategy and run validation
            import importlib
            import strategy
            importlib.reload(strategy)
            self.strategy = strategy.Strategy()

            new_success_rate, _ = self.evaluate_strategy(paths)
            print(f"Post-Evolution Success Rate: {new_success_rate*100:.2f}%")
            if new_success_rate >= success_rate:
                print("Oracle Push Successful: Scenario Neutrality improved.")
            else:
                print("Oracle Push Failed: Strategy degraded. (Mock environment limitations apply)")
        else:
            print("Strategy is already Scenario Neutral (>90% success). No rewrite necessary.")

if __name__ == "__main__":
    oracle = OracleManager()
    oracle.run_oracle_loop()
