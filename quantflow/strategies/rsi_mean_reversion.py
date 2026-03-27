"""RSI Mean Reversion Strategy — buy oversold, sell overbought."""

from __future__ import annotations

from quantflow.core.models import Bar
from quantflow.indicators import RSI
from quantflow.strategies.base import Strategy, Signal


class RSIMeanReversion(Strategy):
    """Buy when RSI drops below oversold, sell when RSI rises above overbought."""

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, size: float = 100) -> None:
        super().__init__(name="RSIMeanReversion")
        self.rsi = RSI(period=period)
        self.oversold = oversold
        self.overbought = overbought
        self.size = size

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        rsi_val = self.rsi.calculate(bar.close_prices)
        if rsi_val is None:
            return self.hold()

        if rsi_val < self.oversold:
            return self.buy(size=self.size)
        elif rsi_val > self.overbought:
            return self.sell(size=self.size)
        return self.hold()
