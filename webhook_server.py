from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import pandas as pd
from singularity_engine import SingularityEngine
from research_team import ResearchTeam
from mt4_bridge import MT4Bridge

app = FastAPI()

# Initialize institutional components
singularity_layer = SingularityEngine()
research_team = ResearchTeam()
mt4_bridge = MT4Bridge()

class TVAlert(BaseModel):
    symbol: str
    action: str
    price: float
    timeframe: str
    volume: float

@app.post("/tv-webhook")
async def tradingview_webhook(alert: TVAlert):
    print(f"\n[WEBHOOK RECEIVED] {alert.action} on {alert.symbol} at {alert.price}")

    # 1. Mock converting the alert into a dataframe window for the Singularity Engine
    # In production, we'd fetch the last 20 candles upon alert trigger
    mock_prices = [alert.price * (1 + (i * 0.001)) for i in range(-10, 1)]
    mock_window = pd.DataFrame({'Close': mock_prices, 'High': mock_prices, 'Low': mock_prices, 'Open': mock_prices})

    # 2. Pass through Singularity Scaling Layer (Noise Rejection)
    is_dissonant, noise_ratio = singularity_layer.analyze_market_dissonance(mock_window)

    if is_dissonant:
        print(f"[REJECTED] Market Dissonance too high (N2S: {noise_ratio:.4f}). Signal discarded to protect capital.")
        return {"status": "rejected", "reason": "market_dissonance_shock"}
    else:
        print(f"[NOISE REJECTED] Signal is clean (N2S: {noise_ratio:.4f}). Proceeding to Adversarial Debate.")

        # 3. Trigger Debate
        cro_approved, trace = research_team.cro_consensus(mock_window)

        if cro_approved:
            print("[CRO APPROVED] Trade cleared by debate consensus.")
            # Execute via MT4 Bridge
            order_type = "OP_BUY" if alert.action.upper() == "BUY" else "OP_SELL"
            # Hardcoded lot size for demo, in production this uses the Volatility Scaler in strategy.py
            response = mt4_bridge.relay_trade(symbol=alert.symbol, order_type=order_type, lots=0.1)

            return {
                "status": "executed",
                "mt4_response": response,
                "trace_bull": trace['bull_score'],
                "trace_bear": trace['bear_score']
            }
        else:
            print("[CRO REJECTED] Trade failed adversarial debate.")
            return {"status": "rejected", "reason": "cro_debate_failure"}

if __name__ == "__main__":
    import uvicorn
    # Run the webhook server
    uvicorn.run(app, host="0.0.0.0", port=8000)
