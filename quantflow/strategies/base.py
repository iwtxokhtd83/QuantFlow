"""Base strategy class and signal model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from quantflow.core.models import Bar


class SignalType(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()


@dataclass
class Signal:
    type: SignalType
    size: Optional[float] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Optional[dict] = None


class Strategy(ABC):
    """Base class for all trading strategies."""

    def __init__(self, name: str = "BaseStrategy") -> None:
        self.name = name

    @abstractmethod
    def on_bar(self, bar: Bar, portfolio) -> Signal:
        """Process a new bar and return a trading signal."""

    def on_start(self) -> None:
        """Called when the engine starts."""

    def on_stop(self) -> None:
        """Called when the engine stops."""

    # Convenience signal builders
    def buy(self, size: float = 1, stop_loss: float = None, take_profit: float = None, **kw) -> Signal:
        return Signal(SignalType.BUY, size=size, stop_loss=stop_loss, take_profit=take_profit, metadata=kw or None)

    def sell(self, size: float = 1, stop_loss: float = None, take_profit: float = None, **kw) -> Signal:
        return Signal(SignalType.SELL, size=size, stop_loss=stop_loss, take_profit=take_profit, metadata=kw or None)

    def hold(self) -> Signal:
        return Signal(SignalType.HOLD)
