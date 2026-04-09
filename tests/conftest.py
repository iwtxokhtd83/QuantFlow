"""Shared fixtures for QuantFlow tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from quantflow.core.models import Bar, OrderSide, Position, Trade


@pytest.fixture
def sample_prices() -> np.ndarray:
    """50 bars of synthetic close prices with slight upward drift."""
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 50)
    prices = 100.0 * np.cumprod(1 + returns)
    return prices


@pytest.fixture
def sample_ohlcv() -> dict[str, np.ndarray]:
    """50 bars of synthetic OHLCV data."""
    np.random.seed(42)
    n = 50
    close = 100.0 * np.cumprod(1 + np.random.normal(0.001, 0.02, n))
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = close * (1 + np.random.normal(0, 0.003, n))
    volume = np.random.randint(100000, 1000000, n).astype(float)
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume}


@pytest.fixture
def sample_bar(sample_prices) -> Bar:
    """A single Bar with full price history."""
    return Bar(
        symbol="TEST",
        timestamp=datetime(2024, 1, 1),
        open=sample_prices[-2],
        high=max(sample_prices[-2:]),
        low=min(sample_prices[-2:]),
        close=sample_prices[-1],
        volume=500000.0,
        close_prices=sample_prices,
    )


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Small OHLCV DataFrame for data feed tests."""
    np.random.seed(42)
    n = 30
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = 100.0 * np.cumprod(1 + np.random.normal(0.001, 0.015, n))
    df = pd.DataFrame({
        "open": close * (1 + np.random.normal(0, 0.003, n)),
        "high": close * (1 + np.abs(np.random.normal(0, 0.005, n))),
        "low": close * (1 - np.abs(np.random.normal(0, 0.005, n))),
        "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    }, index=dates)
    df.index.name = "date"
    return df
