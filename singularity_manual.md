# Singularity Engine: Shock-Response Protocols

This manual details the execution protocols integrated into the autonomous trading fund when 'Market Dissonance' is detected.

## 1. Signal Decomposition (FFT & Laurent Approximation)
The `SingularityEngine` analyzes raw tick/candle data to separate standard trending market behavior from unstable, diverging shocks:
- **Fast Fourier Transform (FFT):** Extracts high-frequency market noise. A Noise-to-Signal ratio > 0.4 triggers a warning.
- **Laurent Divergence:** A mocked approximation tracks rapid geometric divergence from the 'Regular Part' (moving averages). Divergence > 2% flags the 'Principal Part' (unstable shock).

## 2. Recursive Agent Optimization (RAO)
If Market Dissonance is flagged, the system immediately switches to **Shock-Neutral Mode**.
- The main `paper_trading.py` loop calls `execute_rao_swarm`.
- A recursive sub-agent tree (simulated to depth 10) is spawned to process the shock dynamics.
- The swarm's goal is to find a stable arbitrage path that survives the geometric Laurent divergence.

## 3. Singularity Neutrality
- **Approval Constraints:** The Chief Risk Officer (CRO) cannot execute an otherwise valid SMC setup during Shock-Neutral Mode *unless* the RAO Swarm explicitly returns `arbitrage_path_stable = True`.
- **Rejection Protocol:** If the swarm fails to find a stable path through the noise, the trade is aborted and logged as: `"Setup approved by CRO, but aborted due to Shock-Neutral mode. RAO Swarm failed to find stable arbitrage across Laurent divergence."`
