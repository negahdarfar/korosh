"""Offline indicators, signal generation, and risk sizing. No broker execution."""
from __future__ import annotations

import math
import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


def validate_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    data = frame.copy()
    for col in ("open", "high", "low", "close", "volume"):
        data[col] = pd.to_numeric(data[col], errors="raise")
    if data.empty:
        raise ValueError("OHLCV data is empty")
    if (data["high"] < data[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("High must be >= open, close, and low")
    if (data["low"] > data[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("Low must be <= open, close, and high")
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    data = data.sort_values("timestamp").reset_index(drop=True)
    return data


def add_indicators(frame: pd.DataFrame, fast: int = 20, slow: int = 50,
                   rsi_period: int = 14, atr_period: int = 14) -> pd.DataFrame:
    if fast <= 0 or slow <= fast or rsi_period <= 1 or atr_period <= 0:
        raise ValueError("Invalid indicator periods")
    data = validate_ohlcv(frame)
    close = data["close"]
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / rsi_period, adjust=False,
                                   min_periods=rsi_period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / rsi_period, adjust=False,
                                      min_periods=rsi_period).mean()
    rs = gain / loss.replace(0, float("nan"))
    data["rsi"] = 100 - (100 / (1 + rs))
    data.loc[(loss == 0) & (gain > 0), "rsi"] = 100
    data["ema_fast"] = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    data["ema_slow"] = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    previous_close = close.shift(1)
    true_range = pd.concat([
        data["high"] - data["low"],
        (data["high"] - previous_close).abs(),
        (data["low"] - previous_close).abs(),
    ], axis=1).max(axis=1)
    data["atr"] = true_range.ewm(alpha=1 / atr_period, adjust=False,
                                  min_periods=atr_period).mean()
    return data


def generate_signal(row: pd.Series) -> str:
    """Simple research rule: trend alignment plus RSI recovery from pullback."""
    required = ("ema_fast", "ema_slow", "rsi")
    if any(pd.isna(row.get(key)) for key in required):
        return "HOLD"
    if row["ema_fast"] > row["ema_slow"] and 40 <= row["rsi"] <= 60:
        return "BUY"
    if row["ema_fast"] < row["ema_slow"] and 40 <= row["rsi"] <= 60:
        return "SELL"
    return "HOLD"


def position_size(balance: float, risk_fraction: float, stop_distance: float,
                  value_per_price_unit_per_lot: float = 1.0) -> float:
    """Return lots for a supplied instrument-specific value conversion.

    The caller must supply the correct contract/tick-value conversion for the
    symbol and account currency. This generic helper deliberately does not
    guess Forex/CFD contract specifications.
    """
    values = (balance, risk_fraction, stop_distance, value_per_price_unit_per_lot)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Inputs must be finite")
    if balance <= 0 or not 0 < risk_fraction <= 0.02:
        raise ValueError("Balance must be positive and risk_fraction in (0, 0.02]")
    if stop_distance <= 0 or value_per_price_unit_per_lot <= 0:
        raise ValueError("Stop distance and value conversion must be positive")
    risk_cash = balance * risk_fraction
    return risk_cash / (stop_distance * value_per_price_unit_per_lot)
