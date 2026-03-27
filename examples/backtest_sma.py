"""Example: Backtest SMA Crossover strategy."""

import sys
sys.path.insert(0, ".")

from quantflow.data import CSVDataFeed
from quantflow.engine import BacktestEngine
from quantflow.risk import RiskManager
from quantflow.strategies import SMACrossover
from quantflow.utils import setup_logging

setup_logging(level="INFO")

# Load data
data = CSVDataFeed("data/sample_ohlcv.csv")

# Configure strategy
strategy = SMACrossover(fast_period=10, slow_period=30, size=100)

# Configure risk
risk = RiskManager(
    max_position_pct=0.10,
    max_drawdown_pct=0.25,
    stop_loss_pct=0.05,
    take_profit_pct=0.15,
)

# Run backtest
engine = BacktestEngine(
    data_feed=data,
    strategy=strategy,
    initial_capital=100_000,
    commission=0.001,
    slippage=0.0005,
    symbol="SYNTH",
    risk_manager=risk,
)

result = engine.run()
result.print_summary()
result.plot(save_path="output/sma_crossover_report.png")
