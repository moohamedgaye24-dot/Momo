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

        return sweep_high or sweep_low

    def check_fair_value_gap(self, window):
        if len(window) < 3:
            return False

        highs = window['High']
        lows = window['Low']

        if isinstance(highs, pd.DataFrame):
            highs = highs.iloc[:, 0]
            lows = lows.iloc[:, 0]

        # Bullish FVG: Low of candle 3 is higher than High of candle 1
        bullish_fvg = lows.iloc[-1] > highs.iloc[-3]

        # Bearish FVG: High of candle 3 is lower than Low of candle 1
        bearish_fvg = highs.iloc[-1] < lows.iloc[-3]

        return bullish_fvg or bearish_fvg

    def identify_breaker_blocks(self, window):
        # Mock logic: A failed order block that flips bias
        if len(window) < 5:
            return False
        # Simplified: If price creates a higher high then aggressively breaks the previous low
        # Updated mock to be slightly looser to allow traces to generate in mock runtime
        return True if window['Close'].iloc[-1] < (window['Low'].iloc[-3] * 0.999) else False

    def identify_rejection_blocks(self, window):
        # Mock logic: Identifying long wicks showing rejection
        if len(window) < 2:
            return False
        candle = window.iloc[-1]
        body = abs(candle['Close'] - candle['Open'])
        upper_wick = candle['High'] - max(candle['Close'], candle['Open'])
        lower_wick = min(candle['Close'], candle['Open']) - candle['Low']
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

    def check_market_structure_shift(self, price_data):
        # Placeholder for entering after MSS
        pass

    def execute_trade(self, price_data):
        # Logic to enter only on a Fair Value Gap (FVG) after a Market Structure Shift
        pass
