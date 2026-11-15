"""Small, transparent single-position OHLCV backtester (research only)."""
from __future__ import annotations

import pandas as pd
from .core import add_indicators, generate_signal, validate_ohlcv


def run_backtest(frame: pd.DataFrame, starting_balance: float = 1000.0,
                 risk_fraction: float = 0.005, spread: float = 0.0,
                 slippage: float = 0.0, reward_risk: float = 2.0) -> dict:
    if starting_balance <= 0 or not 0 < risk_fraction <= 0.02:
        raise ValueError("Invalid balance or risk fraction")
    if spread < 0 or slippage < 0 or reward_risk < 1:
        raise ValueError("Invalid trading costs or reward/risk")
    data = add_indicators(validate_ohlcv(frame))
    balance = float(starting_balance)
    equity_peak = balance
    max_drawdown = 0.0
    trades = []
    position = None
    # Signals are evaluated at candle close; entries occur on the next candle open.
    for i in range(1, len(data)):
        bar = data.iloc[i]
        prev = data.iloc[i - 1]
        if position is not None:
            exit_price = None
            if position["side"] == "BUY":
                if bar["low"] <= position["stop"]:
                    exit_price = position["stop"]
                elif bar["high"] >= position["target"]:
                    exit_price = position["target"]
            else:
                if bar["high"] >= position["stop"]:
                    exit_price = position["stop"]
                elif bar["low"] <= position["target"]:
                    exit_price = position["target"]
            if exit_price is not None:
                direction = 1 if position["side"] == "BUY" else -1
                pnl = direction * (exit_price - position["entry"]) * position["units"]
                pnl -= (spread + slippage) * position["units"]
                balance += pnl
                trades.append({"side": position["side"], "pnl": pnl,
                               "entry": position["entry"], "exit": exit_price})
                position = None
        if position is None:
            signal = generate_signal(prev)
            atr = prev.get("atr")
            if signal in ("BUY", "SELL") and pd.notna(atr) and atr > 0:
                entry = float(bar["open"])
                stop_distance = float(atr)
                risk_cash = balance * risk_fraction
                units = risk_cash / stop_distance
                direction = 1 if signal == "BUY" else -1
                stop = entry - direction * stop_distance
                target = entry + direction * stop_distance * reward_risk
                position = {"side": signal, "entry": entry, "stop": stop,
                            "target": target, "units": units}
        equity_peak = max(equity_peak, balance)
        if equity_peak > 0:
            max_drawdown = max(max_drawdown, (equity_peak - balance) / equity_peak)
    return {
        "starting_balance": starting_balance,
        "ending_balance": balance,
        "net_profit": balance - starting_balance,
        "trades": len(trades),
        "wins": sum(t["pnl"] > 0 for t in trades),
        "win_rate": (sum(t["pnl"] > 0 for t in trades) / len(trades)) if trades else 0.0,
        "max_drawdown": max_drawdown,
        "trade_log": trades,
        "open_position_at_end": position is not None,
        "note": "Simplified research simulation; no funding, swap, margin, partial fills, or broker contract rules.",
    }
