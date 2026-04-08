"""Portfolio management — tracks positions, cash, and trade history."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from quantflow.core.models import Order, OrderSide, OrderStatus, OrderType, Position, Trade
from quantflow.strategies.base import Signal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class Portfolio:
    """Manages cash, positions, and trade execution."""

    initial_capital: float = 100000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    short_margin_rate: float = 1.0  # margin required for short positions (100% of value)

    cash: float = field(init=False)
    equity_peak: float = field(init=False)
    positions: dict[str, Position] = field(default_factory=dict, init=False)
    trades: list[Trade] = field(default_factory=list, init=False)
    orders: list[Order] = field(default_factory=list, init=False)
    equity_curve: list[float] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_capital
        self.equity_peak = self.initial_capital

    @property
    def equity(self) -> float:
        """Total equity = cash + market value of all positions (using current prices)."""
        pos_value = 0.0
        for p in self.positions.values():
            if p.side == OrderSide.BUY:
                pos_value += p.market_value
            else:
                # Short position: value = entry proceeds + unrealized PnL
                pos_value += p.cost_basis + p.unrealized_pnl()
        return self.cash + pos_value

    @property
    def open_position_count(self) -> int:
        return len(self.positions)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions

    def update_market_prices(self, symbol: str, current_price: float) -> None:
        """Update current market price for a position."""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price

    def execute_signal(self, signal: Signal, symbol: str, current_price: float, timestamp: datetime) -> Optional[Order]:
        """Convert a signal into an order and execute it."""
        if signal.type == SignalType.HOLD:
            return None

        side = OrderSide.BUY if signal.type == SignalType.BUY else OrderSide.SELL
        quantity = signal.size or 1

        # Apply slippage
        if side == OrderSide.BUY:
            fill_price = current_price * (1 + self.slippage_rate)
        else:
            fill_price = current_price * (1 - self.slippage_rate)

        commission = fill_price * quantity * self.commission_rate
        cost = fill_price * quantity + commission

        # Check if we're closing an existing position
        if symbol in self.positions:
            pos = self.positions[symbol]
            if (pos.side == OrderSide.BUY and side == OrderSide.SELL) or \
               (pos.side == OrderSide.SELL and side == OrderSide.BUY):
                return self._close_position(symbol, fill_price, timestamp, commission)

        # Cash check for opening new positions
        if side == OrderSide.BUY and cost > self.cash:
            logger.info("Insufficient cash for buy: need %.2f, have %.2f", cost, self.cash)
            return None

        if side == OrderSide.SELL:
            # Short selling requires margin collateral
            margin_required = fill_price * quantity * self.short_margin_rate + commission
            if margin_required > self.cash:
                logger.info("Insufficient margin for short: need %.2f, have %.2f", margin_required, self.cash)
                return None

        order = Order(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            status=OrderStatus.FILLED,
            filled_price=fill_price,
            filled_at=timestamp,
            commission=commission,
        )

        if side == OrderSide.BUY:
            self.cash -= cost
        else:
            self.cash += fill_price * quantity - commission

        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=fill_price,
            entry_time=timestamp,
            current_price=fill_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
        )

        self.orders.append(order)
        logger.debug("Opened %s %d %s @ %.2f", side.name, quantity, symbol, fill_price)
        return order

    def _close_position(self, symbol: str, exit_price: float, timestamp: datetime, commission: float) -> Order:
        pos = self.positions.pop(symbol)
        trade = Trade(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
            entry_time=pos.entry_time,
            exit_time=timestamp,
            commission=commission + pos.entry_price * pos.quantity * self.commission_rate,
        )
        self.trades.append(trade)

        if pos.side == OrderSide.BUY:
            self.cash += exit_price * pos.quantity - commission
        else:
            pnl = (pos.entry_price - exit_price) * pos.quantity - commission
            self.cash += pos.cost_basis + pnl

        order = Order(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=OrderSide.SELL if pos.side == OrderSide.BUY else OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=pos.quantity,
            status=OrderStatus.FILLED,
            filled_price=exit_price,
            filled_at=timestamp,
            commission=commission,
        )
        self.orders.append(order)
        logger.debug("Closed %s %s — PnL: %.2f", symbol, pos.side.name, trade.pnl)
        return order

    def check_stops(self, symbol: str, current_price: float, timestamp: datetime) -> Optional[Order]:
        """Check and trigger stop loss / take profit for a position."""
        if symbol not in self.positions:
            return None

        # Update current market price
        self.positions[symbol].current_price = current_price
        pos = self.positions[symbol]

        triggered = False
        if pos.side == OrderSide.BUY:
            if pos.stop_loss and current_price <= pos.stop_loss:
                triggered = True
            if pos.take_profit and current_price >= pos.take_profit:
                triggered = True
        else:
            if pos.stop_loss and current_price >= pos.stop_loss:
                triggered = True
            if pos.take_profit and current_price <= pos.take_profit:
                triggered = True

        if triggered:
            commission = current_price * pos.quantity * self.commission_rate
            return self._close_position(symbol, current_price, timestamp, commission)
        return None

    def update_equity(self) -> None:
        eq = self.equity
        self.equity_curve.append(eq)
        if eq > self.equity_peak:
            self.equity_peak = eq
