"""Technical indicators library — pure numpy implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Trend Indicators
# ---------------------------------------------------------------------------

@dataclass
class SMA:
    """Simple Moving Average."""
    period: int = 20

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) < self.period:
            return None
        return float(np.mean(prices[-self.period:]))

    def series(self, prices: np.ndarray) -> np.ndarray:
        out = np.full(len(prices), np.nan)
        for i in range(self.period - 1, len(prices)):
            out[i] = np.mean(prices[i - self.period + 1: i + 1])
        return out


@dataclass
class EMA:
    """Exponential Moving Average."""
    period: int = 20

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) < self.period:
            return None
        return float(self.series(prices)[-1])

    def series(self, prices: np.ndarray) -> np.ndarray:
        alpha = 2.0 / (self.period + 1)
        out = np.full(len(prices), np.nan)
        out[self.period - 1] = np.mean(prices[:self.period])
        for i in range(self.period, len(prices)):
            out[i] = alpha * prices[i] + (1 - alpha) * out[i - 1]
        return out


@dataclass
class MACD:
    """Moving Average Convergence Divergence."""
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

    def calculate(self, prices: np.ndarray) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(prices) < self.slow_period + self.signal_period:
            return None, None, None
        macd_line, signal_line, histogram = self.series(prices)
        return float(macd_line[-1]), float(signal_line[-1]), float(histogram[-1])

    def series(self, prices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        fast_ema = EMA(self.fast_period).series(prices)
        slow_ema = EMA(self.slow_period).series(prices)
        macd_line = fast_ema - slow_ema
        valid = ~np.isnan(macd_line)
        signal_line = np.full(len(prices), np.nan)
        valid_macd = macd_line[valid]
        if len(valid_macd) >= self.signal_period:
            sig = EMA(self.signal_period).series(valid_macd)
            signal_line[valid] = sig
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram



@dataclass
class ADX:
    """Average Directional Index."""
    period: int = 14

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Optional[float]:
        if len(high) < self.period * 2:
            return None
        return float(self.series(high, low, close)[-1])

    def series(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        n = len(high)
        tr = np.zeros(n)
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        for i in range(1, n):
            h_diff = high[i] - high[i - 1]
            l_diff = low[i - 1] - low[i]
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
            plus_dm[i] = h_diff if h_diff > l_diff and h_diff > 0 else 0
            minus_dm[i] = l_diff if l_diff > h_diff and l_diff > 0 else 0

        atr = self._smooth(tr, self.period)
        plus_di = 100 * self._smooth(plus_dm, self.period) / np.where(atr == 0, 1, atr)
        minus_di = 100 * self._smooth(minus_dm, self.period) / np.where(atr == 0, 1, atr)
        dx = 100 * np.abs(plus_di - minus_di) / np.where(plus_di + minus_di == 0, 1, plus_di + minus_di)
        adx = self._smooth(dx, self.period)
        return adx

    @staticmethod
    def _smooth(data: np.ndarray, period: int) -> np.ndarray:
        out = np.full(len(data), np.nan)
        out[period] = np.sum(data[1:period + 1])
        for i in range(period + 1, len(data)):
            out[i] = out[i - 1] - out[i - 1] / period + data[i]
        return out


# ---------------------------------------------------------------------------
# Momentum Indicators
# ---------------------------------------------------------------------------

@dataclass
class RSI:
    """Relative Strength Index."""
    period: int = 14

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) < self.period + 1:
            return None
        return float(self.series(prices)[-1])

    def series(self, prices: np.ndarray) -> np.ndarray:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        out = np.full(len(prices), np.nan)
        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])
        if avg_loss == 0:
            out[self.period] = 100.0
        else:
            out[self.period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        for i in range(self.period, len(deltas)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period
            if avg_loss == 0:
                out[i + 1] = 100.0
            else:
                out[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        return out


@dataclass
class Stochastic:
    """Stochastic Oscillator (%K and %D)."""
    k_period: int = 14
    d_period: int = 3

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> tuple[Optional[float], Optional[float]]:
        if len(close) < self.k_period:
            return None, None
        k, d = self.series(high, low, close)
        return float(k[-1]) if not np.isnan(k[-1]) else None, float(d[-1]) if not np.isnan(d[-1]) else None

    def series(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = len(close)
        k = np.full(n, np.nan)
        for i in range(self.k_period - 1, n):
            hh = np.max(high[i - self.k_period + 1: i + 1])
            ll = np.min(low[i - self.k_period + 1: i + 1])
            k[i] = 100 * (close[i] - ll) / (hh - ll) if hh != ll else 50.0
        d = SMA(self.d_period).series(k[~np.isnan(k)])
        d_full = np.full(n, np.nan)
        valid_idx = np.where(~np.isnan(k))[0]
        d_full[valid_idx[:len(d)]] = d
        return k, d_full


@dataclass
class WilliamsR:
    """Williams %R."""
    period: int = 14

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Optional[float]:
        if len(close) < self.period:
            return None
        hh = np.max(high[-self.period:])
        ll = np.min(low[-self.period:])
        if hh == ll:
            return -50.0
        return float(-100 * (hh - close[-1]) / (hh - ll))


@dataclass
class CCI:
    """Commodity Channel Index."""
    period: int = 20

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Optional[float]:
        if len(close) < self.period:
            return None
        tp = (high + low + close) / 3
        tp_slice = tp[-self.period:]
        mean_tp = np.mean(tp_slice)
        mean_dev = np.mean(np.abs(tp_slice - mean_tp))
        if mean_dev == 0:
            return 0.0
        return float((tp[-1] - mean_tp) / (0.015 * mean_dev))


@dataclass
class ROC:
    """Rate of Change."""
    period: int = 12

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) <= self.period:
            return None
        prev = prices[-self.period - 1]
        if prev == 0:
            return 0.0
        return float((prices[-1] - prev) / prev * 100)


@dataclass
class MFI:
    """Money Flow Index."""
    period: int = 14

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> Optional[float]:
        if len(close) < self.period + 1:
            return None
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = 0.0
        neg_mf = 0.0
        for i in range(-self.period, 0):
            if tp[i] > tp[i - 1]:
                pos_mf += mf[i]
            else:
                neg_mf += mf[i]
        if neg_mf == 0:
            return 100.0
        ratio = pos_mf / neg_mf
        return float(100 - 100 / (1 + ratio))



# ---------------------------------------------------------------------------
# Volatility Indicators
# ---------------------------------------------------------------------------

@dataclass
class BollingerBands:
    """Bollinger Bands."""
    period: int = 20
    num_std: float = 2.0

    def calculate(self, prices: np.ndarray) -> tuple[Optional[float], Optional[float], Optional[float]]:
        if len(prices) < self.period:
            return None, None, None
        mid = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:], ddof=0)
        return float(mid + self.num_std * std), float(mid), float(mid - self.num_std * std)

    def series(self, prices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        mid = SMA(self.period).series(prices)
        upper = np.full(len(prices), np.nan)
        lower = np.full(len(prices), np.nan)
        for i in range(self.period - 1, len(prices)):
            std = np.std(prices[i - self.period + 1: i + 1], ddof=0)
            upper[i] = mid[i] + self.num_std * std
            lower[i] = mid[i] - self.num_std * std
        return upper, mid, lower


@dataclass
class ATR:
    """Average True Range."""
    period: int = 14

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Optional[float]:
        if len(high) < self.period + 1:
            return None
        return float(self.series(high, low, close)[-1])

    def series(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        n = len(high)
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        atr = np.full(n, np.nan)
        atr[self.period] = np.mean(tr[1:self.period + 1])
        for i in range(self.period + 1, n):
            atr[i] = (atr[i - 1] * (self.period - 1) + tr[i]) / self.period
        return atr


# ---------------------------------------------------------------------------
# Volume Indicators
# ---------------------------------------------------------------------------

@dataclass
class VWAP:
    """Volume Weighted Average Price."""

    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> Optional[float]:
        if len(close) == 0:
            return None
        tp = (high + low + close) / 3
        total_vol = np.sum(volume)
        if total_vol == 0:
            return float(tp[-1])
        return float(np.sum(tp * volume) / total_vol)


@dataclass
class OBV:
    """On-Balance Volume."""

    def series(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        obv = np.zeros(len(close))
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif close[i] < close[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        return obv


# ---------------------------------------------------------------------------
# Composite Indicators
# ---------------------------------------------------------------------------

@dataclass
class Ichimoku:
    """Ichimoku Cloud."""
    tenkan_period: int = 9
    kijun_period: int = 26
    senkou_b_period: int = 52

    def calculate(self, high: np.ndarray, low: np.ndarray) -> dict[str, Optional[float]]:
        result = {"tenkan": None, "kijun": None, "senkou_a": None, "senkou_b": None}
        if len(high) >= self.tenkan_period:
            result["tenkan"] = float((np.max(high[-self.tenkan_period:]) + np.min(low[-self.tenkan_period:])) / 2)
        if len(high) >= self.kijun_period:
            result["kijun"] = float((np.max(high[-self.kijun_period:]) + np.min(low[-self.kijun_period:])) / 2)
        if result["tenkan"] is not None and result["kijun"] is not None:
            result["senkou_a"] = (result["tenkan"] + result["kijun"]) / 2
        if len(high) >= self.senkou_b_period:
            result["senkou_b"] = float((np.max(high[-self.senkou_b_period:]) + np.min(low[-self.senkou_b_period:])) / 2)
        return result