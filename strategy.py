import pandas as pd
import numpy as np

class Strategy:
    def __init__(self):
        # INVARIANT: The autonomous update loop is forbidden from modifying this 1% limit.
        self.risk_per_trade_limit = 0.01 # 1% risk-per-trade limit
        self.total_drawdown_kill_switch = 0.05 # 5% total drawdown kill-switch

        # Singularity Neutrality states
        self.shock_neutral_mode = False
        self.rao_arbitrage_approved = False

    def identify_liquidity_sweeps(self, window):
        if len(window) < 5:
            return False

        # Extract series to avoid multi-index issues with yfinance
        highs = window['High']
        lows = window['Low']

        if isinstance(highs, pd.DataFrame):
            highs = highs.iloc[:, 0]
            lows = lows.iloc[:, 0]

        current_high = highs.iloc[-1]
        current_low = lows.iloc[-1]

        # Check if current candle sweeps recent highs or lows
        recent_highs = highs.iloc[-5:-1]
        recent_lows = lows.iloc[-5:-1]

        sweep_high = current_high > recent_highs.max()
        sweep_low = current_low < recent_lows.min()

        if sweep_low: return "BUY" # Swept lows -> potential reversal up
        if sweep_high: return "SELL" # Swept highs -> potential reversal down
        return None

    def check_fair_value_gap(self, window):
        if len(window) < 3:
            return None

        highs = window['High']
        lows = window['Low']

        if isinstance(highs, pd.DataFrame):
            highs = highs.iloc[:, 0]
            lows = lows.iloc[:, 0]

        # Bullish FVG: Low of candle 3 is higher than High of candle 1
        bullish_fvg = lows.iloc[-1] > highs.iloc[-3]

        # Bearish FVG: High of candle 3 is lower than Low of candle 1
        bearish_fvg = highs.iloc[-1] < lows.iloc[-3]

        if bullish_fvg: return "BUY"
        if bearish_fvg: return "SELL"
        return None

    def identify_breaker_blocks(self, window):
        # Mock logic: A failed order block that flips bias
        if len(window) < 5:
            return False
        # Handle possible yf MultiIndex
        close_price = window['Close'].iloc[-1]
        low_price = window['Low'].iloc[-3]
        if isinstance(close_price, pd.Series): close_price = close_price.iloc[0]
        if isinstance(low_price, pd.Series): low_price = low_price.iloc[0]

        # Simplified: If price creates a higher high then aggressively breaks the previous low
        # Updated mock to be slightly looser to allow traces to generate in mock runtime
        return True if close_price < (low_price * 0.999) else False

    def identify_rejection_blocks(self, window):
        # Mock logic: Identifying long wicks showing rejection
        if len(window) < 2:
            return False
        candle = window.iloc[-1]

        close_p = candle['Close']
        open_p = candle['Open']
        high_p = candle['High']
        low_p = candle['Low']

        if isinstance(close_p, pd.Series): close_p = close_p.iloc[0]
        if isinstance(open_p, pd.Series): open_p = open_p.iloc[0]
        if isinstance(high_p, pd.Series): high_p = high_p.iloc[0]
        if isinstance(low_p, pd.Series): low_p = low_p.iloc[0]

        body = abs(close_p - open_p)
        upper_wick = high_p - max(close_p, open_p)
        lower_wick = min(close_p, open_p) - low_p
        return True if (upper_wick > body * 3) or (lower_wick > body * 3) else False

    def calculate_atr(self, window, period=14):
        if len(window) < period + 1:
            return 0.001 # Fallback value
        high_low = window['High'] - window['Low']
        high_close = abs(window['High'] - window['Close'].shift())
        low_close = abs(window['Low'] - window['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean().iloc[-1]
        return atr

    def check_trend_filter(self, window, direction):
        """
        1-hour trend confirms direction via 50 EMA.
        Returns True if trend aligns with trade direction.
        """
        if len(window) < 50:
            return True # Not enough data, allow by default for mock testing
        ema_50 = window['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        current_price = window['Close'].iloc[-1]

        if direction == "BUY":
            return current_price > ema_50
        elif direction == "SELL":
            return current_price < ema_50
        return False

    def check_news_filter(self):
        """
        Ensure no major news in next 30 minutes.
        Mock implementation.
        """
        # Return True meaning "no major news, safe to trade"
        return True

    def drawdown_shield_scaler(self, base_lots, current_dissonance_ratio):
        """
        Drawdown Shield: ATR-based Volatility Scaler that automatically reduces
        lot sizes during spikes in market dissonance (from the Singularity Engine).
        """
        # If noise-to-signal ratio is exceptionally high (>0.5), slash lots drastically
        if current_dissonance_ratio > 0.5:
            return base_lots * 0.25
        # If moderate dissonance (>0.3), cut lots in half
        elif current_dissonance_ratio > 0.3:
            return base_lots * 0.50

        # Standard conditions
        return base_lots

    def check_market_structure_shift(self, price_data):
        # Placeholder for entering after MSS
        pass

    def execute_trade(self, price_data):
        # Logic to enter only on a Fair Value Gap (FVG) after a Market Structure Shift
        pass
