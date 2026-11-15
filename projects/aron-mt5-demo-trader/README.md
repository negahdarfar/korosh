# ARON MT5 Demo Trader (Phase 1)

A separate, safety-first research and backtesting project for the Aron Groups MT5 demo account.

> **Important:** this phase does not connect to a broker, does not place orders, and does not need account credentials. It is an offline signal/backtest foundation. MT5 Expert Advisors cannot run inside the Android MT5 app; live/demo terminal execution later requires MT5 Desktop on Windows or a Windows VPS.

## Current features
- CSV OHLCV input for any symbol/timeframe.
- EMA trend + RSI pullback signal prototype.
- ATR-based stop distance and risk-based position sizing calculator.
- Backtest simulator with spread/slippage assumptions, one open position at a time, and fixed fractional risk.
- Unit tests and GitHub Actions checks.
- No broker keys, passwords, tokens, or account numbers in the repository.

## Safety defaults
- Demo/research only; no order-sending code in Phase 1.
- Risk per trade: 0.5% (configurable).
- Daily loss stop: 2% (guardrail for a later execution layer).
- Maximum drawdown stop: 6% (guardrail for a later execution layer).
- Minimum planned reward/risk: 2.0.
- Signals are examples for research, not investment advice or a promise of profitability.

## Run locally
Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m aron_trader.cli --csv data/sample_ohlcv.csv --symbol EURUSD
pytest
```

The sample CSV is synthetic demonstration data, not historical market data.

## CSV format
Required columns: `timestamp,open,high,low,close,volume`. Timestamps should be chronological. Use one symbol and timeframe per file.

## Project stages
1. Offline indicators, signal rules, risk calculations and tests.
2. Historical backtesting with realistic costs and out-of-sample validation.
3. Paper trading / signal monitoring.
4. Only after successful validation, design a strictly demo-only MT5 bridge for a Windows terminal, with a hard block against real accounts.

## Android limitation
An Android phone can view/manage an MT5 account, but it cannot host an MT5 Expert Advisor. GitHub Actions can run tests and offline backtests; it is not a persistent broker-connected trading terminal.

## Configuration
Copy `config.example.json` to a local config if needed. Never commit credentials. This project currently has no broker login fields by design.
