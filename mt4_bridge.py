import zmq
import json

class MT4Bridge:
    def __init__(self, host="tcp://127.0.0.1", port=5555):
        """
        Initializes the ZeroMQ connection to the MT4 terminal.
        Assumes the MT4 terminal has an EA running a ZMQ PULL or REP server.
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        try:
            self.socket.connect(f"{host}:{port}")
            print(f"MT4 Bridge initialized. Connected to {host}:{port}")
        except Exception as e:
            print(f"Failed to initialize MT4 Bridge: {e}")

    def relay_trade(self, symbol, order_type, lots, sl=0.0, tp=0.0, magic=12345):
        """
        Relays a trade command to MetaTrader 4 via ZeroMQ.
        """
        trade_payload = {
            "action": "TRADE",
            "symbol": symbol,
            "type": order_type,
            "lots": lots,
            "sl": sl,
            "tp": tp,
            "magic": magic
        }

        try:
            # Send the trade request as a JSON string
            self.socket.send_string(json.dumps(trade_payload))

            # Wait for MT4 EA confirmation response (Mocking timeout handling)
            # Use a brief poll to prevent locking the main thread if MT4 is disconnected
            if self.socket.poll(3000):
                response = self.socket.recv_string()
                print(f"[MT4 BRIDGE] Response: {response}")
                return response
            else:
                print("[MT4 BRIDGE] Request timeout. MT4 terminal not responding.")
                return None
        except Exception as e:
            print(f"[MT4 BRIDGE ERROR] {e}")
            return None

    def cleanup(self):
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    bridge = MT4Bridge()
    # Mock sending an RAO-approved trade
    print("Testing mock RAO-approved trade relay...")
    bridge.relay_trade(symbol="EURUSD", order_type="OP_BUY", lots=0.1)
