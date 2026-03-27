"""MACD Trend Strategy — trade on MACD signal line crossovers."""

from __future__ import annotations

from quantflow.core.models import Bar
from quantflow.indicators import MACD
from quantflow.strategies.base import Strategy, Signal


class MACDTrend(Strategy):
    """Buy when MACD crosses above signal, sell when it crosses below."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, size: float = 100) -> None:
        super().__init__(name="MACDTrend")
        self.macd = MACD(fast_period=fast, slow_period=slow, signal_period=signal)
        self.size = size
        self._prev_hist: float | None = None

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        macd_val, signal_val, hist = self.macd.calculate(bar.close_prices)
        if hist is None:
            return self.hold()

        result = self.hold()
        if self._prev_hist is not None:
            if self._prev_hist <= 0 < hist:
                result = self.buy(size=self.size)
            elif self._prev_hist >= 0 > hist:
                result = self.sell(size=self.size)

        self._prev_hist = hist
        return result
