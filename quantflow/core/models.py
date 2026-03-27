"""Core data models for the trading system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

import numpy as np


class OrderSide(Enum):
    BUY = auto()
    SELL = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class OrderStatus(Enum):
    PENDING = auto()
    SUBMITTED = auto()
    FILLED = auto()
    PARTIALLY_FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()


@dataclass
class Bar:
    """Single OHLCV bar."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_prices: Optional[np.ndarray] = field(default=None, repr=False)

    @property
    def mid(self) -> float:
        return (self.high + self.low) / 2

    @property
    def spread(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open


@dataclass
class Order:
    """Trade order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    commission: float = 0.0


@dataclass
class Trade:
    """Completed round-trip trade."""
    id: str
    symbol: str
    side: OrderSide
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    commission: float = 0.0

    @property
    def pnl(self) -> float:
        if self.side == OrderSide.BUY:
            raw = (self.exit_price - self.entry_price) * self.quantity
        else:
            raw = (self.entry_price - self.exit_price) * self.quantity
        return raw - self.commission

    @property
    def pnl_pct(self) -> float:
        cost = self.entry_price * self.quantity
        return self.pnl / cost if cost != 0 else 0.0

    @property
    def duration(self):
        return self.exit_time - self.entry_time


@dataclass
class Position:
    """Open position tracker."""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @property
    def market_value(self) -> float:
        return self.quantity * self.entry_price

    def unrealized_pnl(self, current_price: float) -> float:
        if self.side == OrderSide.BUY:
            return (current_price - self.entry_price) * self.quantity
        return (self.entry_price - current_price) * self.quantity
