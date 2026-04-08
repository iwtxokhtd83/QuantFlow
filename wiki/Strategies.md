# Strategies

## Strategy Interface

Every strategy extends the `Strategy` base class:

```python
from quantflow.strategies.base import Strategy, Signal

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")

    def on_bar(self, bar, portfolio) -> Signal:
        # Analyze bar, return BUY / SELL / HOLD
        return self.hold()
```

### Lifecycle Methods

| Method | When Called | Required |
|--------|-----------|----------|
| `on_bar(bar, portfolio)` | Every new price bar | Yes |
| `on_start()` | Engine starts | No |
| `on_stop()` | Engine stops | No |

### Signal Builders

The base class provides convenience methods:

```python
self.buy(size=100)                                    # market buy
self.buy(size=100, stop_loss=95, take_profit=115)     # with exits
self.sell(size=100)                                   # market sell
self.hold()                                           # no action
```

### Accessing Data

The `bar` object provides:

```python
bar.symbol          # str: ticker symbol
bar.timestamp       # datetime
bar.open            # float
bar.high            # float
bar.low             # float
bar.close           # float
bar.volume          # float
bar.close_prices    # np.ndarray: all close prices up to this bar
bar.is_bullish      # bool: close > open
bar.mid             # float: (high + low) / 2
bar.spread          # float: high - low
```

The `portfolio` object provides:

```python
portfolio.cash                  # float: available cash
portfolio.equity                # float: cash + position values
portfolio.has_position(symbol)  # bool
portfolio.open_position_count   # int
```

## Built-in Strategies

### SMACrossover

Classic trend-following strategy using two moving averages.

```python
from quantflow.strategies import SMACrossover

strategy = SMACrossover(fast_period=10, slow_period=30, size=100)
```

- Buys on golden cross (fast SMA crosses above slow SMA)
- Sells on death cross (fast SMA crosses below slow SMA)
- Requires crossover detection (not just relative position)

### RSIMeanReversion

Mean reversion strategy based on RSI extremes.

```python
from quantflow.strategies import RSIMeanReversion

strategy = RSIMeanReversion(period=14, oversold=30, overbought=70, size=100)
```

- Buys when RSI drops below `oversold` threshold
- Sells when RSI rises above `overbought` threshold
- Works best in range-bound markets

### MACDTrend

Trend strategy based on MACD histogram crossovers.

```python
from quantflow.strategies import MACDTrend

strategy = MACDTrend(fast=12, slow=26, signal=9, size=100)
```

- Buys when histogram crosses from negative to positive
- Sells when histogram crosses from positive to negative

### BollingerBreakout

Volatility breakout strategy using Bollinger Bands.

```python
from quantflow.strategies import BollingerBreakout

strategy = BollingerBreakout(period=20, num_std=2.0, size=100)
```

- Buys when price touches the lower band (with stop-loss at 2% below lower band)
- Sells when price touches the upper band (with stop-loss at 2% above upper band)
- Take-profit targets the middle band

## Writing a Custom Strategy

### Example: Dual Indicator Strategy

```python
from quantflow.strategies.base import Strategy, Signal
from quantflow.indicators import RSI, EMA, ATR

class TrendMomentum(Strategy):
    """Buy in uptrend when momentum is oversold."""

    def __init__(self, ema_period=50, rsi_period=14, atr_period=14):
        super().__init__(name="TrendMomentum")
        self.ema = EMA(period=ema_period)
        self.rsi = RSI(period=rsi_period)
        self.atr = ATR(period=atr_period)

    def on_bar(self, bar, portfolio):
        ema_val = self.ema.calculate(bar.close_prices)
        rsi_val = self.rsi.calculate(bar.close_prices)

        if ema_val is None or rsi_val is None:
            return self.hold()

        # Only buy in uptrend (price above EMA) when RSI is oversold
        if bar.close > ema_val and rsi_val < 35:
            return self.buy(
                size=100,
                stop_loss=bar.close * 0.97,
                take_profit=bar.close * 1.10,
            )

        # Exit when RSI is overbought
        if rsi_val > 75 and portfolio.has_position(bar.symbol):
            return self.sell(size=100)

        return self.hold()
```

### Tips for Strategy Development

1. Always handle the warm-up period — check for `None` from indicators
2. Use `portfolio.has_position()` to avoid duplicate entries
3. Set stop-loss and take-profit in the signal, or let the risk manager apply defaults
4. Keep strategies stateless where possible — store only what's needed for signal generation
5. Test on synthetic data first, then on real historical data
