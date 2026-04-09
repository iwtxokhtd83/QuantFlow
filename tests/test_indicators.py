"""Tests for technical indicators."""

from __future__ import annotations

import numpy as np
import pytest

from quantflow.indicators import (
    SMA, EMA, RSI, MACD, BollingerBands, ATR, Stochastic,
    VWAP, OBV, WilliamsR, CCI, ROC, MFI, ADX, Ichimoku,
)


class TestSMA:
    def test_insufficient_data_returns_none(self):
        sma = SMA(period=20)
        assert sma.calculate(np.array([1.0, 2.0, 3.0])) is None

    def test_known_value(self):
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sma = SMA(period=5)
        assert sma.calculate(prices) == pytest.approx(3.0)

    def test_uses_last_n_prices(self):
        prices = np.array([10.0, 1.0, 2.0, 3.0])
        sma = SMA(period=3)
        assert sma.calculate(prices) == pytest.approx(2.0)

    def test_series_length_matches_input(self, sample_prices):
        sma = SMA(period=10)
        result = sma.series(sample_prices)
        assert len(result) == len(sample_prices)
        assert np.isnan(result[0])
        assert not np.isnan(result[9])

    def test_series_values_match_calculate(self, sample_prices):
        sma = SMA(period=10)
        series = sma.series(sample_prices)
        for i in range(10, len(sample_prices)):
            expected = sma.calculate(sample_prices[:i + 1])
            assert series[i] == pytest.approx(expected, rel=1e-10)


class TestEMA:
    def test_insufficient_data_returns_none(self):
        ema = EMA(period=20)
        assert ema.calculate(np.array([1.0, 2.0])) is None

    def test_single_period_equals_price(self):
        ema = EMA(period=1)
        assert ema.calculate(np.array([42.0])) == pytest.approx(42.0)

    def test_known_value(self):
        prices = np.arange(1.0, 11.0)
        ema = EMA(period=5)
        val = ema.calculate(prices)
        assert val is not None
        assert isinstance(val, float)

    def test_calculate_matches_series_last(self, sample_prices):
        ema = EMA(period=12)
        calc_val = ema.calculate(sample_prices)
        series_val = ema.series(sample_prices)[-1]
        assert calc_val == pytest.approx(series_val, rel=1e-10)


class TestRSI:
    def test_insufficient_data(self):
        rsi = RSI(period=14)
        assert rsi.calculate(np.array([1.0] * 10)) is None

    def test_all_gains_returns_100(self):
        prices = np.arange(1.0, 20.0)
        rsi = RSI(period=14)
        val = rsi.calculate(prices)
        assert val == pytest.approx(100.0)

    def test_all_losses_returns_0(self):
        prices = np.arange(20.0, 1.0, -1.0)
        rsi = RSI(period=14)
        val = rsi.calculate(prices)
        assert val == pytest.approx(0.0, abs=0.01)

    def test_range_0_to_100(self, sample_prices):
        rsi = RSI(period=14)
        val = rsi.calculate(sample_prices)
        assert val is not None
        assert 0.0 <= val <= 100.0

    def test_series_no_nan_after_warmup(self, sample_prices):
        rsi = RSI(period=14)
        series = rsi.series(sample_prices)
        assert all(np.isnan(series[:14]))
        assert not any(np.isnan(series[15:]))


class TestMACD:
    def test_insufficient_data(self):
        macd = MACD()
        prices = np.arange(1.0, 30.0)
        m, s, h = macd.calculate(prices)
        assert m is None and s is None and h is None

    def test_returns_three_floats(self, sample_prices):
        macd = MACD(fast_period=5, slow_period=10, signal_period=3)
        m, s, h = macd.calculate(sample_prices)
        assert all(isinstance(v, float) for v in (m, s, h))

    def test_histogram_equals_macd_minus_signal(self, sample_prices):
        macd = MACD(fast_period=5, slow_period=10, signal_period=3)
        m, s, h = macd.calculate(sample_prices)
        assert h == pytest.approx(m - s, abs=1e-10)

    def test_no_nan_leakage(self):
        """MACD should return None, not NaN, for edge cases."""
        prices = np.arange(1.0, 40.0)
        macd = MACD()
        m, s, h = macd.calculate(prices)
        if m is not None:
            assert not np.isnan(m)
            assert not np.isnan(s)
            assert not np.isnan(h)


class TestBollingerBands:
    def test_insufficient_data(self):
        bb = BollingerBands(period=20)
        u, m, l = bb.calculate(np.array([1.0] * 5))
        assert u is None and m is None and l is None

    def test_constant_prices(self):
        prices = np.full(20, 100.0)
        bb = BollingerBands(period=20, num_std=2.0)
        u, m, l = bb.calculate(prices)
        assert m == pytest.approx(100.0)
        assert u == pytest.approx(100.0)
        assert l == pytest.approx(100.0)

    def test_upper_above_lower(self, sample_prices):
        bb = BollingerBands(period=20)
        u, m, l = bb.calculate(sample_prices)
        assert u > m > l


class TestATR:
    def test_insufficient_data(self, sample_ohlcv):
        atr = ATR(period=50)
        assert atr.calculate(sample_ohlcv["high"][:10], sample_ohlcv["low"][:10], sample_ohlcv["close"][:10]) is None

    def test_positive_value(self, sample_ohlcv):
        atr = ATR(period=14)
        val = atr.calculate(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"])
        assert val is not None
        assert val > 0


class TestStochastic:
    def test_insufficient_data(self):
        stoch = Stochastic(k_period=14)
        k, d = stoch.calculate(np.ones(5), np.ones(5), np.ones(5))
        assert k is None and d is None

    def test_range_0_to_100(self, sample_ohlcv):
        stoch = Stochastic(k_period=14, d_period=3)
        k, d = stoch.calculate(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"])
        assert k is not None
        assert 0.0 <= k <= 100.0

    def test_d_alignment(self, sample_ohlcv):
        """D line should start d_period-1 bars after K starts."""
        stoch = Stochastic(k_period=5, d_period=3)
        k_series, d_series = stoch.series(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"])
        first_k = np.where(~np.isnan(k_series))[0][0]
        first_d = np.where(~np.isnan(d_series))[0][0]
        assert first_d == first_k + stoch.d_period - 1


class TestWilliamsR:
    def test_range(self, sample_ohlcv):
        wr = WilliamsR(period=14)
        val = wr.calculate(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"])
        assert val is not None
        assert -100.0 <= val <= 0.0


class TestCCI:
    def test_insufficient_data(self):
        cci = CCI(period=20)
        assert cci.calculate(np.ones(5), np.ones(5), np.ones(5)) is None

    def test_constant_prices_returns_zero(self):
        n = 25
        prices = np.full(n, 100.0)
        cci = CCI(period=20)
        assert cci.calculate(prices, prices, prices) == pytest.approx(0.0)


class TestROC:
    def test_insufficient_data(self):
        roc = ROC(period=12)
        assert roc.calculate(np.array([1.0] * 12)) is None

    def test_known_value(self):
        prices = np.array([100.0] * 13)
        prices[-1] = 110.0
        roc = ROC(period=12)
        assert roc.calculate(prices) == pytest.approx(10.0)


class TestMFI:
    def test_insufficient_data(self):
        mfi = MFI(period=14)
        assert mfi.calculate(np.ones(10), np.ones(10), np.ones(10), np.ones(10)) is None

    def test_range_0_to_100(self, sample_ohlcv):
        mfi = MFI(period=14)
        val = mfi.calculate(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"], sample_ohlcv["volume"])
        assert val is not None
        assert 0.0 <= val <= 100.0


class TestADX:
    def test_insufficient_data(self):
        adx = ADX(period=14)
        assert adx.calculate(np.ones(10), np.ones(10), np.ones(10)) is None

    def test_returns_float(self, sample_ohlcv):
        adx = ADX(period=14)
        val = adx.calculate(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"])
        assert val is not None
        assert isinstance(val, float)


class TestVWAP:
    def test_empty_returns_none(self):
        vwap = VWAP()
        assert vwap.calculate(np.array([]), np.array([]), np.array([]), np.array([])) is None

    def test_known_value(self):
        h = np.array([102.0, 104.0])
        l = np.array([98.0, 96.0])
        c = np.array([100.0, 100.0])
        v = np.array([1000.0, 1000.0])
        vwap = VWAP()
        val = vwap.calculate(h, l, c, v)
        expected = ((102 + 98 + 100) / 3 * 1000 + (104 + 96 + 100) / 3 * 1000) / 2000
        assert val == pytest.approx(expected)


class TestOBV:
    def test_known_series(self):
        close = np.array([10.0, 11.0, 10.5, 11.5])
        volume = np.array([100.0, 200.0, 150.0, 300.0])
        obv = OBV()
        result = obv.series(close, volume)
        assert result[0] == 0
        assert result[1] == 200       # up
        assert result[2] == 50        # down
        assert result[3] == 350       # up


class TestIchimoku:
    def test_insufficient_data(self):
        ich = Ichimoku()
        result = ich.calculate(np.ones(5), np.ones(5))
        assert result["tenkan"] is None

    def test_known_tenkan(self):
        high = np.array([10.0, 12.0, 11.0, 13.0, 9.0, 14.0, 10.0, 11.0, 15.0])
        low = np.array([8.0, 9.0, 7.0, 10.0, 6.0, 11.0, 8.0, 9.0, 12.0])
        ich = Ichimoku(tenkan_period=9)
        result = ich.calculate(high, low)
        expected = (15.0 + 6.0) / 2
        assert result["tenkan"] == pytest.approx(expected)
