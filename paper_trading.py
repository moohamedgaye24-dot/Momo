import os
import time
import csv
from datetime import datetime
import pandas as pd
from strategy import Strategy
from research_team import ResearchTeam
from singularity_engine import SingularityEngine
from neural_ensemble import NeuralEnsembleBrain
from news_analyst import NewsAnalyst
from notifier import TelegramNotifier
import json
import random

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
        self.news_engine = NewsAnalyst()
        self.telegram = TelegramNotifier()
        self.log_file = "paper_results.csv"
        self.initial_balance = 10000.0
        self.balance = self.initial_balance
        self.traces_dir = "traces"
        self.symbols = ["XAUUSD", "XAGUSD", "EURUSD"]
        self.global_compounding_multiplier = 1.0
        self.last_week_balance = self.initial_balance

        self.symbol_states = {}
        for sym in self.symbols:
            self.symbol_states[sym] = {
                "balance": self.initial_balance,
                "daily_start_balance": self.initial_balance,
                "consecutive_losses": 0,
                "pause_until": None,
                "open_positions": [],
                "london_trades": 0,
                "overlap_trades": 0,
                "ny_trades": 0,
                "wins": 0,
                "losses": 0,
                "completed_trades": 0,
                "consensus_streak": 0,
                "notified_loss": False,
                "notified_profit": False
            }

        if not os.path.exists(self.traces_dir): os.makedirs(self.traces_dir)

        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.api_secret = os.getenv("APCA_API_SECRET_KEY")
        if self.api_key and self.api_secret:
            try:
                self.data_client = CryptoHistoricalDataClient(api_key=self.api_key, secret_key=self.api_secret)
                self.trading_client = TradingClient(self.api_key, self.api_secret, paper=True)
            except:
                self.data_client = None
                self.trading_client = None
        else:
            self.data_client = None
            self.trading_client = None

        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Action", "Reasoning", "Risk_Limit", "Drawdown_Status"])

    def _fetch_latest_data(self, symbol):
        import yfinance as yf
        yf_map = {"XAUUSD": "GC=F", "XAGUSD": "SI=F", "EURUSD": "EURUSD=X"}
        yf_ticker = yf_map.get(symbol, "GC=F")
        try:
            df_5m = yf.download(yf_ticker, period='1d', interval='5m', progress=False)
            df_15m = yf.download(yf_ticker, period='5d', interval='15m', progress=False)
            df_1h = yf.download(yf_ticker, period='10d', interval='1h', progress=False)
            if df_5m.empty or df_15m.empty or df_1h.empty: raise ValueError("Empty")
            return {'5m': df_5m, '15m': df_15m, '1h': df_1h}
        except:
            mock = pd.DataFrame({'High': [1900.0]*10, 'Low': [1890.0]*10, 'Close': [1895.0]*10, 'Open': [1892.0]*10})
            return {'5m': mock, '15m': mock, '1h': mock}

    def log_trade(self, action, reasoning, drawdown_status):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        risk = f"{self.strategy.risk_per_trade_limit * 100}%"
        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, action, reasoning, risk, drawdown_status])

    def evaluate_binary_evals(self, action, current_drawdown, is_liquidity_sweep, is_fvg, is_breaker, is_rejection, expected_pnl=0, realized_pnl=0):
        passed = True
        reason = ""
        if current_drawdown >= self.strategy.total_drawdown_kill_switch:
            passed, reason = False, "Failed: 5% total drawdown limit breached."
        if action == "ENTER LONG/SHORT":
            if not ((is_liquidity_sweep and is_fvg) or (is_breaker or is_rejection)):
                passed, reason = False, "Failed: Entered trade without SMC confirmation."
        if realized_pnl > 0:
            surprise_ratio = abs(realized_pnl - expected_pnl)
            if surprise_ratio > abs(expected_pnl) * 0.5:
                with open("learnings.md", "a") as f: f.write(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Lucky Win: High Surprise Ratio.\n")
        if not passed:
            with open("learnings.md", "a") as f: f.write(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Eval Failure: {reason}\n")

    def update_dashboard(self, completed_trades, wins, losses):
        content = f"# Performance Monitor\n\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        content += f"**Total Paper P&L:** TBD\n**Current Win Rate:** {(wins / completed_trades * 100) if completed_trades > 0 else 0:.2f}%\n"
        with open("performance_monitor.md", "w") as f: f.write(content)

    def trigger_recursive_optimization(self):
        with open("performance_monitor.md", "a") as f: f.write(f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Routine analysis.")

    def run_paper_trading_loop(self, poll_interval_seconds=300):
        max_open_positions = 5
        daily_loss_limit = 0.03
        daily_profit_limit = 0.05
        while True:
            import datetime as dt_mod
            now_utc = dt_mod.datetime.now(dt_mod.timezone.utc)
            h = now_utc.hour

            if now_utc.weekday() == 0 and h == 0 and now_utc.minute == 0 and now_utc.second < max(poll_interval_seconds, 60):
                current_total_balance = sum([s['balance'] for s in self.symbol_states.values()])
                if current_total_balance > self.last_week_balance: self.global_compounding_multiplier *= 1.10
                else: self.global_compounding_multiplier *= 0.90
                self.last_week_balance = current_total_balance

            valid_time = (7 <= h < 10) or (12 <= h < 13) or (13 <= h < 16)
            for symbol, state in self.symbol_states.items():
                if h == 0 and now_utc.minute == 0 and now_utc.second < max(poll_interval_seconds, 60):
                    state['daily_start_balance'], state['consecutive_losses'], state['pause_until'], state['london_trades'], state['overlap_trades'], state['ny_trades'] = state['balance'], 0, None, 0, 0, 0
                    state['notified_loss'], state['notified_profit'] = False, False
                if state['pause_until'] and now_utc < state['pause_until']: continue

                daily_pnl_pct = (state['balance'] - state['daily_start_balance']) / state['daily_start_balance']
                if daily_pnl_pct <= -daily_loss_limit:
                    if not state['notified_loss']: self.telegram.notify_circuit_breaker(symbol, f"3% Loss"); state['notified_loss'] = True
                    continue
                elif daily_pnl_pct >= daily_profit_limit:
                    if not state['notified_profit']: self.telegram.notify_circuit_breaker(symbol, f"5% Profit"); state['notified_profit'] = True
                    continue

                active_positions = []
                for pos in state['open_positions']:
                    pos['duration'] -= 1
                    if pos['duration'] <= 0:
                        state['completed_trades'] += 1
                        if pos['result'] == 'win':
                            state['wins'] += 1; state['consecutive_losses'] = 0; state['balance'] += 100
                        else:
                            state['losses'] += 1; state['consecutive_losses'] += 1; state['balance'] -= 100
                            if state['consecutive_losses'] >= 3: state['pause_until'] = now_utc + dt_mod.timedelta(hours=2); self.telegram.notify_circuit_breaker(symbol, "3 Losses")
                        self.telegram.notify_trade_close(symbol, pos['result'], 100 if pos['result'] == 'win' else -100)
                    else: active_positions.append(pos)
                state['open_positions'] = active_positions

                windows = self._fetch_latest_data(symbol)
                window_15m, window_5m, window_1h = windows['15m'], windows['5m'], windows['1h']
                is_dissonant, noise_ratio = self.singularity.analyze_market_dissonance(window_15m)
                self.strategy.shock_neutral_mode = is_dissonant
                if is_dissonant: self.strategy.rao_arbitrage_approved = self.singularity.execute_rao_swarm(window_15m)
                else: self.strategy.rao_arbitrage_approved = False

                sweep_dir = self.strategy.identify_liquidity_sweeps(window_15m)
                fvg_dir = self.strategy.check_fair_value_gap(window_5m)
                is_liquidity_sweep, is_fvg = sweep_dir is not None, fvg_dir is not None
                is_breaker, is_rejection = self.strategy.identify_breaker_blocks(window_15m), self.strategy.identify_rejection_blocks(window_15m)
                atr_val = self.strategy.calculate_atr(window_15m)
                hurst_val = self.strategy.calculate_hurst_exponent(window_15m)
                has_volume_imbalance = self.strategy.analyze_order_flow_imbalance(window_15m)

                trade_direction = sweep_dir if sweep_dir else "BUY"
                dynamic_risk_limit = self.strategy.risk_per_trade_limit * (1 / (atr_val * 100)) * (0.7 if random.choice([True,False]) else 1.0) * self.global_compounding_multiplier
                dynamic_risk_limit *= self.news_engine.check_news_impact(symbol, trade_direction)

                current_drawdown = max((state['daily_start_balance'] - state['balance']) / state['daily_start_balance'], 0.0) if state['daily_start_balance'] > 0 else 0.0
                if current_drawdown >= self.strategy.total_drawdown_kill_switch:
                    self.log_trade("HALT", f"DD limit ({current_drawdown*100}%)", "KILLED")
                    continue

                has_primary = is_liquidity_sweep and is_fvg and (sweep_dir == fvg_dir) and self.strategy.check_trend_filter(window_1h, trade_direction) and self.strategy.check_news_filter()
                if has_primary:
                    ai_approved, pos_ai = self.ai_brain.evaluate_trade(window_15m, window_5m, window_1h)
                    if not ai_approved: self.log_trade("PASS", "AI PoS Blocked", "Safe"); continue
                    if not valid_time: self.log_trade("PASS", "Time Blocked", "Safe"); continue
                    if (7 <= h < 10 and state['london_trades'] >= 3) or (12 <= h < 13 and state['overlap_trades'] >= 2) or (13 <= h < 16 and state['ny_trades'] >= 3):
                        self.log_trade("PASS", "Session limit Blocked", "Safe"); continue
                    if any([p.get('dir') == trade_direction for p in state['open_positions']]): continue

                    cro_approved, trace = self.research_team.cro_consensus(window_15m)
                    state['consensus_streak'] = state['consensus_streak'] + 1 if cro_approved and trace['bull_score'] > trace['bear_score'] * 2.0 else 0
                    if state['consensus_streak'] >= 3: dynamic_risk_limit *= 0.5

                    trace_file = os.path.join(self.traces_dir, f"trace_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}.json")
                    with open(trace_file, "w") as f: json.dump(trace, f)

                    if cro_approved:
                        if self.strategy.shock_neutral_mode and not self.strategy.rao_arbitrage_approved: self.log_trade("PASS", "Shock Neutral Blocked", "Safe")
                        elif len(state['open_positions']) >= max_open_positions: self.log_trade("PASS", "Max Position Blocked", "Safe")
                        else:
                            pip_size = 0.01 if symbol in ["XAUUSD", "XAGUSD"] else 0.0001
                            sl_pips = random.uniform(8, 12)
                            tp_pips = sl_pips * 2
                            current_price = window_15m['Close'].iloc[-1]
                            sl_price = current_price - (sl_pips * pip_size) if trade_direction == "BUY" else current_price + (sl_pips * pip_size)
                            tp_price = current_price + (tp_pips * pip_size) if trade_direction == "BUY" else current_price - (tp_pips * pip_size)

                            try:
                                if self.trading_client:
                                    req = MarketOrderRequest(symbol=symbol, qty=0.01, side=OrderSide.BUY if trade_direction == "BUY" else OrderSide.SELL, time_in_force=TimeInForce.GTC)
                                    self.trading_client.submit_order(order_data=req)
                            except: pass

                            self.telegram.notify_trade_open(symbol, trade_direction, sl_price, tp_price, "Setup Approved")
                            state['open_positions'].append({'dir': trade_direction, 'duration': random.randint(1, 3), 'result': 'win' if random.choice([-50,50,200]) > 0 else 'loss'})
                            if (7 <= h < 10): state['london_trades'] += 1
                            elif (12 <= h < 13): state['overlap_trades'] += 1
                            elif (13 <= h < 16): state['ny_trades'] += 1
                self.evaluate_binary_evals("", current_drawdown, is_liquidity_sweep, is_fvg, is_breaker, is_rejection)

            self.update_dashboard(sum(s['completed_trades'] for s in self.symbol_states.values()), sum(s['wins'] for s in self.symbol_states.values()), sum(s['losses'] for s in self.symbol_states.values()))
            if sum(s['completed_trades'] for s in self.symbol_states.values()) > 0 and sum(s['completed_trades'] for s in self.symbol_states.values()) % 5 == 0:
                self.trigger_recursive_optimization()
            time.sleep(poll_interval_seconds)

if __name__ == "__main__":
    engine = PaperTradingEngine()
    engine.run_paper_trading_loop(poll_interval_seconds=300)
