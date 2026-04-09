"""Tests for portfolio management."""

from __future__ import annotations

import pytest
from datetime import datetime

from quantflow.core.models import OrderSide, OrderStatus, Position
from quantflow.portfolio.manager import Portfolio
from quantflow.strategies.base import Signal, SignalType


class TestPortfolio:
    def setup_method(self):
        self.portfolio = Portfolio(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage_rate=0.0,  # zero slippage for predictable tests
        )
        self.ts = datetime(2024, 1, 1)

    def test_initial_state(self):
        assert self.portfolio.cash == 100000.0
        assert self.portfolio.equity == 100000.0
        assert self.portfolio.open_position_count == 0
        assert len(self.portfolio.trades) == 0

    def test_buy_reduces_cash(self):
        signal = Signal(SignalType.BUY, size=100)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        expected_cost = 100 * 100.0 + 100 * 100.0 * 0.001  # price + commission
        assert self.portfolio.cash == pytest.approx(100000.0 - expected_cost)

    def test_buy_creates_position(self):
        signal = Signal(SignalType.BUY, size=50)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert self.portfolio.has_position("TEST")
        assert self.portfolio.open_position_count == 1

    def test_sell_closes_long_position(self):
        buy = Signal(SignalType.BUY, size=50)
        self.portfolio.execute_signal(buy, "TEST", 100.0, self.ts)
        sell = Signal(SignalType.SELL, size=50)
        self.portfolio.execute_signal(sell, "TEST", 110.0, self.ts)
        assert not self.portfolio.has_position("TEST")
        assert len(self.portfolio.trades) == 1
        assert self.portfolio.trades[0].pnl > 0

    def test_hold_does_nothing(self):
        signal = Signal(SignalType.HOLD)
        result = self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert result is None
        assert self.portfolio.cash == 100000.0

    def test_insufficient_cash_rejects_buy(self):
        signal = Signal(SignalType.BUY, size=2000)  # 2000 * 100 = $200k > $100k
        result = self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert result is None
        assert self.portfolio.open_position_count == 0

    def test_short_margin_check(self):
        """Short selling should require margin collateral."""
        self.portfolio.short_margin_rate = 1.0
        signal = Signal(SignalType.SELL, size=2000)  # 2000 * 100 = $200k margin > $100k
        result = self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert result is None

    def test_short_within_margin_succeeds(self):
        self.portfolio.short_margin_rate = 1.0
        signal = Signal(SignalType.SELL, size=500)  # 500 * 100 = $50k margin < $100k
        result = self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert result is not None
        assert self.portfolio.has_position("TEST")

    def test_commission_applied(self):
        signal = Signal(SignalType.BUY, size=100)
        order = self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        assert order.commission > 0

    def test_stop_loss_triggers(self):
        signal = Signal(SignalType.BUY, size=100, stop_loss=95.0)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        result = self.portfolio.check_stops("TEST", 94.0, self.ts)
        assert result is not None
        assert not self.portfolio.has_position("TEST")

    def test_take_profit_triggers(self):
        signal = Signal(SignalType.BUY, size=100, take_profit=110.0)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        result = self.portfolio.check_stops("TEST", 111.0, self.ts)
        assert result is not None
        assert not self.portfolio.has_position("TEST")

    def test_stop_not_triggered_within_range(self):
        signal = Signal(SignalType.BUY, size=100, stop_loss=95.0, take_profit=110.0)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        result = self.portfolio.check_stops("TEST", 102.0, self.ts)
        assert result is None
        assert self.portfolio.has_position("TEST")

    def test_equity_reflects_current_price(self):
        """Equity should use current market price, not entry price."""
        signal = Signal(SignalType.BUY, size=100)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        self.portfolio.update_market_prices("TEST", 120.0)
        # Cash reduced by ~$10010, position now worth $12000
        assert self.portfolio.equity > self.portfolio.cash + 100 * 100.0

    def test_equity_curve_updated(self):
        self.portfolio.update_equity()
        assert len(self.portfolio.equity_curve) == 1
        assert self.portfolio.equity_curve[0] == 100000.0

    def test_equity_peak_tracks_high(self):
        signal = Signal(SignalType.BUY, size=100)
        self.portfolio.execute_signal(signal, "TEST", 100.0, self.ts)
        self.portfolio.update_market_prices("TEST", 150.0)
        self.portfolio.update_equity()
        peak = self.portfolio.equity_peak
        self.portfolio.update_market_prices("TEST", 120.0)
        self.portfolio.update_equity()
        assert self.portfolio.equity_peak == peak  # peak doesn't decrease


class TestPosition:
    def test_market_value_uses_current_price(self):
        pos = Position("TEST", OrderSide.BUY, 100, 100.0, datetime.now(), current_price=120.0)
        assert pos.market_value == pytest.approx(12000.0)

    def test_cost_basis(self):
        pos = Position("TEST", OrderSide.BUY, 100, 100.0, datetime.now(), current_price=120.0)
        assert pos.cost_basis == pytest.approx(10000.0)

    def test_unrealized_pnl_long(self):
        pos = Position("TEST", OrderSide.BUY, 100, 100.0, datetime.now(), current_price=110.0)
        assert pos.unrealized_pnl() == pytest.approx(1000.0)

    def test_unrealized_pnl_short(self):
        pos = Position("TEST", OrderSide.SELL, 100, 100.0, datetime.now(), current_price=90.0)
        assert pos.unrealized_pnl() == pytest.approx(1000.0)

    def test_default_current_price_equals_entry(self):
        pos = Position("TEST", OrderSide.BUY, 100, 100.0, datetime.now())
        assert pos.current_price == 100.0
