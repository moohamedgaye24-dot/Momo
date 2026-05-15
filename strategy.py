import pandas as pd
import numpy as np

class Strategy:
    def __init__(self):
        self.risk_per_trade_limit = 0.01
        self.total_drawdown_kill_switch = 0.05
        self.shock_neutral_mode = False
        self.rao_arbitrage_approved = False

    def identify_liquidity_sweeps(self, window):
        if len(window) < 5:
            return None
        close_p = window['Close'].iloc[-1]
        if isinstance(close_p, pd.Series): close_p = close_p.iloc[0]
        recent_highs = window['High'].iloc[-5:-1]
        recent_lows = window['Low'].iloc[-5:-1]
        if isinstance(recent_highs, pd.DataFrame): recent_highs = recent_highs.iloc[:, 0]
        if isinstance(recent_lows, pd.DataFrame): recent_lows = recent_lows.iloc[:, 0]

        sweep_high = close_p > recent_highs.max()
        sweep_low = close_p < recent_lows.min()

        if sweep_low: return "BUY"
        if sweep_high: return "SELL"
        return None

    def check_fair_value_gap(self, window):
        if len(window) < 3:
            return None
        highs = window['High']
        lows = window['Low']
        if isinstance(highs, pd.DataFrame): highs = highs.iloc[:, 0]
        if isinstance(lows, pd.DataFrame): lows = lows.iloc[:, 0]

        bullish_fvg = lows.iloc[-1] > highs.iloc[-3]
        bearish_fvg = highs.iloc[-1] < lows.iloc[-3]

        if bullish_fvg: return "BUY"
        if bearish_fvg: return "SELL"
        return None

    def calculate_atr(self, window, period=14):
        if len(window) < period + 1:
            return 0.001
        high_low = window['High'] - window['Low']
        high_close = abs(window['High'] - window['Close'].shift())
        low_close = abs(window['Low'] - window['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean().iloc[-1]

    def check_trend_filter(self, window, direction):
        if len(window) < 50: return True
        ema_50 = window['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        if isinstance(ema_50, pd.Series): ema_50 = ema_50.iloc[0]
        current_price = window['Close'].iloc[-1]
        if isinstance(current_price, pd.Series): current_price = current_price.iloc[0]
        if direction == "BUY": return current_price > ema_50
        elif direction == "SELL": return current_price < ema_50
        return False

    def check_news_filter(self):
        return True

    def calculate_hurst_exponent(self, window, lags_to_test=20):
        ts = window['Close'].values
        if len(ts) < lags_to_test * 2: return 0.5
        tau = []
        lagvec = []
        for lag in range(2, lags_to_test):
            pdiff = np.subtract(ts[lag:], ts[:-lag])
            tau.append(np.sqrt(np.std(pdiff)))
            lagvec.append(lag)
        poly = np.polyfit(np.log(lagvec), np.log(tau), 1)
        return poly[0] * 2.0

    def analyze_order_flow_imbalance(self, window):
        if 'Volume' not in window.columns or len(window) < 5: return True
        recent_vol = window['Volume'].iloc[-5:-1].mean()
        current_vol = window['Volume'].iloc[-1]
        if isinstance(recent_vol, pd.Series): recent_vol = recent_vol.iloc[0]
        if isinstance(current_vol, pd.Series): current_vol = current_vol.iloc[0]
        return current_vol > (recent_vol * 1.5)

    def drawdown_shield_scaler(self, base_lots, current_dissonance_ratio):
        if current_dissonance_ratio > 0.5: return base_lots * 0.25
        elif current_dissonance_ratio > 0.3: return base_lots * 0.50
        return base_lots
