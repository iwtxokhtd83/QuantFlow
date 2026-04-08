# Configuration

QuantFlow uses YAML configuration files for engine, risk, data, and logging settings.

## Config File Location

```
config/
├── default.yaml    # default configuration (tracked in git)
└── local.yaml      # local overrides (gitignored)
```

## Loading Config

```python
from quantflow.utils import load_config

config = load_config("config/default.yaml")
# or
config = load_config("config/local.yaml")
```

## Full Config Reference

```yaml
# Engine settings
engine:
  mode: backtest          # backtest | paper | live
  initial_capital: 100000 # starting cash
  commission: 0.001       # commission rate (0.1%)
  slippage: 0.0005        # slippage rate (0.05%)

# Risk management
risk:
  max_position_pct: 0.1   # max 10% of capital per position
  max_drawdown_pct: 0.2   # halt at 20% drawdown
  max_open_positions: 10   # max concurrent positions
  stop_loss_pct: 0.05     # default 5% stop loss
  take_profit_pct: 0.15   # default 15% take profit

# Data source
data:
  source: csv             # csv | yahoo | binance
  symbol: AAPL            # ticker symbol
  interval: 1d            # 1m, 5m, 15m, 1h, 1d
  start_date: "2020-01-01"
  end_date: "2025-12-31"

# Logging
logging:
  level: INFO             # DEBUG, INFO, WARNING, ERROR
  file: logs/quantflow.log
```

## Using Config in Code

```python
from quantflow.utils import load_config
from quantflow.risk import RiskManager
from quantflow.engine import BacktestEngine
from quantflow.data import CSVDataFeed
from quantflow.strategies import SMACrossover

config = load_config("config/default.yaml")

risk = RiskManager(
    max_position_pct=config["risk"]["max_position_pct"],
    max_drawdown_pct=config["risk"]["max_drawdown_pct"],
    max_open_positions=config["risk"]["max_open_positions"],
    stop_loss_pct=config["risk"]["stop_loss_pct"],
    take_profit_pct=config["risk"]["take_profit_pct"],
)

engine = BacktestEngine(
    data_feed=CSVDataFeed("data/sample_ohlcv.csv"),
    strategy=SMACrossover(),
    initial_capital=config["engine"]["initial_capital"],
    commission=config["engine"]["commission"],
    slippage=config["engine"]["slippage"],
    risk_manager=risk,
)
```

## Environment-Specific Config

Create `config/local.yaml` for your local settings (it's gitignored):

```bash
cp config/default.yaml config/local.yaml
```

Edit `local.yaml` with your specific parameters — API keys, custom paths, etc.
