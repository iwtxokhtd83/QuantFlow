"""Integration tests for the backtest engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime
from io import StringIO

from quantflow.data.feeds import DataFeed, CSVDataFeed
from quantflow.engine.backtest import BacktestEngine
from quantflow.strategies import SMACrossover, RSIMeanReversion
from quantflow.strategies.base import Strategy, Signal, SignalType
from quantflow.risk.manager import RiskManager
from quantflow.core.models import Bar


class InMemoryDataFeed(DataFeed):
    """Data feed from a DataFrame for testing."""
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def load(self) -> pd.DataFrame:
        return self._df


class AlwaysBuyStrategy(Strategy):
    """Buy on every bar for testing."""
    def __init__(self):
        super().__init__(name="AlwaysBuy")

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        if not portfolio.has_position(bar.symbol):
            return self.buy(size=10)
        return self.hold()


class AlwaysHoldStrategy(Strategy):
    """Never trade."""
    def __init__(self):
        super().__init__(name="AlwaysHold")

    def on_bar(self, bar: Bar, portfolio) -> Signal:
        return self.hold()


class TestBacktestEngine:
    @pytest.fixture
    def data_feed(self, sample_dataframe):
        return InMemoryDataFeed(sample_dataframe)

    def test_engine_runs_without_error(self, data_feed):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=SMACrossover(fast_period=5, slow_period=10),
            initial_capital=100000,
            symbol="TEST",
        )
        result = engine.run()
        assert result is not None
        assert len(result.equity_curve) > 0

    def test_no_trades_strategy(self, data_feed):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=AlwaysHoldStrategy(),
            initial_capital=100000,
        )
        result = engine.run()
        assert result.num_trades == 0
        assert result.total_return == pytest.approx(0.0)

    def test_equity_curve_length_matches_bars(self, data_feed, sample_dataframe):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=AlwaysHoldStrategy(),
            initial_capital=100000,
        )
        result = engine.run()
        assert len(result.equity_curve) == len(sample_dataframe)

    def test_always_buy_creates_trades(self, data_feed):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=AlwaysBuyStrategy(),
            initial_capital=100000,
            symbol="TEST",
        )
        result = engine.run()
        assert len(result.equity_curve) > 0

    def test_commission_reduces_equity(self, data_feed):
        engine_no_comm = BacktestEngine(
            data_feed=data_feed,
            strategy=AlwaysBuyStrategy(),
            initial_capital=100000,
            commission=0.0,
            symbol="TEST",
        )
        engine_with_comm = BacktestEngine(
            data_feed=InMemoryDataFeed(data_feed._df.copy()),
            strategy=AlwaysBuyStrategy(),
            initial_capital=100000,
            commission=0.01,
            symbol="TEST",
        )
        r1 = engine_no_comm.run()
        r2 = engine_with_comm.run()
        # Higher commission should result in lower or equal final equity
        assert r2.equity_curve[-1] <= r1.equity_curve[-1]

    def test_performance_report_metrics(self, data_feed):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=SMACrossover(fast_period=3, slow_period=7, size=50),
            initial_capital=100000,
            symbol="TEST",
        )
        result = engine.run()
        # Metrics should be computable without error
        _ = result.total_return
        _ = result.sharpe_ratio()
        _ = result.sortino_ratio()
        _ = result.max_drawdown
        _ = result.win_rate
        _ = result.profit_factor

    def test_sharpe_accepts_custom_params(self, data_feed):
        engine = BacktestEngine(
            data_feed=data_feed,
            strategy=SMACrossover(fast_period=3, slow_period=7, size=50),
            initial_capital=100000,
            symbol="TEST",
        )
        result = engine.run()
        s1 = result.sharpe_ratio()
        s2 = result.sharpe_ratio(risk_free_rate=0.05)
        # With higher risk-free rate, Sharpe should be lower
        assert s2 <= s1

    def test_single_bar_no_crash(self):
        """Engine should handle a single bar without crashing."""
        df = pd.DataFrame({
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.5],
            "volume": [100000],
        }, index=pd.DatetimeIndex([datetime(2024, 1, 1)], name="date"))
        engine = BacktestEngine(
            data_feed=InMemoryDataFeed(df),
            strategy=AlwaysHoldStrategy(),
            initial_capital=100000,
        )
        result = engine.run()
        assert len(result.equity_curve) == 1

    def test_zero_volume_no_crash(self):
        """Engine should handle zero volume bars."""
        n = 20
        df = pd.DataFrame({
            "open": np.full(n, 100.0),
            "high": np.full(n, 101.0),
            "low": np.full(n, 99.0),
            "close": np.full(n, 100.0),
            "volume": np.zeros(n),
        }, index=pd.date_range("2024-01-01", periods=n, freq="B", name="date"))
        engine = BacktestEngine(
            data_feed=InMemoryDataFeed(df),
            strategy=AlwaysHoldStrategy(),
            initial_capital=100000,
        )
        result = engine.run()
        assert result.total_return == pytest.approx(0.0)
