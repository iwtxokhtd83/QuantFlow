# Getting Started

## Requirements

- Python 3.10+
- pip

## Installation

```bash
git clone https://github.com/iwtxokhtd83/QuantFlow.git
cd QuantFlow
pip install -r requirements.txt
```

## Generate Sample Data

QuantFlow ships with a synthetic data generator for testing:

```bash
python data/generate_sample.py
```

This creates `data/sample_ohlcv.csv` with ~1000 trading days of realistic OHLCV data.

## Your First Backtest

```python
from quantflow.data import CSVDataFeed
from quantflow.engine import BacktestEngine
from quantflow.strategies import SMACrossover

data = CSVDataFeed("data/sample_ohlcv.csv")
strategy = SMACrossover(fast_period=10, slow_period=30)
engine = BacktestEngine(data_feed=data, strategy=strategy, initial_capital=100000)

result = engine.run()
result.print_summary()
result.plot()
```

Output:

```
============================================================
  QUANTFLOW BACKTEST REPORT
============================================================
  Initial Capital:      $    100,000.00
  Final Equity:         $    328,288.04
  Total Return:                228.29%
  ...
============================================================
```

## Compare Multiple Strategies

```bash
python examples/backtest_multi_strategy.py
```

This runs all four built-in strategies on the same data and prints a comparison table.

## Project Structure

```
quantflow/
├── core/           # Event bus, data models, enums
├── data/           # Data feed abstraction and implementations
├── indicators/     # 16 technical indicators (pure numpy)
├── strategies/     # Strategy base class + 4 built-in strategies
├── engine/         # Backtest and live trading engines
├── brokers/        # Broker adapters (paper trading)
├── risk/           # Risk management layer
├── portfolio/      # Position tracking and order execution
├── analytics/      # Performance metrics and visualization
└── utils/          # Config loader, logging setup
```

## Next Steps

- Read [Architecture](Architecture) to understand the system design
- Explore [Strategies](Strategies) to write your own
- Check [Backtesting](Backtesting) for advanced configuration
