# Risk Management

The `RiskManager` sits between the strategy and the portfolio, intercepting every signal before execution.

```
Strategy → Signal → RiskManager.check() → Modified Signal → Portfolio.execute()
```

## Configuration

```python
from quantflow.risk import RiskManager

risk = RiskManager(
    max_position_pct=0.10,      # max 10% of capital per position
    max_drawdown_pct=0.20,      # halt trading at 20% drawdown
    max_open_positions=10,      # max concurrent positions
    stop_loss_pct=0.05,         # default 5% stop loss
    take_profit_pct=0.15,       # default 15% take profit
)
```

Or via YAML config:

```yaml
risk:
  max_position_pct: 0.1
  max_drawdown_pct: 0.2
  max_open_positions: 10
  stop_loss_pct: 0.05
  take_profit_pct: 0.15
```

## Risk Rules

### 1. Drawdown Circuit Breaker

If total portfolio equity (cash + current market value of all positions) drops below `equity_peak * (1 - max_drawdown_pct)`, all trading halts immediately.

The drawdown is calculated from total equity, not just cash. This prevents false triggers when cash is low due to open positions that are still profitable.

This is a hard stop — once triggered, the manager stays halted for the remainder of the session. This prevents strategies from digging deeper into a losing streak.

```
equity_peak = $100,000
max_drawdown_pct = 0.20
trigger level = $80,000

If current equity (cash + positions) < $80,000 → all signals become HOLD
```

### 2. Position Count Limit

Caps the number of concurrent open positions. Prevents over-diversification or correlated position pyramiding.

```
max_open_positions = 10
current positions = 10
new BUY signal → converted to HOLD
```

### 3. Position Sizing

Caps any single position to `max_position_pct` of current equity. If a strategy requests a position larger than the limit, the size is reduced.

```
equity = $100,000
max_position_pct = 0.10
max position value = $10,000
stock price = $150
max shares = 66 (floored)
```

If the adjusted size is 0 or negative, the signal becomes HOLD.

### 3b. Short Selling Margin

Short positions require cash collateral. By default, 100% of the position value must be available in cash (configurable via `short_margin_rate` on the Portfolio). If insufficient margin is available, the short signal is rejected.

### 4. Default Stop-Loss and Take-Profit

If the strategy doesn't specify exit levels, the risk manager applies defaults:

| Signal | Stop-Loss | Take-Profit |
|--------|-----------|-------------|
| BUY | `price * (1 - stop_loss_pct)` | `price * (1 + take_profit_pct)` |
| SELL | `price * (1 + stop_loss_pct)` | `price * (1 - take_profit_pct)` |

Strategies can override these by setting `stop_loss` and `take_profit` in the signal.

## Stop Execution

Stops are checked by the portfolio on every bar, before the strategy runs:

```python
portfolio.check_stops(symbol, current_price, timestamp)
```

This means:
- Stop-loss and take-profit are evaluated at bar close prices
- The strategy sees the portfolio state after any stop-triggered exits
- Stops are not guaranteed to fill at the exact stop price (gap risk exists in real markets)

## Disabling Risk Management

Pass a permissive risk manager to the engine:

```python
risk = RiskManager(
    max_position_pct=1.0,
    max_drawdown_pct=1.0,
    max_open_positions=999,
    stop_loss_pct=1.0,
    take_profit_pct=1.0,
)
```

This effectively disables all risk checks. Useful for testing raw strategy performance, but not recommended for live trading.
