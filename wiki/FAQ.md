# FAQ

## General

### What Python version is required?

Python 3.10 or higher. The codebase uses `match` statements, type union syntax (`X | Y`), and other 3.10+ features.

### What are the dependencies?

- `numpy` — numerical computation
- `pandas` — data manipulation
- `matplotlib` — charting
- `pyyaml` — configuration
- `requests` — HTTP for Yahoo Finance data
- `websocket-client` — WebSocket support for future real-time feeds

No external TA library is required. All indicators are implemented in pure numpy.

### Is this suitable for production trading?

QuantFlow is designed for research and education. While it includes a live trading engine, you should thoroughly test any strategy with paper trading before risking real capital. The authors are not responsible for financial losses.

## Backtesting

### Why is my strategy's win rate low but total return high?

This is normal for trend-following strategies. They lose on many small trades during choppy markets but capture large moves during trends. Look at the profit factor (gross profit / gross loss) — if it's above 1.0, the strategy is profitable despite a low win rate.

### How do I avoid overfitting?

- Don't optimize on the full dataset. Split into in-sample (training) and out-of-sample (testing) periods.
- Use fewer parameters. Simpler strategies generalize better.
- Be suspicious of Sharpe ratios above 3.0 — they often indicate overfitting.
- Test on multiple symbols and time periods.

### Why does the same strategy give different results on different runs?

It shouldn't — backtests are deterministic. If you're seeing different results, check that:
- You're creating a fresh `DataFeed` instance for each run
- No global state is leaking between runs
- The data file hasn't changed

### How do I backtest on real market data?

Use `YahooDataFeed`:

```python
from quantflow.data import YahooDataFeed

data = YahooDataFeed(symbol="AAPL", start="2020-01-01", end="2025-01-01")
```

Or download data from any source, save as CSV with columns `date,open,high,low,close,volume`, and use `CSVDataFeed`.

### Can I backtest on multiple symbols simultaneously?

Not in the current version. The engine processes one symbol at a time. For multi-symbol strategies, run separate backtests and aggregate results, or contribute a multi-asset engine.

## Strategies

### How do I handle the indicator warm-up period?

All indicators return `None` when they don't have enough data. Always check:

```python
def on_bar(self, bar, portfolio):
    sma = self.sma.calculate(bar.close_prices)
    if sma is None:
        return self.hold()
    # ... rest of logic
```

### Can I use multiple timeframes?

Not directly. The engine feeds one timeframe. To use multiple timeframes, pre-compute higher timeframe indicators in your data pipeline and include them as additional columns, or maintain internal resampling logic in your strategy.

### How do I access previous bars?

The `bar.close_prices` array contains all close prices up to the current bar. For full OHLCV history, maintain your own buffer in the strategy:

```python
class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        self.bars = []

    def on_bar(self, bar, portfolio):
        self.bars.append(bar)
        # now self.bars[-5:] gives the last 5 bars
```

## Risk Management

### What happens when the drawdown limit is hit?

All trading halts for the remainder of the session. The risk manager converts every signal to HOLD. This is a safety mechanism to prevent catastrophic losses.

### Can I disable risk management?

Yes, by setting permissive limits:

```python
risk = RiskManager(max_position_pct=1.0, max_drawdown_pct=1.0, max_open_positions=999)
```

### Are stops guaranteed to fill at the stop price?

In backtesting, stops fill at the bar's close price when triggered, not at the exact stop level. In real markets, stops can experience slippage, especially during gaps.

## Live Trading

### How do I connect to a real broker?

Implement the `Broker` interface (5 methods). See [Live Trading](Live-Trading) for a Binance example.

### Is there a built-in Binance or Interactive Brokers adapter?

Not yet. These are on the roadmap. The `PaperBroker` is included for testing.

### How do I stop the live engine?

Press `Ctrl+C`, or call `engine.stop()` from another thread.

## Contributing

### How do I add a new indicator?

1. Add the class to `quantflow/indicators/technical.py`
2. Implement `calculate()` and optionally `series()`
3. Add to `quantflow/indicators/__init__.py` exports

### How do I add a new strategy?

1. Create a new file in `quantflow/strategies/`
2. Extend `Strategy`, implement `on_bar()`
3. Add to `quantflow/strategies/__init__.py`
4. Add an example in `examples/`

### How do I run tests?

```bash
python -m pytest tests/ -v
```
