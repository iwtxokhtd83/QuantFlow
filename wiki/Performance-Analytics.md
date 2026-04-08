# Performance Analytics

The `PerformanceReport` class computes standard quantitative metrics from backtest results.

## Usage

```python
result = engine.run()
result.print_summary()    # print formatted report
result.plot()             # show equity curve + drawdown chart
result.plot(save_path="report.png")  # save to file

# Sharpe and Sortino are methods — customize risk-free rate and periods
result.sharpe_ratio()                              # default: rf=0.0, periods=252
result.sharpe_ratio(risk_free_rate=0.02)           # 2% annual risk-free rate
result.sortino_ratio(risk_free_rate=0.02, periods=252)
```

## Metrics Reference

### Return Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Total Return | `(final_equity - initial) / initial` | Overall percentage gain/loss |
| Total PnL | `sum(trade.pnl for all trades)` | Absolute dollar profit/loss |

### Trade Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Num Trades | Count of completed round-trips | Sample size for statistical significance |
| Win Rate | `winning_trades / total_trades` | Percentage of profitable trades |
| Profit Factor | `gross_profit / gross_loss` | > 1.0 means profitable overall |
| Avg Trade PnL | `total_pnl / num_trades` | Average profit per trade |
| Avg Win | Mean PnL of winning trades | Typical winning trade size |
| Avg Loss | Mean PnL of losing trades | Typical losing trade size |
| Max Consec. Wins | Longest winning streak | Streak analysis |
| Max Consec. Losses | Longest losing streak | Streak analysis |

### Risk-Adjusted Metrics

| Metric | Formula | Good Value |
|--------|---------|------------|
| Sharpe Ratio | `result.sharpe_ratio(risk_free_rate, periods)` | > 1.0 |
| Sortino Ratio | `result.sortino_ratio(risk_free_rate, periods)` | > 1.5 |
| Max Drawdown | `min((equity - peak) / peak)` | > -20% |

Note: `sharpe_ratio()` and `sortino_ratio()` are methods (not properties) so you can pass custom `risk_free_rate` and `periods` arguments.

### Understanding Sharpe Ratio

The Sharpe ratio measures return per unit of risk (volatility):

| Sharpe | Interpretation |
|--------|----------------|
| < 0 | Losing money |
| 0 - 0.5 | Poor |
| 0.5 - 1.0 | Below average |
| 1.0 - 2.0 | Good |
| 2.0 - 3.0 | Very good |
| > 3.0 | Excellent (verify — may be overfitting) |

### Understanding Sortino Ratio

Like Sharpe, but only penalizes downside volatility. A strategy with high upside volatility (big winners) will have a better Sortino than Sharpe.

### Understanding Max Drawdown

The largest peak-to-trough decline in equity:

| Max Drawdown | Interpretation |
|-------------|----------------|
| > -5% | Very conservative |
| -5% to -15% | Moderate |
| -15% to -25% | Aggressive |
| < -25% | High risk |

## Visualization

`result.plot()` generates a two-panel chart:

1. **Equity Curve** (top) — portfolio value over time, with initial capital baseline
2. **Drawdown Chart** (bottom) — percentage drawdown from peak at each point

```python
result.plot(save_path="output/backtest_report.png")
```

## Accessing Raw Data

```python
# Equity curve as numpy array
equity = result.equity_curve

# All completed trades
for trade in result.trades:
    print(f"{trade.symbol} {trade.side.name}: {trade.pnl:.2f} ({trade.pnl_pct:.2%})")
    print(f"  Entry: {trade.entry_price:.2f} @ {trade.entry_time}")
    print(f"  Exit:  {trade.exit_price:.2f} @ {trade.exit_time}")
    print(f"  Duration: {trade.duration}")
```

## Exporting Results

```python
import pandas as pd

# Export trades to CSV
trades_df = pd.DataFrame([{
    "symbol": t.symbol,
    "side": t.side.name,
    "entry_price": t.entry_price,
    "exit_price": t.exit_price,
    "quantity": t.quantity,
    "pnl": t.pnl,
    "pnl_pct": t.pnl_pct,
    "entry_time": t.entry_time,
    "exit_time": t.exit_time,
} for t in result.trades])
trades_df.to_csv("output/trades.csv", index=False)

# Export equity curve
eq_df = pd.DataFrame({"equity": result.equity_curve})
eq_df.to_csv("output/equity_curve.csv", index=False)
```
