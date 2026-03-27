"""Paper trading broker — simulated execution for testing."""

from __future__ import annotations

import logging
import random
import uuid
from typing import Optional

from quantflow.brokers.base import Broker

logger = logging.getLogger(__name__)


class PaperBroker(Broker):
    """Simulated broker for paper trading and strategy testing."""

    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001) -> None:
        self._balance = initial_capital
        self.commission_rate = commission_rate
        self._positions: list[dict] = []
        self._orders: list[dict] = []
        self._last_prices: dict[str, dict] = {}

    def get_balance(self) -> float:
        return self._balance

    def get_latest_bar(self, symbol: str, interval: str) -> Optional[dict]:
        """Simulate a price bar (for testing). Override for real data."""
        if symbol not in self._last_prices:
            self._last_prices[symbol] = {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10000}

        last = self._last_prices[symbol]
        change = random.uniform(-0.02, 0.02)
        new_close = last["close"] * (1 + change)
        bar = {
            "open": last["close"],
            "high": max(last["close"], new_close) * (1 + random.uniform(0, 0.005)),
            "low": min(last["close"], new_close) * (1 - random.uniform(0, 0.005)),
            "close": new_close,
            "volume": random.randint(5000, 50000),
        }
        self._last_prices[symbol] = bar
        return bar

    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "market",
                    price: float = None) -> dict:
        fill_price = price or self._last_prices.get(symbol, {}).get("close", 100)
        commission = fill_price * quantity * self.commission_rate

        order = {
            "id": str(uuid.uuid4())[:8],
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "fill_price": fill_price,
            "commission": commission,
            "status": "filled",
        }

        if side == "buy":
            self._balance -= fill_price * quantity + commission
            self._positions.append({"symbol": symbol, "side": side, "quantity": quantity, "entry_price": fill_price})
        else:
            self._balance += fill_price * quantity - commission
            self._positions = [p for p in self._positions if not (p["symbol"] == symbol and p["side"] == "buy")]

        self._orders.append(order)
        logger.info("Paper order: %s %s %.0f %s @ %.2f", order["id"], side, quantity, symbol, fill_price)
        return order

    def cancel_order(self, order_id: str) -> bool:
        for o in self._orders:
            if o["id"] == order_id and o["status"] == "pending":
                o["status"] = "cancelled"
                return True
        return False

    def get_positions(self) -> list[dict]:
        return self._positions.copy()
