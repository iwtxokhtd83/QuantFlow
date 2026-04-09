# QuantFlow - Open Source Quantitative Trading System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modular, extensible quantitative trading framework for strategy development, backtesting, and live trading.

## Features

- **Strategy Engine** — Write strategies with a simple, declarative API
- **Backtesting** — High-performance vectorized and event-driven backtesting
- **Live Trading** — Paper and live trading via broker adapters (Binance, Interactive Brokers)
- **Risk Management** — Position sizing, stop-loss, drawdown limits, exposure controls
- **Data Pipeline** — Multi-source market data ingestion and normalization
- **Portfolio Management** — Multi-asset portfolio tracking and rebalancing
- **Technical Indicators** — 30+ built-in indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- **Performance Analytics** — Sharpe ratio, max drawdown, win rate, and detailed trade logs
- **Event-Driven Architecture** — Clean separation of concerns via an event bus
- **Extensible** — Plugin-based design for custom strategies, data sources, and brokers

## Quick Start

```bash
pip install -r requirements.txt
```

### Run a Backtest

```python
from quantflow.engine import BacktestEngine
from quantflow.strategies import SMACrossover
from quantflow.data import CSVDataFeed

data = CSVDataFeed("data/sample_ohlcv.csv")
strategy = SMACrossover(fast_period=10, slow_period=30)
engine = BacktestEngine(data_feed=data, strategy=strategy, initial_capital=100000)
result = engine.run()
result.print_summary()
result.plot()
```

### Run Live Paper Trading

```python
from quantflow.engine import LiveEngine
from quantflow.strategies import RSIMeanReversion
from quantflow.brokers import PaperBroker

strategy = RSIMeanReversion(period=14, oversold=30, overbought=70)
broker = PaperBroker(initial_capital=100000)
engine = LiveEngine(strategy=strategy, broker=broker, symbol="AAPL", interval="1m")
engine.start()
```

## Project Structure

```
quantflow/
├── core/           # Event bus, base classes, enums
├── data/           # Data feeds, downloaders, storage
├── indicators/     # Technical indicators library
├── strategies/     # Strategy base class and built-in strategies
├── engine/         # Backtest and live trading engines
├── brokers/        # Broker adapters (paper, Binance, IB)
├── risk/           # Risk management and position sizing
├── portfolio/      # Portfolio tracking and management
├── analytics/      # Performance metrics and reporting
└── utils/          # Logging, config, helpers
```

## Writing a Custom Strategy

```python
from quantflow.strategies.base import Strategy
from quantflow.indicators import SMA, RSI

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        self.sma = SMA(period=20)
        self.rsi = RSI(period=14)

    def on_bar(self, bar, portfolio):
        sma_val = self.sma.calculate(bar.close_prices)
        rsi_val = self.rsi.calculate(bar.close_prices)

        if bar.close < sma_val and rsi_val < 30:
            return self.buy(size=100)
        elif bar.close > sma_val and rsi_val > 70:
            return self.sell(size=100)
        return self.hold()
```

## Configuration

Copy and edit the config template:

```bash
cp config/default.yaml config/local.yaml
```

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

89 tests covering indicators, risk management, portfolio execution, strategies, and engine integration.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

## Changelog

### v0.3.0 (2026-04-09)

- Added comprehensive test suite — 89 tests covering indicators, risk management, portfolio execution, strategies, and backtest engine integration
- Tests for edge cases: empty data, single bar, zero volume, zero price, insufficient data warm-up

### v0.2.0 (2026-04-08)

Bug fixes and accuracy improvements:

- Fixed `sharpe_ratio()` and `sortino_ratio()` — now callable methods with customizable `risk_free_rate` and `periods` parameters (previously `@property` silently ignored arguments)
- Fixed drawdown calculation — risk manager now uses total portfolio equity instead of cash only, preventing false drawdown triggers when positions are open
- Fixed `Portfolio.equity` — now reflects current market prices instead of entry cost basis
- Added short selling margin check — short positions now require cash collateral
- Optimized `DataFeed.bars()` — uses pre-allocated numpy array slicing instead of O(n²) per-bar array creation
- Optimized `EMA.calculate()` — computes final value directly instead of rebuilding the full series
- Fixed Stochastic %D alignment — %D line now correctly aligns with %K using in-place SMA
- Fixed `MACD.calculate()` — returns `None` instead of `NaN` when signal line has insufficient data

## Disclaimer

This software is for educational and research purposes only. Do not use it for actual trading without understanding the risks. The authors are not responsible for any financial losses.

## License

MIT License — see [LICENSE](LICENSE) for details.
