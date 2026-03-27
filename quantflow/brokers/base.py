"""Abstract broker interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Broker(ABC):
    """Base class for all broker adapters."""

    commission_rate: float = 0.001

    @abstractmethod
    def get_balance(self) -> float:
        """Get current account balance."""

    @abstractmethod
    def get_latest_bar(self, symbol: str, interval: str) -> Optional[dict]:
        """Get the latest OHLCV bar as a dict."""

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "market",
                    price: float = None) -> dict:
        """Place an order and return order info."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""

    @abstractmethod
    def get_positions(self) -> list[dict]:
        """Get all open positions."""
