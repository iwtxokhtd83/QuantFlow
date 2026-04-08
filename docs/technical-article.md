# Building QuantFlow: An Event-Driven Quantitative Trading Framework in Python

Quantitative trading systems sit at the intersection of finance, statistics, and software engineering. Most retail traders either pay for expensive platforms or cobble together scripts that become unmaintainable after a few hundred lines. QuantFlow is an open-source attempt to provide a clean, modular foundation that scales from a weekend experiment to a serious research pipeline.

This article walks through the architecture decisions, core abstractions, and trade-offs behind QuantFlow.

## The Problem with Most Backtesting Code

The typical quant's first backtest looks something like this: a single Python script, a for-loop over price data, a few if-statements, and a running PnL counter. It works. Then you want to add commission modeling. Then slippage. Then risk limits. Then you want to compare three strategies. Then you want to run the same strategy live.

At that point, the single script is 800 lines of spaghetti, and every change risks breaking something else.

QuantFlow's goal is to prevent that trajectory by providing the right abstractions from the start — without the overhead of enterprise frameworks that require a PhD in configuration to get a simple moving average crossover running.

## Architecture Overview

The system is organized into seven loosely-coupled modules:

```
quantflow/
├── core/           Event bus, data models, enums
├── data/           Data feed abstraction and implementations
├── indicators/     Technical indicators (pure numpy)
├── strategies/     Strategy base class and built-in strategies
├── engine/         Backtest and live trading engines
├── brokers/        Broker adapters (paper trading, extensible)
├── risk/           Risk management layer
├── portfolio/      Position tracking and order execution
└── analytics/      Performance metrics and visualization
```

The key design principle: each module depends only on `core` and the modules above it in the dependency chain. The strategy doesn't know about the engine. The engine doesn't know about specific strategies. The risk manager doesn't know about specific indicators.

## The Event Bus

At the center of the architecture is a lightweight publish-subscribe event bus:

```python
class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error("Event handler error for %s: %s", event.type, e)
```

This is intentionally simple. No async, no priority queues, no middleware chains. The event types are explicit:

```python
class EventType(Enum):
    BAR = auto()
    ORDER_SUBMITTED = auto()
    ORDER_FILLED = auto()
    ORDER_CANCELLED = auto()
    TRADE_OPENED = auto()
    TRADE_CLOSED = auto()
    RISK_BREACH = auto()
    ENGINE_START = auto()
    ENGINE_STOP = auto()
```

Why an event bus instead of direct method calls? Two reasons. First, it allows components to react to system events without the engine needing to know about them — you can attach a logging handler, a metrics collector, or a notification system without modifying the engine code. Second, it makes the transition from backtesting to live trading transparent: the same events fire in both modes.

## Data Models: Getting the Basics Right

The `Bar` dataclass carries a rolling window of close prices alongside the standard OHLCV fields:

```python
@dataclass
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_prices: Optional[np.ndarray] = field(default=None, repr=False)
```

The `close_prices` field is a numpy array that grows with each bar. This is a deliberate trade-off: it uses more memory than a fixed-size window, but it means indicators can look back as far as they need without the strategy managing its own price history. For a typical backtest over a few thousand bars, the memory overhead is negligible.

The `Trade` model computes PnL including commissions, and tracks both long and short sides:

```python
@property
def pnl(self) -> float:
    if self.side == OrderSide.BUY:
        raw = (self.exit_price - self.entry_price) * self.quantity
    else:
        raw = (self.entry_price - self.exit_price) * self.quantity
    return raw - self.commission
```

## Indicators: Pure Numpy, No Dependencies

All 16 indicators are implemented as pure numpy computations with no external TA library dependency. Each indicator follows the same pattern:

- `calculate(prices) -> Optional[float]` — returns the latest value, or `None` if insufficient data
- `series(prices) -> np.ndarray` — returns the full indicator series for vectorized analysis

For example, the RSI implementation uses Wilder's smoothing method:

```python
@dataclass
class RSI:
    period: int = 14

    def calculate(self, prices: np.ndarray) -> Optional[float]:
        if len(prices) < self.period + 1:
            return None
        return float(self.series(prices)[-1])

    def series(self, prices: np.ndarray) -> np.ndarray:
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        # ... Wilder's smoothing
```

The `None` return on insufficient data is important — it forces strategies to handle the warm-up period explicitly rather than computing on garbage data. This is a common source of bugs in backtests: indicators returning values before they have enough history, leading to phantom signals in the first few bars.

The indicator library covers trend (SMA, EMA, MACD, ADX), momentum (RSI, Stochastic, Williams %R, CCI, ROC, MFI), volatility (Bollinger Bands, ATR), volume (VWAP, OBV), and composite (Ichimoku) categories.

## The Strategy Abstraction

Strategies extend a base class with a single required method:

```python
class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: Bar, portfolio) -> Signal:
        """Process a new bar and return a trading signal."""
```

The return type is a `Signal` dataclass:

```python
@dataclass
class Signal:
    type: SignalType        # BUY, SELL, or HOLD
    size: Optional[float]   # number of shares/units
    price: Optional[float]  # limit price (None = market)
    stop_loss: Optional[float]
    take_profit: Optional[float]
    metadata: Optional[dict]
```

This design means a strategy is a pure function from `(bar, portfolio_state) -> signal`. It doesn't execute orders, manage positions, or track equity. That separation is critical — it means the same strategy object works identically in backtesting and live trading, and it's trivially testable.

The base class provides convenience builders:

```python
def buy(self, size=1, stop_loss=None, take_profit=None, **kw) -> Signal:
    return Signal(SignalType.BUY, size=size, stop_loss=stop_loss,
                  take_profit=take_profit, metadata=kw or None)
```

A complete strategy implementation is typically 20-30 lines. Here's the SMA Crossover:

```python
class SMACrossover(Strategy):
    def __init__(self, fast_period=10, slow_period=30, size=100):
        super().__init__(name="SMACrossover")
        self.fast_sma = SMA(period=fast_period)
        self.slow_sma = SMA(period=slow_period)
        self.size = size
        self._prev_fast = None
        self._prev_slow = None

    def on_bar(self, bar, portfolio):
        fast = self.fast_sma.calculate(bar.close_prices)
        slow = self.slow_sma.calculate(bar.close_prices)
        if fast is None or slow is None:
            return self.hold()

        signal = self.hold()
        if self._prev_fast is not None and self._prev_slow is not None:
            if self._prev_fast <= self._prev_slow and fast > slow:
                signal = self.buy(size=self.size)
            elif self._prev_fast >= self._prev_slow and fast < slow:
                signal = self.sell(size=self.size)

        self._prev_fast, self._prev_slow = fast, slow
        return signal
```

## Risk Management: The Layer Most Frameworks Skip

The `RiskManager` sits between the strategy and the portfolio, intercepting every signal before execution:

```
Strategy → Signal → RiskManager.check() → Modified Signal → Portfolio.execute()
```

It enforces four rules:

1. **Drawdown circuit breaker** — if equity drops below `equity_peak * (1 - max_drawdown_pct)`, all trading halts. This is a hard stop, not a suggestion. Once halted, the manager stays halted for the remainder of the session.

2. **Position count limit** — caps the number of concurrent open positions. This prevents strategies from pyramiding into correlated positions during trending markets.

3. **Position sizing** — caps any single position to `max_position_pct` of current capital. If a strategy requests 1000 shares but that exceeds 10% of capital, the size is reduced.

4. **Default stop-loss and take-profit** — if the strategy doesn't specify exit levels, the risk manager applies configurable defaults.

```python
def check(self, signal, current_price, capital, equity_peak, open_position_count):
    if signal.type == SignalType.HOLD:
        return signal

    # Drawdown check
    if capital < equity_peak * (1 - self.max_drawdown_pct):
        if not self._halted:
            logger.warning("Max drawdown breached. Trading halted.")
            self._halted = True
        return Signal(SignalType.HOLD)

    # Position sizing
    max_value = capital * self.max_position_pct
    if signal.size and signal.size * current_price > max_value:
        signal.size = int(max_value / current_price)
    ...
```

The risk manager is stateful (it tracks the `_halted` flag), but its interface is a pure function: signal in, signal out. This makes it easy to test in isolation.

## The Backtest Engine

The engine orchestrates the simulation loop:

```python
def run(self) -> PerformanceReport:
    portfolio = Portfolio(initial_capital=self.initial_capital, ...)

    for bar in self.data_feed.bars(symbol=self.symbol):
        event_bus.publish(Event(EventType.BAR, data=bar))

        # 1. Check stops on existing positions
        portfolio.check_stops(bar.symbol, bar.close, bar.timestamp)

        # 2. Get strategy signal
        signal = self.strategy.on_bar(bar, portfolio)

        # 3. Risk check
        signal = self.risk_manager.check(signal, bar.close, ...)

        # 4. Execute
        portfolio.execute_signal(signal, bar.symbol, bar.close, bar.timestamp)
        portfolio.update_equity()

    return PerformanceReport(trades=portfolio.trades, equity_curve=portfolio.equity_curve, ...)
```

The order matters: stops are checked before the strategy runs, so the strategy sees the portfolio state after any stop-triggered exits. This prevents the strategy from making decisions based on positions that have already been closed.

The execution model includes both commission and slippage:

```python
# Slippage model: adverse price movement on fill
if side == OrderSide.BUY:
    fill_price = current_price * (1 + self.slippage_rate)
else:
    fill_price = current_price * (1 - self.slippage_rate)

commission = fill_price * quantity * self.commission_rate
```

This is a proportional slippage model — simple but effective for liquid markets. For illiquid instruments, you'd want to extend this with a volume-dependent impact model.

## Portfolio Management

The `Portfolio` class handles the mechanics of position tracking and order execution. It maintains:

- Cash balance
- Open positions (keyed by symbol)
- Completed trades (round-trip)
- Order history
- Equity curve (sampled per bar)

Position closing is handled automatically when a signal opposes an existing position:

```python
def execute_signal(self, signal, symbol, current_price, timestamp):
    # If we have a long position and get a SELL signal, close it
    if symbol in self.positions:
        pos = self.positions[symbol]
        if (pos.side == OrderSide.BUY and side == OrderSide.SELL) or \
           (pos.side == OrderSide.SELL and side == OrderSide.BUY):
            return self._close_position(symbol, fill_price, timestamp, commission)
    # Otherwise, open a new position
    ...
```

The `check_stops` method evaluates stop-loss and take-profit levels on every bar:

```python
def check_stops(self, symbol, current_price, timestamp):
    pos = self.positions[symbol]
    if pos.side == OrderSide.BUY:
        if pos.stop_loss and current_price <= pos.stop_loss:
            triggered = True
        if pos.take_profit and current_price >= pos.take_profit:
            triggered = True
    ...
```

## Performance Analytics

The `PerformanceReport` computes standard quant metrics from the equity curve and trade list:

| Metric | Implementation |
|--------|---------------|
| Total Return | `(final_equity - initial) / initial` |
| Sharpe Ratio | `mean(excess_returns) / std(excess_returns) * sqrt(252)` |
| Sortino Ratio | Same as Sharpe but using downside deviation only |
| Max Drawdown | `min((equity - peak) / peak)` over the curve |
| Profit Factor | `gross_profit / gross_loss` |
| Win Rate | `winning_trades / total_trades` |

The `plot()` method generates a two-panel chart: equity curve on top, drawdown on bottom. This is the standard visualization in quant research — the equity curve shows the growth trajectory, while the drawdown chart reveals the pain points.

## Multi-Strategy Comparison

One of the most useful features for research is the ability to compare strategies on identical data:

```python
strategies = [
    SMACrossover(fast_period=10, slow_period=30),
    RSIMeanReversion(period=14, oversold=30, overbought=70),
    MACDTrend(fast=12, slow=26, signal=9),
    BollingerBreakout(period=20, num_std=2.0),
]

for strategy in strategies:
    data = CSVDataFeed("data/sample_ohlcv.csv")
    engine = BacktestEngine(data_feed=data, strategy=strategy, ...)
    result = engine.run()
```

Because each strategy is a self-contained object and the data feed is re-instantiated per run, there's no state leakage between comparisons.

## From Backtest to Live: The Same Strategy, Different Engine

The `LiveEngine` uses the same strategy interface but replaces the historical data loop with a real-time polling loop:

```python
def start(self):
    while self._running:
        bar_data = self.broker.get_latest_bar(self.symbol, self.interval)
        # ... construct Bar, run strategy, check risk, execute
        time.sleep(interval_seconds)
```

The `Broker` abstraction provides the interface:

```python
class Broker(ABC):
    def get_balance(self) -> float: ...
    def get_latest_bar(self, symbol, interval) -> Optional[dict]: ...
    def place_order(self, symbol, side, quantity, ...) -> dict: ...
    def get_positions(self) -> list[dict]: ...
```

The `PaperBroker` implements this with simulated execution for testing. Adding a real broker (Binance, Interactive Brokers) means implementing these five methods — the engine and strategy code doesn't change.

## Design Trade-offs and Limitations

A few conscious trade-offs worth noting:

**Single-asset focus.** The current engine processes one symbol at a time. Multi-asset portfolio strategies (pairs trading, statistical arbitrage) would need an engine that feeds multiple bar streams simultaneously. This is the most significant limitation for advanced use cases.

**Synchronous execution.** The event bus and engine loop are synchronous. For backtesting this is fine (and simpler to debug). For live trading with multiple symbols or high-frequency strategies, you'd want async I/O.

**Proportional slippage.** The slippage model is a fixed percentage. Real slippage depends on order size relative to available liquidity, time of day, and market microstructure. A more realistic model would use historical order book data.

**No partial fills.** Orders are either fully filled or rejected. In reality, large orders may be partially filled across multiple price levels.

## What's Next

The roadmap includes:

- Multi-asset portfolio engine with cross-asset signal aggregation
- Walk-forward optimization for parameter tuning without overfitting
- Broker adapters for Binance and Interactive Brokers
- WebSocket-based real-time data feeds
- Strategy parameter optimization with grid search and Bayesian methods
- Docker-based deployment for running strategies on cloud infrastructure

## Getting Started

```bash
git clone https://github.com/iwtxokhtd83/QuantFlow.git
cd QuantFlow
pip install -r requirements.txt
python data/generate_sample.py
python examples/backtest_multi_strategy.py
```

The multi-strategy comparison will run four strategies on synthetic data and print a comparison table. From there, writing a custom strategy is a matter of extending the `Strategy` base class and implementing `on_bar()`.

QuantFlow is MIT-licensed and open to contributions. The codebase is intentionally small (~1500 lines of core code) to stay readable and hackable.

---

*QuantFlow is available at [github.com/iwtxokhtd83/QuantFlow](https://github.com/iwtxokhtd83/QuantFlow). Contributions, issues, and feedback are welcome.*
