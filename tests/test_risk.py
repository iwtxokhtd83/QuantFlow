"""Tests for risk management."""

from __future__ import annotations

import pytest

from quantflow.risk.manager import RiskManager
from quantflow.strategies.base import Signal, SignalType


class TestRiskManager:
    def setup_method(self):
        self.rm = RiskManager(
            max_position_pct=0.10,
            max_drawdown_pct=0.20,
            max_open_positions=5,
            stop_loss_pct=0.05,
            take_profit_pct=0.15,
        )

    def test_hold_passes_through(self):
        signal = Signal(SignalType.HOLD)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 0)
        assert result.type == SignalType.HOLD

    def test_drawdown_halts_trading(self):
        signal = Signal(SignalType.BUY, size=10)
        # equity=75000 vs peak=100000 → 25% drawdown > 20% limit
        result = self.rm.check(signal, 100.0, 75000.0, 100000.0, 0)
        assert result.type == SignalType.HOLD

    def test_drawdown_halt_is_sticky(self):
        signal = Signal(SignalType.BUY, size=10)
        self.rm.check(signal, 100.0, 75000.0, 100000.0, 0)
        # Even if equity recovers, still halted
        result = self.rm.check(Signal(SignalType.BUY, size=10), 100.0, 95000.0, 100000.0, 0)
        assert result.type == SignalType.HOLD

    def test_drawdown_reset(self):
        self.rm.check(Signal(SignalType.BUY, size=10), 100.0, 75000.0, 100000.0, 0)
        self.rm.reset()
        result = self.rm.check(Signal(SignalType.BUY, size=10), 100.0, 95000.0, 100000.0, 0)
        assert result.type == SignalType.BUY

    def test_max_positions_blocks_buy(self):
        signal = Signal(SignalType.BUY, size=10)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 5)
        assert result.type == SignalType.HOLD

    def test_max_positions_allows_sell(self):
        signal = Signal(SignalType.SELL, size=10)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 5)
        assert result.type == SignalType.SELL

    def test_position_sizing_caps_size(self):
        # equity=100000, max_pct=10% → max $10000 → at $100/share → max 100 shares
        signal = Signal(SignalType.BUY, size=500)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 0)
        assert result.size <= 100

    def test_position_sizing_zero_becomes_hold(self):
        # equity=1000, max_pct=10% → max $100 → at $200/share → 0 shares
        signal = Signal(SignalType.BUY, size=10)
        result = self.rm.check(signal, 200.0, 1000.0, 1000.0, 0)
        assert result.type == SignalType.HOLD

    def test_default_stop_loss_applied(self):
        signal = Signal(SignalType.BUY, size=10)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 0)
        assert result.stop_loss == pytest.approx(95.0)
        assert result.take_profit == pytest.approx(115.0)

    def test_default_stop_loss_sell(self):
        signal = Signal(SignalType.SELL, size=10)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 0)
        assert result.stop_loss == pytest.approx(105.0)
        assert result.take_profit == pytest.approx(85.0)

    def test_existing_stop_loss_not_overwritten(self):
        signal = Signal(SignalType.BUY, size=10, stop_loss=90.0, take_profit=120.0)
        result = self.rm.check(signal, 100.0, 100000.0, 100000.0, 0)
        assert result.stop_loss == pytest.approx(90.0)
        assert result.take_profit == pytest.approx(120.0)

    def test_drawdown_uses_equity_not_cash(self):
        """Drawdown should be based on total equity, not just cash."""
        signal = Signal(SignalType.BUY, size=10)
        # equity=85000 vs peak=100000 → 15% drawdown < 20% limit → should pass
        result = self.rm.check(signal, 100.0, 85000.0, 100000.0, 0)
        assert result.type == SignalType.BUY
