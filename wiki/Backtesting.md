# Backtesting

## Basic Usage

```python
from quantflow.data import CSVDataFeed
from quantflow.engine import BacktestEngine
from quantflow.strategies import SMACrossover

data = CSVDataFeed("data/sample_ohlcv.csv")
strategy = SMACrossover(fast_period=10, slow_period=30)

engine = BacktestEngine(
    data_feed=data,
    strategy=strategy,
    initial_capital=100000,
    commission=0.001,       # 0.1% per trade
    slippage=0.0005,        # 0.05% slippage
    symbol="AAPL",
)

result = engine.run()
result.print_summary()
```

## Engine Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_feed` | DataFeed | required | Data source |
| `strategy` | Strategy | required | Trading strategy |
| `initial_capital` | float | 100,000 | Starting cash |
| `commission` | float | 0.001 | Commission rate (0.1%) |
| `slippage` | float | 0.0005 | Slippage rate (0.05%) |
| `symbol` | str | "UNKNOWN" | Ticker symbol |
| `risk_manager` | RiskManager | default | Risk management config |

## Execution Model

### Commission

Applied as a percentage of trade value:

```
commission = fill_price × quantity × commission_rate
```

### Slippage

Proportional adverse price movement on fill:

```
BUY:  fill_price = market_price × (1 + slippage_rate)
SELL: fill_price = market_price × (1 - slippage_rate)
```

This models the reality that market orders typically fill at slightly worse prices than the last traded price.

### Order of Operations (per bar)

1. Check stop-loss / take-profit on existing positions
2. Strategy generates signal
3. Risk manager validates signal
4. Portfolio executes order
5. Equity curve updated

## Multi-Strategy Comparison

```python
strategies = [
    SMACrossover(fast_period=10, slow_period=30),
    RSIMeanReversion(period=14, oversold=30, overbought=70),
    MACDTrend(fast=12, slow=26, signal=9),
    BollingerBreakout(period=20, num_std=2.0),
]

for strategy in strategies:
    data = CSVDataFeed("data/sample_ohlcv.csv")  # fresh instance per run
    engine = BacktestEngine(data_feed=data, strategy=strategy, initial_capital=100000)
    result = engine.run()
    print(f"{strategy.name}: {result.total_return:.2%} return, {result.sharpe_ratio:.2f} Sharpe")
```

Important: create a new `DataFeed` instance for each run to avoid state leakage.

## Parameter Sweep

```python
results = []
for fast in [5, 10, 15, 20]:
    for slow in [20, 30, 40, 50]:
        if fast >= slow:
            continue
        data = CSVDataFeed("data/sample_ohlcv.csv")
        strategy = SMACrossover(fast_period=fast, slow_period=slow)
        engine = BacktestEngine(data_feed=data, strategy=strategy, initial_capital=100000)
        result = engine.run()
        results.append({
            "fast": fast, "slow": slow,
            "return": result.total_return,
            "sharpe": result.sharpe_ratio,
            "trades": result.num_trades,
        })

# Sort by Sharpe ratio
results.sort(key=lambda x: x["sharpe"], reverse=True)
for r in results[:5]:
    print(f"SMA({r['fast']},{r['slow']}): {r['return']:.2%} return, {r['sharpe']:.2f} Sharpe, {r['trades']} trades")
```

Warning: parameter optimization on historical data can lead to overfitting. Use walk-forward analysis or out-of-sample testing to validate.

## Interpreting Results

See [Performance Analytics](Performance-Analytics) for detailed metric explanations.

Key things to look for:
- **Sharpe > 1.0** — decent risk-adjusted return
- **Max drawdown < 20%** — manageable risk
- **Win rate vs. profit factor** — a low win rate is fine if winners are much larger than losers
- **Number of trades** — too few trades means the result may not be statistically significant
