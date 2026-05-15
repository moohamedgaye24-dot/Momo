from mt4_bridge import MT4Bridge

class DeltaNeutralAgent:
    def __init__(self):
        self.mt4 = MT4Bridge()
        self.net_delta = 0.0
        self.correlation_matrix = {"EURUSD": "USDCHF", "GBPUSD": "USDCAD", "AUDUSD": "EURGBP"}

    def update_portfolio_delta(self, symbol, action, lots):
        self.net_delta += (1 if "BUY" in action else -1) * lots
        self._evaluate_hedging_requirements(symbol)

    def _evaluate_hedging_requirements(self, primary_symbol):
        if abs(self.net_delta) >= 0.5:
            hedge_pair = self.correlation_matrix.get(primary_symbol, None)
            if not hedge_pair: return
            hedge_action = "OP_BUY" if self.net_delta > 0 else "OP_SELL"
            self.mt4.relay_trade(symbol=hedge_pair, order_type=hedge_action, lots=abs(self.net_delta))
            self.net_delta = 0.0
