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
        profitable_count = 0
        failure_modes = []
        for idx, path in enumerate(paths):
            mock_balance = 10000.0
            path_drawdown = 0.0
            peak = mock_balance
            for i in range(5, len(path)):
                window = path.iloc[i-5:i+1]
                sweep_dir = self.strategy.identify_liquidity_sweeps(window)
                fvg_dir = self.strategy.check_fair_value_gap(window)
                if sweep_dir and fvg_dir and sweep_dir == fvg_dir:
                    cro_approved, _ = self.research_team.cro_consensus(window)
                    if cro_approved and i+1 < len(path):
                        entry_price = path['Close'].iloc[i]
                        exit_price = path['Close'].iloc[i+1]
                        pnl_pct = (exit_price - entry_price) / entry_price
                        mock_balance += (mock_balance * self.strategy.risk_per_trade_limit * pnl_pct * 10)
                        if mock_balance > peak: peak = mock_balance
                        dd = (peak - mock_balance) / peak
                        if dd > path_drawdown: path_drawdown = dd
            if mock_balance > 10000.0 and path_drawdown < self.strategy.total_drawdown_kill_switch:
                profitable_count += 1
            else:
                if path_drawdown >= self.strategy.total_drawdown_kill_switch:
                    failure_modes.append(f"Path {idx}: Kill-switch triggered (DD: {path_drawdown*100:.1f}%) during high volatility simulation.")
                else:
                    failure_modes.append(f"Path {idx}: Net negative PnL (Ending balance: {mock_balance:.2f})")
        return profitable_count / len(paths), failure_modes

    def log_warnings(self, failure_modes):
        content = "# Oracle Warnings: Simulated Future Weaknesses\n\n"
        for mode in failure_modes[:20]: content += f"- {mode}\n"
        with open(self.warnings_file, "w") as f: f.write(content)

    def rewrite_strategy_thresholds(self):
        with open("strategy.py", "r") as f: code = f.read()
        code = code.replace("window['Close'].iloc[-1] < (window['Low'].iloc[-3] * 0.999)", "window['Close'].iloc[-1] < (window['Low'].iloc[-3] * 0.998)")
        code = code.replace("(upper_wick > body * 3) or (lower_wick > body * 3)", "(upper_wick > body * 4) or (lower_wick > body * 4)")
        with open("strategy.py", "w") as f: f.write(code)

    def run_oracle_loop(self):
        paths = self.simulator.generate_paths(num_paths=100)
        success_rate, failure_modes = self.evaluate_strategy(paths)
        self.log_warnings(failure_modes)
        if success_rate < 0.90:
            self.rewrite_strategy_thresholds()
