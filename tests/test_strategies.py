"""Tests for built-in strategies."""

from __future__ import annotations

import numpy as np
import pytest
from datetime import datetime

from quantflow.core.models import Bar
from quantflow.portfolio.manager import Portfolio
from quantflow.strategies import SMACrossover, RSIMeanReversion, MACDTrend, BollingerBreakout
from quantflow.strategies.base import SignalType


def make_bar(close: float, close_prices: np.ndarray, symbol: str = "TEST") -> Bar:
    return Bar(
        symbol=symbol,
        timestamp=datetime(2024, 1, 1),
        open=close,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=100000.0,
        close_prices=close_prices,
    )


class TestSMACrossover:
    def test_hold_during_warmup(self):
        strategy = SMACrossover(fast_period=5, slow_period=10)
        portfolio = Portfolio()
        prices = np.array([100.0, 101.0, 102.0])
        bar = make_bar(102.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.HOLD

    def test_generates_buy_on_golden_cross(self):
        strategy = SMACrossover(fast_period=3, slow_period=5, size=100)
        portfolio = Portfolio()
        # Downtrend then sharp upturn → golden cross
        prices_down = np.linspace(120, 100, 20)
        prices_up = np.linspace(100, 130, 10)
        prices = np.concatenate([prices_down, prices_up])
        signals = []
        for i in range(len(prices)):
            bar = make_bar(prices[i], prices[:i + 1])
            signals.append(strategy.on_bar(bar, portfolio))
        buy_signals = [s for s in signals if s.type == SignalType.BUY]
        assert len(buy_signals) > 0


class TestRSIMeanReversion:
    def test_hold_during_warmup(self):
        strategy = RSIMeanReversion(period=14)
        portfolio = Portfolio()
        prices = np.array([100.0] * 10)
        bar = make_bar(100.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.HOLD

    def test_buy_on_oversold(self):
        strategy = RSIMeanReversion(period=14, oversold=30, size=100)
        portfolio = Portfolio()
        # Strong downtrend → RSI should be very low
        prices = np.linspace(200, 100, 50)
        bar = make_bar(100.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.BUY

    def test_sell_on_overbought(self):
        strategy = RSIMeanReversion(period=14, overbought=70, size=100)
        portfolio = Portfolio()
        # Strong uptrend → RSI should be very high
        prices = np.linspace(50, 200, 50)
        bar = make_bar(200.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.SELL


class TestMACDTrend:
    def test_hold_during_warmup(self):
        strategy = MACDTrend(fast=5, slow=10, signal=3)
        portfolio = Portfolio()
        prices = np.array([100.0] * 10)
        bar = make_bar(100.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.HOLD


class TestBollingerBreakout:
    def test_hold_during_warmup(self):
        strategy = BollingerBreakout(period=20)
        portfolio = Portfolio()
        prices = np.array([100.0] * 10)
        bar = make_bar(100.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.HOLD

    def test_buy_at_lower_band(self):
        strategy = BollingerBreakout(period=20, num_std=2.0, size=100)
        portfolio = Portfolio()
        # Stable prices then sharp drop → price at lower band
        prices = np.concatenate([np.full(25, 100.0), np.array([85.0])])
        bar = make_bar(85.0, prices)
        signal = strategy.on_bar(bar, portfolio)
        assert signal.type == SignalType.BUY
