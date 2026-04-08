"""Example: Compare multiple strategies on the same data."""

import sys
sys.path.insert(0, ".")

from quantflow.data import CSVDataFeed
from quantflow.engine import BacktestEngine
from quantflow.strategies import SMACrossover, RSIMeanReversion, MACDTrend, BollingerBreakout
from quantflow.utils import setup_logging

setup_logging(level="WARNING")

strategies = [
    SMACrossover(fast_period=10, slow_period=30),
    RSIMeanReversion(period=14, oversold=30, overbought=70),
    MACDTrend(fast=12, slow=26, signal=9),
    BollingerBreakout(period=20, num_std=2.0),
]

print("\n" + "=" * 80)
print("  MULTI-STRATEGY COMPARISON")
print("=" * 80)
print(f"  {'Strategy':<25} {'Return':>10} {'Trades':>8} {'Win Rate':>10} {'Sharpe':>8} {'Max DD':>10}")
print("-" * 80)

for strategy in strategies:
    data = CSVDataFeed("data/sample_ohlcv.csv")
    engine = BacktestEngine(data_feed=data, strategy=strategy, initial_capital=100_000, symbol="SYNTH")
    result = engine.run()

    print(f"  {strategy.name:<25} {result.total_return:>10.2%} {result.num_trades:>8d} "
          f"{result.win_rate:>10.2%} {result.sharpe_ratio():>8.2f} {result.max_drawdown:>10.2%}")

print("=" * 80 + "\n")
