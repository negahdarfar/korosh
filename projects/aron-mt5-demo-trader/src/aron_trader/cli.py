"""Command-line runner for offline CSV backtests."""
import argparse
import json
import pandas as pd
from .backtest import run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="ARON demo-trader offline backtest")
    parser.add_argument("--csv", required=True, help="Path to OHLCV CSV file")
    parser.add_argument("--symbol", default="UNKNOWN")
    parser.add_argument("--balance", type=float, default=1000.0)
    args = parser.parse_args()
    result = run_backtest(pd.read_csv(args.csv), starting_balance=args.balance)
    result.pop("trade_log", None)
    print(json.dumps({"symbol": args.symbol, **result}, indent=2, default=str))


if __name__ == "__main__":
    main()
