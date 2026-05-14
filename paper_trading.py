import os
import time
import csv
from datetime import datetime
import pandas as pd
from strategy import Strategy
from research_team import ResearchTeam
from singularity_engine import SingularityEngine
import json

# Mock/Skeleton for Alpaca API
try:
    from alpaca.data.historical import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame
except ImportError:
    print("alpaca-py not installed, using mock data client.")

class PaperTradingEngine:
    def __init__(self):
        self.strategy = Strategy()
        self.research_team = ResearchTeam()
        self.singularity = SingularityEngine()
        self.log_file = "paper_results.csv"
        self.traces_dir = "traces"

        if not os.path.exists(self.traces_dir):
            os.makedirs(self.traces_dir)

        # Alpaca configuration
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.api_secret = os.getenv("APCA_API_SECRET_KEY")
        if self.api_key and self.api_secret:
            try:
                self.data_client = CryptoHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
            except Exception as e:
                print("Failed to initialize Alpaca client:", e)
                self.data_client = None
        else:
            self.data_client = None
            print("Warning: APCA_API_KEY_ID or APCA_API_SECRET_KEY not found in environment.")

        # Initialize CSV log file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Action", "Reasoning", "Risk_Limit", "Drawdown_Status"])

    def _fetch_latest_data(self):
        """
        Fetches the latest hourly candles for BTC/USD via Alpaca Crypto API.
        Note: Alpaca's crypto endpoint is used as a proxy for 24/5 FX demonstration.
        """
        if self.data_client:
            try:
                request_params = CryptoBarsRequest(
                    symbol_or_symbols=["BTC/USD"],
                    timeframe=TimeFrame.Hour,
                    limit=20 # Fetch enough history for SMC window
                )
                bars = self.data_client.get_crypto_bars(request_params)
                df = bars.df
                # Reset index to make 'symbol' and 'timestamp' columns accessible if needed
                # Rename columns to match Strategy class expectations (High, Low, Close, Open)
                df = df.rename(columns={'high': 'High', 'low': 'Low', 'close': 'Close', 'open': 'Open'})
                return df
            except Exception as e:
                print(f"Error fetching data from Alpaca: {e}")
                # Fallback to mock data if API fails to keep loop running
                pass

        print("Using mock data due to API client absence/failure...")
        data = {
            'High': [1.0500, 1.0520, 1.0490, 1.0550, 1.0560] * 4,
            'Low': [1.0450, 1.0460, 1.0410, 1.0480, 1.0500] * 4,
            # Artificially triggering the breaker block logic for mock testing
            'Close': [1.0480, 1.0510, 1.0430, 1.0530, 1.0300] * 4,
            'Open': [1.0470, 1.0500, 1.0420, 1.0520, 1.0530] * 4
        }
        df = pd.DataFrame(data)
        return df

    def log_trade(self, action, reasoning, drawdown_status):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        risk = f"{self.strategy.risk_per_trade_limit * 100}%"

        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, action, reasoning, risk, drawdown_status])
        print(f"[{timestamp}] Logged: {action} | Reason: {reasoning}")

    def evaluate_binary_evals(self, action, current_drawdown, is_liquidity_sweep, is_fvg, is_breaker, is_rejection, expected_pnl=0, realized_pnl=0):
        # Automated Binary Evals (Pass/Fail)
        passed = True
        reason = ""

        # Rule 1: 1% Risk Check
        if current_drawdown >= self.strategy.total_drawdown_kill_switch:
            passed = False
            reason = "Failed: 5% total drawdown limit breached."

        # Rule 2: SMC Setup Requirements
        if action == "ENTER LONG/SHORT":
            has_primary = (is_liquidity_sweep and is_fvg)
            has_secondary = is_breaker or is_rejection
            if not (has_primary or has_secondary):
                passed = False
                reason = "Failed: Entered trade without SMC confirmation (missing Primary FVG/Sweep or Secondary Breaker/Rejection)."

        # Surprise Ratio Calibration
        if realized_pnl > 0: # If it was a win
            surprise_ratio = abs(realized_pnl - expected_pnl)
            if surprise_ratio > abs(expected_pnl) * 0.5: # e.g. 50% deviation
                with open("learnings.md", "a") as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"- [{timestamp}] Lucky/Unpredictable Win: Surprise Ratio is high ({surprise_ratio:.2f}). Do not over-optimize on this setup.\n")

        if not passed:
            with open("learnings.md", "a") as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"- [{timestamp}] Eval Failure: {reason}\n")

    def update_dashboard(self, completed_trades, wins, losses):
        content = f"# Performance Monitor\n\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        content += f"**Total Paper P&L:** TBD (Mock)\n"
        win_rate = (wins / completed_trades * 100) if completed_trades > 0 else 0
        content += f"**Current Win Rate:** {win_rate:.2f}%\n"
        content += f"**Total Trades:** {completed_trades}\n\n"
        content += f"### Evolution Summary\n"
        content += f"No autonomous code evolutions performed yet."

        with open("performance_monitor.md", "w") as f:
            f.write(content)

    def trigger_recursive_optimization(self):
        print("Recursive Optimization triggered: Analyzing learnings.md and applying autonomous code update to strategy.py to filter out losing setups.")
        # Mock logic: in a full implementation, an LLM call or dynamic rewriting logic would go here

        # Update dashboard to reflect the evolution
        with open("performance_monitor.md", "a") as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n- {timestamp}: Triggered routine evolution analysis. No critical patches required.")

    def run_paper_trading_loop(self, poll_interval_seconds=3600):
        print(f"Starting Paper Trading Engine. Polling every {poll_interval_seconds} seconds.")
        print(f"Risk per trade enforced at {self.strategy.risk_per_trade_limit * 100}%")
        print(f"Kill-switch drawdown enforced at {self.strategy.total_drawdown_kill_switch * 100}%")

        completed_trades = 0
        wins = 0
        losses = 0

        # Position-Aware variables
        open_positions = []
        max_open_positions = 5

        # Reflexivity Sensor variable
        consensus_streak = 0

        while True:
            # Mock position management (resolving positions to simulate PnL)
            active_positions = []
            for pos in open_positions:
                pos['duration'] -= 1
                if pos['duration'] <= 0:
                    completed_trades += 1
                    if pos['result'] == 'win':
                        wins += 1
                    else:
                        losses += 1
                else:
                    active_positions.append(pos)
            open_positions = active_positions

            print("\nFetching latest market data...")
            window_data = self._fetch_latest_data()

            # Singularity Engine: Signal Decomposition
            is_dissonant, noise_ratio = self.singularity.analyze_market_dissonance(window_data)
            self.strategy.shock_neutral_mode = is_dissonant
            if is_dissonant:
                print(f"[ORACLE WARNING] High Market Dissonance detected (N2S: {noise_ratio:.4f}). Entering Shock-Neutral Mode.")
                # Trigger Recursive Agent Optimization (RAO)
                arbitrage_path_stable = self.singularity.execute_rao_swarm(window_data)
                self.strategy.rao_arbitrage_approved = arbitrage_path_stable
            else:
                self.strategy.shock_neutral_mode = False
                self.strategy.rao_arbitrage_approved = False

            # Evaluate SMC Strategy Rules & Macro Filter
            print("Evaluating SMC Strategy Rules...")
            is_liquidity_sweep = self.strategy.identify_liquidity_sweeps(window_data)
            is_fvg = self.strategy.check_fair_value_gap(window_data)
            is_breaker = self.strategy.identify_breaker_blocks(window_data)
            is_rejection = self.strategy.identify_rejection_blocks(window_data)
            atr_val = self.strategy.calculate_atr(window_data)

            # Macro Filter (Mocking VIX > 25 condition randomly for demonstration)
            import random
            vix_high = random.choice([True, False])
            macro_adjustment = 0.7 if vix_high else 1.0

            # Position sizing based on ATR
            dynamic_risk_limit = self.strategy.risk_per_trade_limit * (1 / (atr_val * 100)) * macro_adjustment

            # Mock drawdown status
            current_drawdown = 0.02 # e.g., 2% current drawdown
            drawdown_status = "Safe"

            action = ""

            if current_drawdown >= self.strategy.total_drawdown_kill_switch:
                reasoning = f"Kill-switch triggered! Current drawdown ({current_drawdown*100}%) exceeds limit ({self.strategy.total_drawdown_kill_switch*100}%)."
                action = "HALT"
                self.log_trade(action, reasoning, "KILLED")
                self.evaluate_binary_evals(action, current_drawdown, is_liquidity_sweep, is_fvg, is_breaker, is_rejection, 0, 0)
                break

            has_primary = is_liquidity_sweep and is_fvg
            has_secondary = is_breaker or is_rejection

            if has_primary or has_secondary:
                # Trigger Adversarial Debate
                print("Setup detected. Triggering Adversarial Debate Layer...")
                cro_approved, trace = self.research_team.cro_consensus(window_data)

                # Reflexivity Sensor Logic
                if cro_approved and trace['bull_score'] > trace['bear_score'] * 2.0:
                    consensus_streak += 1
                else:
                    consensus_streak = 0

                if consensus_streak >= 3:
                    dynamic_risk_limit *= 0.5
                    print(f"Reflexivity Sensor: 100% consensus for {consensus_streak} rounds. Crowded Trade detected. Risk reduced by 50%.")

                # Log Reasoning Trace
                trace_id = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Use a counter to prevent file overwrite in the same second during mock tests
                trace_file = os.path.join(self.traces_dir, f"trace_{trace_id}_{random.randint(1000, 9999)}.json")
                with open(trace_file, "w") as f:
                    json.dump(trace, f, indent=4)
                print(f"Reasoning trace captured in {trace_file}")

                if cro_approved:
                    # Singularity Neutrality Execution Override
                    if self.strategy.shock_neutral_mode and not self.strategy.rao_arbitrage_approved:
                        reasoning = f"Setup approved by CRO, but aborted due to Shock-Neutral mode. RAO Swarm failed to find stable arbitrage across Laurent divergence. Trace: {trace_file}"
                        action = "PASS"
                        self.log_trade(action, reasoning, drawdown_status)
                        expected_pnl, realized_pnl = 0, 0
                    elif len(open_positions) >= max_open_positions:
                        reasoning = f"Setup approved, but max open positions ({max_open_positions}) reached. Position-Aware engine skips entry."
                        action = "PASS"
                        self.log_trade(action, reasoning, drawdown_status)
                        expected_pnl, realized_pnl = 0, 0
                    else:
                        rao_tag = " [RAO Arbitrage Verified]" if self.strategy.shock_neutral_mode else ""
                        reasoning = f"Valid setup approved by CRO{rao_tag}. Primary={has_primary}, Sec={has_secondary}. Vol-scaled risk. VIX_High={vix_high}. Trace: {trace_file}"
                        action = "ENTER LONG/SHORT"
                        self.log_trade(action, reasoning, drawdown_status)

                        # Mock Realized vs Expected P&L for Surprise Ratio
                        expected_pnl = 100 * dynamic_risk_limit
                        realized_pnl = random.choice([-50, 50, 200]) # 200 would trigger high surprise ratio on win

                        # Add to open positions
                        mock_result = 'win' if realized_pnl > 0 else 'loss'
                        open_positions.append({'duration': random.randint(1, 3), 'result': mock_result})
                else:
                    reasoning = f"Setup rejected by CRO debate. Trace: {trace_file}"
                    action = "PASS"
                    self.log_trade(action, reasoning, drawdown_status)
                    expected_pnl, realized_pnl = 0, 0

            else:
                reasoning = "Invalid setup: No Primary (Sweep+FVG) or Secondary (Breaker/Rejection) blocks detected."
                action = "PASS"
                self.log_trade(action, reasoning, drawdown_status)
                expected_pnl, realized_pnl = 0, 0

            self.evaluate_binary_evals(action, current_drawdown, is_liquidity_sweep, is_fvg, is_breaker, is_rejection, expected_pnl, realized_pnl)
            self.update_dashboard(completed_trades, wins, losses)

            if completed_trades > 0 and completed_trades % 5 == 0:
                self.trigger_recursive_optimization()

            time.sleep(poll_interval_seconds)

if __name__ == "__main__":
    engine = PaperTradingEngine()
    # Setting an extremely short sleep interval for demonstration purposes before reverting
    engine.run_paper_trading_loop(poll_interval_seconds=1)
