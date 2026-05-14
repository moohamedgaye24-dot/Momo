# Institutional Hierarchy

This document codifies the operational hierarchy and logic flow of the autonomous self-improving Forex trading system.

## 1. Analysts
- **Technical Analyst (`strategy.py`):** Responsible for parsing 1-hour interval data to identify primary Smart Money Concepts (SMC) setups, including Liquidity Sweeps and Fair Value Gaps (FVG). Also identifies secondary confirmations such as Breaker Blocks and Rejection Blocks, and calculates ATR for volatility-scaled position sizing.
- **News/Sentiment Analyst (`news_analyst.py`):** Calculates a Sentiment Z-score based on real-time news to filter out trades during conflicting macro conditions.

## 2. Researchers (`research_team.py`)
Triggered only when the Technical Analyst identifies a valid SMC setup.
- **Bullish Researcher:** Tasked with aggressively finding every technical, fundamental, and structural reason why the proposed setup will succeed.
- **Bearish Researcher:** Tasked with critically finding every reason why the setup will fail (e.g., hidden liquidity pools, upcoming macro news divergence, or RSI overextension).
- *Darwinian Weights:* The influence of each researcher is dynamically adjusted by the Meta-Learning loop based on their historical accuracy during failed setups.

## 3. Chief Risk Officer (CRO) (`research_team.py` & `paper_trading.py`)
- **Consensus Logic:** Evaluates the arguments from both the Bullish and Bearish researchers. The system will ONLY execute a trade if the CRO determines the Bullish case significantly outweighs the Bearish risks.
- **Invariant Guardrails:** Enforces the hardcoded 1% risk-per-trade limit and the 5% total drawdown kill-switch.

## 4. Fund Manager / Meta-Learner (`backtest_harness.py`)
- **Infinite Learning Loop:** Runs automated binary evaluations on completed trades to log failure patterns to `learnings.md`.
- **Trace Engineering:** Analyzes the JSON debate traces stored in `/traces` to determine which researcher correctly predicted a setup's failure.
- **Recursive Optimization:** Adjusts the Darwinian Weights of the research team and is authorized to rewrite `strategy.py` to filter out specific losing patterns to maximize the Sharpe Ratio.
