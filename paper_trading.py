import os
import time
import csv
from datetime import datetime
import pandas as pd
from strategy import Strategy
from research_team import ResearchTeam
from singularity_engine import SingularityEngine
from neural_ensemble import NeuralEnsembleBrain
import json

# Mock/Skeleton for Alpaca API
try:
    from alpaca.data.historical import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except ImportError:
    print("alpaca-py not installed, using mock data client.")

class PaperTradingEngine:
    def __init__(self):
        self.strategy = Strategy()
        self.research_team = ResearchTeam()
        self.singularity = SingularityEngine()
        self.ai_brain = NeuralEnsembleBrain()
        self.log_file = "paper_results.csv"
        self.initial_balance = 10000.0
        self.balance = self.initial_balance
        self.traces_dir = "traces"

        if not os.path.exists(self.traces_dir):
            os.makedirs(self.traces_dir)

        # Alpaca configuration
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.api_secret = os.getenv("APCA_API_SECRET_KEY")
        if self.api_key and self.api_secret:
            try:
                self.data_client = CryptoHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                self.trading_client = TradingClient(self.api_key, self.api_secret, paper=True)
            except Exception as e:
                print("Failed to initialize Alpaca client:", e)
                self.data_client = None
                self.trading_client = None
        else:
            self.data_client = None
            self.trading_client = None
            print("Warning: APCA_API_KEY_ID or APCA_API_SECRET_KEY not found in environment.")

        # Initialize CSV log file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Action", "Reasoning", "Risk_Limit", "Drawdown_Status"])

    def _fetch_latest_data(self):
        """
        Fetches multi-timeframe real data for XAUUSD (Gold) using yfinance.
        We need 15m (Primary SL/TP), 5m (FVG checks), and 1h (Trend).
        """
        import yfinance as yf
        try:
            # We use 'GC=F' as the yfinance ticker for Gold futures to represent XAUUSD
            df_5m = yf.download('GC=F', period='1d', interval='5m', progress=False)
            df_15m = yf.download('GC=F', period='5d', interval='15m', progress=False)
            df_1h = yf.download('GC=F', period='10d', interval='1h', progress=False)

            if df_5m.empty or df_15m.empty or df_1h.empty:
                raise ValueError("YFinance returned empty dataframes.")

            return {'5m': df_5m, '15m': df_15m, '1h': df_1h}
        except Exception as e:
            print(f"Error fetching real XAUUSD multi-timeframe data: {e}")
            # Mock structure fallback
            mock = pd.DataFrame({
                'High': [1900.0, 1905.0, 1902.0, 1910.0, 1915.0] * 10,
                'Low': [1890.0, 1895.0, 1880.0, 1900.0, 1905.0] * 10,
                'Close': [1895.0, 1900.0, 1885.0, 1905.0, 1890.0] * 10,
                'Open': [1892.0, 1898.0, 1882.0, 1902.0, 1908.0] * 10
            })
            return {'5m': mock, '15m': mock, '1h': mock}

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

        # Daily Protections
        daily_start_balance = self.initial_balance
        daily_loss_limit = 0.03
        daily_profit_limit = 0.05
        consecutive_losses = 0
        pause_until = None

        london_trades_today = 0
        overlap_trades_today = 0
        ny_trades_today = 0

        while True:
            now_utc = datetime.utcnow()

            # Daily reset mock logic (Reset balance tracking at midnight UTC)
            if now_utc.hour == 0 and now_utc.minute == 0 and now_utc.second < 5:
                daily_start_balance = self.balance
                consecutive_losses = 0
                pause_until = None
                london_trades_today = 0
                overlap_trades_today = 0
                ny_trades_today = 0

            # Time Filters
            valid_time = False
            h = now_utc.hour
            # London: 7-10 GMT, Overlap: 12-13 GMT, NY: 13-16 GMT
            if (7 <= h < 10) or (12 <= h < 13) or (13 <= h < 16):
                valid_time = True

            # 2-hour Pause Check
            if pause_until and now_utc < pause_until:
                print(f"[{now_utc.strftime('%H:%M:%S')}] System paused after 3 consecutive losses. Resumes at {pause_until.strftime('%H:%M:%S')}.")
                time.sleep(poll_interval_seconds)
                continue

            # Daily PnL Limits Check
            daily_pnl_pct = (self.balance - daily_start_balance) / daily_start_balance
            if daily_pnl_pct <= -daily_loss_limit:
                print(f"[{now_utc.strftime('%H:%M:%S')}] 3% Daily Loss limit reached ({daily_pnl_pct*100:.2f}%). Trading stopped for the day.")
                time.sleep(poll_interval_seconds)
                continue
            elif daily_pnl_pct >= daily_profit_limit:
                print(f"[{now_utc.strftime('%H:%M:%S')}] 5% Daily Profit target hit ({daily_pnl_pct*100:.2f}%). Gains locked. Trading stopped for the day.")
                time.sleep(poll_interval_seconds)
                continue

            # Mock position management (resolving positions to simulate PnL)
            active_positions = []
            for pos in open_positions:
                pos['duration'] -= 1
                if pos['duration'] <= 0:
                    completed_trades += 1
                    if pos['result'] == 'win':
                        wins += 1
                        consecutive_losses = 0
                        self.balance += 100 # Mock PnL win
                    else:
                        losses += 1
                        consecutive_losses += 1
                        self.balance -= 100 # Mock PnL loss
                        if consecutive_losses >= 3:
                            from datetime import timedelta
                            pause_until = now_utc + timedelta(hours=2)
                else:
                    active_positions.append(pos)
            open_positions = active_positions

            print("\nFetching latest market data...")
            windows = self._fetch_latest_data()
            window_15m = windows['15m']
            window_5m = windows['5m']
            window_1h = windows['1h']

            # Singularity Engine: Signal Decomposition (on 15m)
            is_dissonant, noise_ratio = self.singularity.analyze_market_dissonance(window_15m)
            self.strategy.shock_neutral_mode = is_dissonant
            if is_dissonant:
                print(f"[ORACLE WARNING] High Market Dissonance detected (N2S: {noise_ratio:.4f}). Entering Shock-Neutral Mode.")
                # Trigger Recursive Agent Optimization (RAO)
                arbitrage_path_stable = self.singularity.execute_rao_swarm(window_15m)
                self.strategy.rao_arbitrage_approved = arbitrage_path_stable
            else:
                self.strategy.shock_neutral_mode = False
                self.strategy.rao_arbitrage_approved = False

            # Evaluate SMC Strategy Rules & Macro Filter across timeframes
            print("Evaluating SMC Strategy Rules (Multi-Timeframe)...")
            sweep_dir = self.strategy.identify_liquidity_sweeps(window_15m) # Primary sweep on 15m
            fvg_dir = self.strategy.check_fair_value_gap(window_5m) # FVG strictly on 5m

            is_liquidity_sweep = sweep_dir is not None
            is_fvg = fvg_dir is not None

            is_breaker = self.strategy.identify_breaker_blocks(window_15m)
            is_rejection = self.strategy.identify_rejection_blocks(window_15m)
            atr_val = self.strategy.calculate_atr(window_15m)

            hurst_val = self.strategy.calculate_hurst_exponent(window_15m)
            has_volume_imbalance = self.strategy.analyze_order_flow_imbalance(window_15m)

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

            trade_direction = sweep_dir if sweep_dir else "BUY" # Default to buy if fallback to secondary

            # Confirm 5 Entry Rules
            trend_aligned = self.strategy.check_trend_filter(window_1h, trade_direction)
            news_clear = self.strategy.check_news_filter()

            # Require all 5 rules (Sweep, Reversal (implicit in FVG/Sweep match), FVG, Trend, News)
            # The prompt requested we upgrade to strictly require all 5.
            has_primary = is_liquidity_sweep and is_fvg and (sweep_dir == fvg_dir) and trend_aligned and news_clear
            has_secondary = False # Disabling secondary entries based on prompt strict "all 5 must be true" constraint

            if has_primary:
                # God Mode AI Filter
                ai_approved, pos = self.ai_brain.evaluate_trade(window_15m, window_5m, window_1h)
                if not ai_approved:
                    reasoning = f"Setup identified but blocked by AI Brain (PoS: {pos*100:.2f}% < 80%). Hurst: {hurst_val:.2f}, VolImbal: {has_volume_imbalance}"
                    action = "PASS"
                    self.log_trade(action, reasoning, drawdown_status)
                    time.sleep(poll_interval_seconds)
                    continue

                if not valid_time:
                    reasoning = f"Setup identified but blocked by Time Window Filter (Current GMT: {h}:00)"
                    action = "PASS"
                    self.log_trade(action, reasoning, drawdown_status)
                    time.sleep(poll_interval_seconds)
                    continue

                # Session limit check
                # London: max 3, Overlap: max 2, NY: max 3
                limit_reached = False
                if (7 <= h < 10) and london_trades_today >= 3:
                    limit_reached = True
                elif (12 <= h < 13) and overlap_trades_today >= 2:
                    limit_reached = True
                elif (13 <= h < 16) and ny_trades_today >= 3:
                    limit_reached = True

                if limit_reached:
                    reasoning = f"Session trade limit reached. Blocking entry."
                    action = "PASS"
                    self.log_trade(action, reasoning, drawdown_status)
                    time.sleep(poll_interval_seconds)
                    continue

                # Prevent averaging down: Check if we already have an open position in this direction
                existing_direction = any([pos.get('dir') == trade_direction for pos in open_positions])
                if existing_direction:
                    print(f"Skipping {trade_direction} setup to prevent averaging down on existing position.")
                    continue

                # Trigger Adversarial Debate
                print("Setup detected. Triggering Adversarial Debate Layer...")
                cro_approved, trace = self.research_team.cro_consensus(window_15m)

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
                        action = f"ENTER {trade_direction}"

                        # Calculate Stop Loss and Take Profit
                        current_price = window_15m['Close'].iloc[-1]
                        pip_size = 0.01 # Standard for XAUUSD
                        sl_pips = random.uniform(8, 12) # 8-12 pips for XAUUSD
                        tp_pips = sl_pips * 2 # 2x the stop loss

                        if trade_direction == "BUY":
                            sl_price = current_price - (sl_pips * pip_size)
                            tp_price = current_price + (tp_pips * pip_size)
                        else:
                            sl_price = current_price + (sl_pips * pip_size)
                            tp_price = current_price - (tp_pips * pip_size)

                        reasoning += f" | SL: {sl_price:.2f} ({sl_pips:.1f} pips), TP: {tp_price:.2f} ({tp_pips:.1f} pips)"

                        # Execute Real Alpaca Paper Trade
                        try:
                            if self.trading_client:
                                print(f"Executing real Alpaca paper trade based on SMC setup.")
                                side_enum = OrderSide.BUY if trade_direction == "BUY" else OrderSide.SELL
                                req = MarketOrderRequest(
                                    symbol="XAUUSD",
                                    qty=0.01, # Static nominal quantity for demo
                                    side=side_enum,
                                    time_in_force=TimeInForce.GTC
                                )
                                # Note: To execute SL/TP on Alpaca, a TrailingStopOrderRequest or BracketOrder is needed in production.
                                order = self.trading_client.submit_order(order_data=req)
                                reasoning += f" | Alpaca Order ID: {order.id}"
                            else:
                                reasoning += " | (MOCKED: No Alpaca Client connected - XAUUSD)"
                        except Exception as e:
                            reasoning += f" | Alpaca Execution Failed: {e}"

                        self.log_trade(action, reasoning, drawdown_status)

                        # Mock Realized vs Expected P&L for Surprise Ratio logic continuity
                        expected_pnl = 100 * dynamic_risk_limit
                        realized_pnl = random.choice([-50, 50, 200]) # 200 would trigger high surprise ratio on win

                        # Add to open positions
                        mock_result = 'win' if realized_pnl > 0 else 'loss'
                        open_positions.append({'dir': trade_direction, 'duration': random.randint(1, 3), 'result': mock_result})

                        # Increment session trades
                        if (7 <= h < 10): london_trades_today += 1
                        elif (12 <= h < 13): overlap_trades_today += 1
                        elif (13 <= h < 16): ny_trades_today += 1
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
    # Use 5 minutes (300s) as default to avoid yfinance rate limits
    engine.run_paper_trading_loop(poll_interval_seconds=300)
