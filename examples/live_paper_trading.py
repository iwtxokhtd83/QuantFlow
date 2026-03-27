"""Example: Paper trading with RSI Mean Reversion."""

import sys
sys.path.insert(0, ".")

from quantflow.brokers import PaperBroker
from quantflow.engine import LiveEngine
from quantflow.strategies import RSIMeanReversion
from quantflow.utils import setup_logging

setup_logging(level="INFO")

strategy = RSIMeanReversion(period=14, oversold=30, overbought=70, size=50)
broker = PaperBroker(initial_capital=100_000)

engine = LiveEngine(
    strategy=strategy,
    broker=broker,
    symbol="AAPL",
    interval="5s",  # 5-second bars for quick demo
)

print("Starting paper trading... Press Ctrl+C to stop.\n")
engine.start()
