"""SMA Crossover Strategy — classic trend-following approach."""

from __future__ import annotations

from quantflow.core.models import Bar
from quantflow.indicators import SMA
from quantflow.strategies.base import Strategy, Signal


class SMACrossover(Strategy):
    """Buy when fast SMA crosses above slow SMA, sell on cross below."""

    def __init__(self, fast_period: int = 10, slow_period: int = 30, size: float = 100) -> None:
        super().__init__(name="SMACrossover")
        self.fast_sma = SMA(period=fast_period)
        self.slow_sma = SMA(period=slow_period)
        self.size = size
        self._prev_fast: float | None = None
        self._prev_slow: float | None = None

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        fast = self.fast_sma.calculate(bar.close_prices)
        slow = self.slow_sma.calculate(bar.close_prices)

        if fast is None or slow is None:
            return self.hold()

        signal = self.hold()

        if self._prev_fast is not None and self._prev_slow is not None:
            # Golden cross
            if self._prev_fast <= self._prev_slow and fast > slow:
                signal = self.buy(size=self.size)
            # Death cross
            elif self._prev_fast >= self._prev_slow and fast < slow:
                signal = self.sell(size=self.size)

        self._prev_fast = fast
        self._prev_slow = slow
        return signal
