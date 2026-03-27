"""Bollinger Bands Breakout Strategy — trade on band touches."""

from __future__ import annotations

from quantflow.core.models import Bar
from quantflow.indicators import BollingerBands
from quantflow.strategies.base import Strategy, Signal


class BollingerBreakout(Strategy):
    """Buy when price touches lower band, sell when it touches upper band."""

    def __init__(self, period: int = 20, num_std: float = 2.0, size: float = 100) -> None:
        super().__init__(name="BollingerBreakout")
        self.bb = BollingerBands(period=period, num_std=num_std)
        self.size = size

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        upper, mid, lower = self.bb.calculate(bar.close_prices)
        if upper is None:
            return self.hold()

        if bar.close <= lower:
            return self.buy(size=self.size, stop_loss=lower * 0.98, take_profit=mid)
        elif bar.close >= upper:
            return self.sell(size=self.size, stop_loss=upper * 1.02, take_profit=mid)
        return self.hold()
