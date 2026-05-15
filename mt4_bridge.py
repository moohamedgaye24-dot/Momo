import zmq
import json

class MT4Bridge:
    def __init__(self, host="tcp://127.0.0.1", port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        try: self.socket.connect(f"{host}:{port}")
        except: pass

    def relay_trade(self, symbol, order_type, lots, sl=0.0, tp=0.0, magic=12345):
        trade_payload = {"action": "TRADE", "symbol": symbol, "type": order_type, "lots": lots, "sl": sl, "tp": tp, "magic": magic}
        try:
            self.socket.send_string(json.dumps(trade_payload))
            if self.socket.poll(3000): return self.socket.recv_string()
            return None
        except: return None
