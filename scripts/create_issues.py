"""Create GitHub issues for QuantFlow bugs and feature requests."""

import os
import time
from github import Github

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    TOKEN = input("Enter your GitHub Personal Access Token: ").strip()

g = Github(TOKEN)
repo = g.get_repo("iwtxokhtd83/QuantFlow")

issues = [
    # ============ BUGS ============
    {
        "title": "[Bug] sharpe_ratio and sortino_ratio defined as @property but accept parameters",
        "body": """## Description

In `quantflow/analytics/performance.py`, `sharpe_ratio` and `sortino_ratio` are decorated with `@property` but their method signatures include parameters (`risk_free_rate`, `periods`):

```python
@property
def sharpe_ratio(self, risk_free_rate: float = 0.0, periods: int = 252) -> float:
```

Python `@property` does not support passing arguments. The `risk_free_rate` and `periods` parameters are silently ignored — they always use the default values, even if a caller tries to pass custom values.

## Expected Behavior

Users should be able to customize the risk-free rate and annualization period.

## Fix

Either:
1. Remove `@property` and make them regular methods: `result.sharpe_ratio(risk_free_rate=0.02)`
2. Or store `risk_free_rate` and `periods` as instance attributes set in `__init__`
""",
        "labels": ["bug"],
    },
    {
        "title": "[Bug] RiskManager uses cash instead of total equity for drawdown check",
        "body": """## Description

In `quantflow/risk/manager.py`, the drawdown check compares `capital` (which is `portfolio.cash`) against `equity_peak`:

```python
if capital < equity_peak * (1 - self.max_drawdown_pct):
```

But `equity_peak` tracks total equity (cash + positions). When a position is open, cash is reduced but equity may still be fine. This causes false drawdown triggers — the system halts trading even though the portfolio is healthy.

## Expected Behavior

Drawdown should be calculated from total equity (`cash + unrealized position value`), not just cash.

## Fix

Pass `portfolio.equity` instead of `portfolio.cash` to `risk_manager.check()`, or add an `equity` parameter to the `check()` method.
""",
        "labels": ["bug"],
    },
    {
        "title": "[Bug] Portfolio.equity uses entry_price instead of current market price",
        "body": """## Description

`Portfolio.equity` sums `position.market_value`, but `Position.market_value` is defined as:

```python
@property
def market_value(self) -> float:
    return self.quantity * self.entry_price
```

This returns the cost basis, not the current market value. The equity curve and equity peak are therefore inaccurate — they don't reflect unrealized gains/losses.

## Expected Behavior

`equity` should reflect the current market value of positions, not the entry cost.

## Fix

Either:
1. Update `Position` to track `current_price` and use it in `market_value`
2. Or change `Portfolio.equity` to accept `current_prices: dict[str, float]` and compute market value from current prices
""",
        "labels": ["bug"],
    },
    {
        "title": "[Bug] Short selling allows opening positions without cash collateral check",
        "body": """## Description

In `Portfolio.execute_signal()`, the cash sufficiency check only applies to BUY orders:

```python
if side == OrderSide.BUY and cost > self.cash:
    return None
```

SELL (short) orders bypass this check entirely. In real markets, short selling requires margin. Without any check, the system can open unlimited short positions.

## Expected Behavior

Short positions should require margin or at minimum a cash collateral check.

## Fix

Add a margin requirement check for short positions, e.g., require `current_price * quantity * margin_rate` in available cash.
""",
        "labels": ["bug"],
    },
    {
        "title": "[Bug] DataFeed.bars() creates a new numpy array copy on every bar",
        "body": """## Description

In `quantflow/data/feeds.py`, the `bars()` method appends to a Python list and creates a new `np.array()` on every iteration:

```python
closes.append(row["close"])
yield Bar(..., close_prices=np.array(closes, dtype=np.float64))
```

For a 10,000-bar backtest, this creates 10,000 numpy arrays of increasing size, resulting in O(n²) memory allocation and significant GC pressure.

## Expected Behavior

Efficient memory usage that doesn't degrade with dataset size.

## Fix

Pre-allocate a numpy array from the full DataFrame and pass slices:

```python
all_closes = df["close"].values.astype(np.float64)
for i, (_, row) in enumerate(df.iterrows()):
    yield Bar(..., close_prices=all_closes[:i+1])
```
""",
        "labels": ["bug", "performance"],
    },
    {
        "title": "[Bug] EMA.calculate() recomputes entire series for a single value",
        "body": """## Description

`EMA.calculate()` calls `self.series(prices)[-1]`, which computes the full EMA series just to return the last value. Since strategies call `calculate()` on every bar with a growing price array, this results in O(n²) total computation over a backtest.

## Expected Behavior

`calculate()` should be O(n) per call or maintain state for O(1) incremental updates.

## Fix

Either:
1. Cache the previous EMA value and compute incrementally
2. Or compute only the last value without building the full series
""",
        "labels": ["bug", "performance"],
    },
    {
        "title": "[Bug] Stochastic %D series alignment is incorrect",
        "body": """## Description

In `Stochastic.series()`, the %D line is computed by:
1. Filtering out NaN values from %K
2. Computing SMA on the filtered array
3. Mapping back to original indices

```python
d = SMA(self.d_period).series(k[~np.isnan(k)])
d_full[valid_idx[:len(d)]] = d
```

The SMA series will have leading NaN values, but the mapping `valid_idx[:len(d)]` doesn't account for this offset. The %D values end up misaligned with the %K values.

## Expected Behavior

%D should be a `d_period`-bar SMA of %K, properly aligned in time.
""",
        "labels": ["bug"],
    },
    {
        "title": "[Bug] MACD.calculate() may return NaN instead of None",
        "body": """## Description

`MACD.calculate()` checks `len(prices) < self.slow_period + self.signal_period` and returns `None` tuple if insufficient. But `MACD.series()` can produce NaN values in the signal line even when there's enough data. The `calculate()` method then returns `float(NaN)` instead of `None`.

Downstream strategies check `if hist is None` but don't check for NaN, leading to incorrect signal generation.

## Expected Behavior

`calculate()` should return `None` for any component that is NaN.

## Fix

Add NaN checks before returning:
```python
if np.isnan(macd_line[-1]) or np.isnan(signal_line[-1]):
    return None, None, None
```
""",
        "labels": ["bug"],
    },

    # ============ FEATURES ============
    {
        "title": "[Feature] Add unit test suite",
        "body": """## Description

The project currently has no tests. A comprehensive test suite is essential for an open-source project.

## Scope

- Unit tests for all 16 indicators (validate against known values)
- Unit tests for risk manager rules
- Unit tests for portfolio execution logic (commission, slippage, PnL)
- Integration tests for backtest engine (end-to-end)
- Test for edge cases: empty data, single bar, zero volume, zero price

## Implementation

Use `pytest` with fixtures for sample data. Add `tests/` directory with:
```
tests/
├── test_indicators.py
├── test_strategies.py
├── test_risk.py
├── test_portfolio.py
├── test_engine.py
└── conftest.py
```

Add to CI with GitHub Actions.
""",
        "labels": ["enhancement", "good first issue"],
    },
    {
        "title": "[Feature] Add GitHub Actions CI/CD pipeline",
        "body": """## Description

Set up automated testing and linting on every push and PR.

## Scope

- Run `pytest` on Python 3.10, 3.11, 3.12
- Run `flake8` or `ruff` for linting
- Run `mypy` for type checking
- Generate test coverage report
- Badge in README

## Implementation

Add `.github/workflows/ci.yml` with matrix strategy for Python versions.
""",
        "labels": ["enhancement", "infrastructure"],
    },
    {
        "title": "[Feature] Multi-asset portfolio engine",
        "body": """## Description

The current engine processes one symbol at a time. Many quant strategies require multi-asset support:
- Pairs trading
- Statistical arbitrage
- Portfolio rebalancing
- Cross-asset momentum

## Requirements

- Engine feeds multiple bar streams simultaneously (aligned by timestamp)
- Strategy receives a dict of bars per timestamp: `on_bars(bars: dict[str, Bar], portfolio)`
- Portfolio tracks positions across multiple symbols
- Risk manager enforces cross-asset exposure limits
- Correlation-aware position sizing

## Design Considerations

- Bars from different symbols may not align perfectly in time — need a synchronization mechanism
- Memory usage scales with number of symbols
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] Walk-forward optimization",
        "body": """## Description

Parameter optimization on historical data leads to overfitting. Walk-forward analysis is the standard solution:

1. Split data into N windows
2. For each window: optimize on in-sample, validate on out-of-sample
3. Aggregate out-of-sample results

## Requirements

- `WalkForwardOptimizer` class that accepts a strategy factory, parameter grid, and data
- Configurable in-sample / out-of-sample ratio
- Anchored and rolling window modes
- Output: per-window best parameters + aggregated out-of-sample performance
- Visualization of parameter stability across windows
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] Broker adapters for Binance and Interactive Brokers",
        "body": """## Description

The `PaperBroker` is useful for testing, but real trading requires exchange connectivity.

## Scope

### Binance Adapter
- REST API for account info, order placement, position queries
- WebSocket for real-time bar data (replace polling)
- Support for spot and futures
- Rate limit handling

### Interactive Brokers Adapter
- TWS API / IB Gateway connection
- Support for stocks, options, futures
- Real-time market data subscription
- Order management (market, limit, stop)

## Implementation

Each adapter implements the `Broker` interface. Add optional dependencies (e.g., `python-binance`, `ib_insync`) as extras in `setup.py`.
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] WebSocket real-time data feed",
        "body": """## Description

The current `LiveEngine` polls the broker for new bars using `time.sleep()`. This is inefficient and introduces latency.

## Requirements

- WebSocket-based data feed that pushes bars to the engine
- Support for Binance WebSocket streams
- Reconnection logic with exponential backoff
- Heartbeat / ping-pong handling
- Thread-safe bar queue between WebSocket receiver and engine loop
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] Strategy parameter optimization (grid search + Bayesian)",
        "body": """## Description

Add tools for systematic parameter optimization:

## Scope

### Grid Search
- Exhaustive search over parameter combinations
- Parallel execution with `multiprocessing`
- Results as DataFrame sortable by any metric

### Bayesian Optimization
- Use `scipy.optimize` or `optuna` for intelligent parameter search
- Objective function: Sharpe ratio, Sortino, or custom metric
- Early stopping for unpromising parameter regions

### Output
- Heatmap visualization for 2D parameter sweeps
- Parameter sensitivity analysis
- Overfitting detection (in-sample vs out-of-sample gap)
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] Trade log export (CSV, JSON) and HTML report generation",
        "body": """## Description

The current `print_summary()` outputs to console only. Users need exportable reports.

## Requirements

- `to_csv(path)` — export trades and equity curve to CSV
- `to_json(path)` — export full results as JSON
- `to_html(path)` — generate a standalone HTML report with:
  - Summary metrics table
  - Interactive equity curve chart (using embedded Chart.js or similar)
  - Trade log table with sorting/filtering
  - Monthly returns heatmap
  - Drawdown periods table
""",
        "labels": ["enhancement", "good first issue"],
    },
    {
        "title": "[Feature] Add limit and stop order support in backtest engine",
        "body": """## Description

The backtest engine currently only supports market orders (immediate fill at close price). Real trading uses limit orders, stop orders, and stop-limit orders.

## Requirements

- `OrderType.LIMIT` — fill only if price reaches limit level
- `OrderType.STOP` — trigger market order when stop price is hit
- `OrderType.STOP_LIMIT` — trigger limit order when stop price is hit
- Pending order queue in portfolio
- Order expiration (GTC, GTD, IOC)
- Partial fill simulation for limit orders
""",
        "labels": ["enhancement"],
    },
    {
        "title": "[Feature] Add transaction cost models (fixed, tiered, maker/taker)",
        "body": """## Description

The current commission model is a flat percentage. Real exchanges have more complex fee structures.

## Requirements

- Fixed fee per trade (e.g., $1 per trade)
- Tiered fee based on monthly volume
- Maker/taker fee differentiation
- Minimum commission
- Per-share fee model (e.g., $0.005/share)
- Pluggable `CostModel` interface
""",
        "labels": ["enhancement", "good first issue"],
    },
    {
        "title": "[Feature] Add logging and event hooks for strategy debugging",
        "body": """## Description

Debugging strategies is difficult without visibility into what's happening per bar.

## Requirements

- Structured logging with bar number, signal, portfolio state per bar
- Event hooks: `on_order_filled`, `on_trade_closed`, `on_risk_breach`
- Debug mode that logs every indicator value per bar
- Trade journal: human-readable log of why each trade was entered/exited
- Integration with the existing `EventBus` — subscribe to events for custom logging
""",
        "labels": ["enhancement"],
    },
]

print(f"Creating {len(issues)} issues on iwtxokhtd83/QuantFlow...\n")

for i, issue_data in enumerate(issues):
    try:
        labels = issue_data.get("labels", [])
        # Ensure labels exist
        existing_labels = [l.name for l in repo.get_labels()]
        for label in labels:
            if label not in existing_labels:
                colors = {
                    "bug": "d73a4a",
                    "enhancement": "a2eeef",
                    "good first issue": "7057ff",
                    "performance": "f9d0c4",
                    "infrastructure": "0075ca",
                }
                repo.create_label(label, colors.get(label, "ededed"))
                existing_labels.append(label)

        issue = repo.create_issue(
            title=issue_data["title"],
            body=issue_data["body"],
            labels=labels,
        )
        print(f"  [{i+1}/{len(issues)}] Created: #{issue.number} - {issue_data['title']}")
        time.sleep(1)  # rate limit
    except Exception as e:
        print(f"  [{i+1}/{len(issues)}] FAILED: {issue_data['title']} - {e}")

print("\nDone!")
