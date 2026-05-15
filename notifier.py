import requests
import os

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_message(self, message):
        if not self.bot_token or not self.chat_id: return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try: requests.post(url, json=payload)
        except: pass

    def notify_trade_open(self, symbol, direction, sl, tp, reason):
        self.send_message(f"🟢 *TRADE OPENED*\n\n**Symbol:** {symbol}\n**Action:** {direction}\n**SL:** {sl:.2f}\n**TP:** {tp:.2f}\n\n**Reasoning:** {reason}")

    def notify_trade_close(self, symbol, result, pnl):
        icon = "🚀" if result == 'win' else "💥"
        self.send_message(f"{icon} *TRADE CLOSED*\n\n**Symbol:** {symbol}\n**Result:** {result.upper()}\n**PnL:** ${pnl:.2f}")

    def notify_circuit_breaker(self, symbol, reason):
        self.send_message(f"🛑 *EMERGENCY CIRCUIT BREAKER*\n\n**Symbol:** {symbol}\n**Trigger:** {reason}\nTrading halted.")

    def notify_midnight_summary(self, total_pnl, evolutions):
        self.send_message(f"🌙 *MIDNIGHT EVOLUTION REPORT*\n\n**Total PnL:** ${total_pnl:.2f}\n\n**Evolutions:**\n{evolutions}")
