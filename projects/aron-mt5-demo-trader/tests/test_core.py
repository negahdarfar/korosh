import pandas as pd
import pytest
from aron_trader.core import add_indicators, position_size, validate_ohlcv
from aron_trader.backtest import run_backtest


def sample_data(n=140):
    close = [1.10 + i * 0.0002 for i in range(n)]
    return pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n, freq="15min"),
        "open": close, "high": [x + 0.0005 for x in close],
        "low": [x - 0.0005 for x in close], "close": close,
        "volume": [1000] * n,
    })


def test_indicators_are_created():
    result = add_indicators(sample_data())
    assert {"ema_fast", "ema_slow", "rsi", "atr"}.issubset(result.columns)
    assert result["atr"].dropna().gt(0).all()


def test_position_size_respects_risk_cash():
    lots = position_size(1000, 0.005, 0.01, 100000)
    assert lots == pytest.approx(0.005)


def test_position_size_rejects_excessive_risk():
    with pytest.raises(ValueError):
        position_size(1000, 0.1, 0.01)


def test_validation_rejects_bad_candles():
    bad = sample_data(5)
    bad.loc[0, "high"] = 0.5
    with pytest.raises(ValueError):
        validate_ohlcv(bad)


def test_backtest_returns_metrics_without_execution():
    result = run_backtest(sample_data())
    assert result["starting_balance"] == 1000
    assert result["ending_balance"] > 0
    assert "trade_log" in result
