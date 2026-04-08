# Indicators

QuantFlow includes 16 technical indicators implemented in pure numpy. No external TA library required.

## Common Interface

Every indicator follows the same pattern:

```python
indicator = SMA(period=20)

# Single value (latest)
value = indicator.calculate(close_prices)  # float or None

# Full series
series = indicator.series(close_prices)    # np.ndarray
```

- `calculate()` returns `None` if there isn't enough data (warm-up period)
- `series()` returns an array with `NaN` for positions without enough data

## Trend Indicators

### SMA — Simple Moving Average

```python
from quantflow.indicators import SMA

sma = SMA(period=20)
value = sma.calculate(prices)       # latest SMA value
series = sma.series(prices)         # full SMA series
```

### EMA — Exponential Moving Average

```python
from quantflow.indicators import EMA

ema = EMA(period=20)
value = ema.calculate(prices)
```

Uses standard EMA formula: `alpha = 2 / (period + 1)`, seeded with SMA of the first `period` values.

### MACD — Moving Average Convergence Divergence

```python
from quantflow.indicators import MACD

macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd_line, signal_line, histogram = macd.calculate(prices)
```

Returns three values: MACD line, signal line, and histogram (MACD - signal).

### ADX — Average Directional Index

```python
from quantflow.indicators import ADX

adx = ADX(period=14)
value = adx.calculate(high, low, close)
series = adx.series(high, low, close)
```

Measures trend strength (0-100). Values above 25 indicate a strong trend.

## Momentum Indicators

### RSI — Relative Strength Index

```python
from quantflow.indicators import RSI

rsi = RSI(period=14)
value = rsi.calculate(prices)    # 0-100
```

Uses Wilder's smoothing method. Common thresholds: oversold < 30, overbought > 70.

### Stochastic Oscillator

```python
from quantflow.indicators import Stochastic

stoch = Stochastic(k_period=14, d_period=3)
k, d = stoch.calculate(high, low, close)
```

Returns %K (fast) and %D (slow) lines.

### Williams %R

```python
from quantflow.indicators import WilliamsR

wr = WilliamsR(period=14)
value = wr.calculate(high, low, close)    # -100 to 0
```

### CCI — Commodity Channel Index

```python
from quantflow.indicators import CCI

cci = CCI(period=20)
value = cci.calculate(high, low, close)
```

### ROC — Rate of Change

```python
from quantflow.indicators import ROC

roc = ROC(period=12)
value = roc.calculate(prices)    # percentage
```

### MFI — Money Flow Index

```python
from quantflow.indicators import MFI

mfi = MFI(period=14)
value = mfi.calculate(high, low, close, volume)    # 0-100
```

Volume-weighted RSI. Requires volume data.

## Volatility Indicators

### Bollinger Bands

```python
from quantflow.indicators import BollingerBands

bb = BollingerBands(period=20, num_std=2.0)
upper, middle, lower = bb.calculate(prices)
```

Returns upper band, middle band (SMA), and lower band.

### ATR — Average True Range

```python
from quantflow.indicators import ATR

atr = ATR(period=14)
value = atr.calculate(high, low, close)
```

Measures volatility. Useful for dynamic stop-loss placement.

## Volume Indicators

### VWAP — Volume Weighted Average Price

```python
from quantflow.indicators import VWAP

vwap = VWAP()
value = vwap.calculate(high, low, close, volume)
```

### OBV — On-Balance Volume

```python
from quantflow.indicators import OBV

obv = OBV()
series = obv.series(close, volume)
```

Cumulative volume indicator. Rising OBV confirms uptrend.

## Composite Indicators

### Ichimoku Cloud

```python
from quantflow.indicators import Ichimoku

ich = Ichimoku(tenkan_period=9, kijun_period=26, senkou_b_period=52)
result = ich.calculate(high, low)
# result = {"tenkan": ..., "kijun": ..., "senkou_a": ..., "senkou_b": ...}
```

Returns a dictionary with Tenkan-sen, Kijun-sen, Senkou Span A, and Senkou Span B.

## Adding a Custom Indicator

Follow the existing pattern:

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class MyIndicator:
    period: int = 20

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) < self.period:
            return None
        # your computation here
        return float(result)

    def series(self, prices: np.ndarray) -> np.ndarray:
        out = np.full(len(prices), np.nan)
        for i in range(self.period - 1, len(prices)):
            # your computation here
            out[i] = result
        return out
```
