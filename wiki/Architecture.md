# Architecture

## Design Principles

1. **Loose coupling** — modules communicate through events and interfaces, not direct references
2. **Strategy as pure function** — `(bar, portfolio_state) → signal`, no side effects
3. **Risk as middleware** — sits between strategy and execution, intercepting every signal
4. **Engine-agnostic strategies** — same strategy code runs in backtest and live modes
5. **Zero external TA dependencies** — all indicators are pure numpy

## Module Dependency Graph

```
core (events, models)
 ├── data (feeds)
 ├── indicators (technical)
 ├── strategies (base + implementations)
 ├── risk (manager)
 ├── portfolio (manager)
 ├── brokers (base + paper)
 ├── analytics (performance)
 └── engine (backtest, live)
```

Every module depends on `core`. The engine depends on everything else. No circular dependencies.

## Event Bus

The `EventBus` is a synchronous publish-subscribe system:

```python
event_bus = EventBus()
event_bus.subscribe(EventType.BAR, my_handler)
event_bus.publish(Event(EventType.BAR, data=bar))
```

Event types:

| Event | When |
|-------|------|
| `BAR` | New price bar received |
| `ORDER_SUBMITTED` | Order sent to broker |
| `ORDER_FILLED` | Order executed |
| `ORDER_CANCELLED` | Order cancelled |
| `TRADE_OPENED` | New position opened |
| `TRADE_CLOSED` | Position closed (round-trip complete) |
| `RISK_BREACH` | Risk limit triggered |
| `ENGINE_START` | Engine begins processing |
| `ENGINE_STOP` | Engine finishes processing |

The event bus enables extensibility — attach logging, metrics, notifications, or custom handlers without modifying engine code.

## Data Flow

The backtest engine processes data in this order per bar:

```
1. DataFeed yields Bar
2. EventBus publishes BAR event
3. Portfolio checks stop-loss / take-profit on open positions
4. Strategy.on_bar() produces a Signal
5. RiskManager.check() validates/modifies the Signal
6. Portfolio.execute_signal() fills the order
7. Portfolio.update_equity() records equity curve point
```

The ordering is intentional: stops are checked before the strategy runs, so the strategy sees the portfolio state after any stop-triggered exits.

## Core Data Models

### Bar
OHLCV price bar with a rolling `close_prices` numpy array for indicator computation.

### Signal
Strategy output: `BUY`, `SELL`, or `HOLD` with optional size, price, stop-loss, and take-profit.

### Order
Execution record with fill price, commission, and status tracking.

### Trade
Completed round-trip (entry + exit) with PnL computation including commissions.

### Position
Open position tracker with entry price, stop-loss, and take-profit levels.

See [API Reference](API-Reference) for full class documentation.
