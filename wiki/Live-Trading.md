# Live Trading

## Paper Trading

Paper trading uses simulated execution to test strategies in real-time without risking capital.

```python
from quantflow.brokers import PaperBroker
from quantflow.engine import LiveEngine
from quantflow.strategies import RSIMeanReversion

strategy = RSIMeanReversion(period=14, oversold=30, overbought=70, size=50)
broker = PaperBroker(initial_capital=100000)

engine = LiveEngine(
    strategy=strategy,
    broker=broker,
    symbol="AAPL",
    interval="1m",      # poll every 1 minute
)

engine.start()          # blocks until Ctrl+C or engine.stop()
```

The `PaperBroker` generates synthetic price bars with random walks. Override `get_latest_bar()` to feed real market data.

## LiveEngine Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy` | Strategy | required | Trading strategy |
| `broker` | Broker | required | Broker adapter |
| `symbol` | str | "AAPL" | Ticker symbol |
| `interval` | str | "1m" | Bar interval |
| `risk_manager` | RiskManager | default | Risk config |

### Interval Format

| Value | Meaning |
|-------|---------|
| `5s` | 5 seconds |
| `1m` | 1 minute |
| `5m` | 5 minutes |
| `15m` | 15 minutes |
| `1h` | 1 hour |
| `1d` | 1 day |

## Broker Interface

All brokers implement the `Broker` abstract class:

```python
class Broker(ABC):
    def get_balance(self) -> float: ...
    def get_latest_bar(self, symbol: str, interval: str) -> Optional[dict]: ...
    def place_order(self, symbol, side, quantity, order_type, price) -> dict: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_positions(self) -> list[dict]: ...
```

### Writing a Custom Broker

To connect to a real exchange, implement the `Broker` interface:

```python
from quantflow.brokers.base import Broker

class BinanceBroker(Broker):
    def __init__(self, api_key: str, api_secret: str):
        self.client = BinanceClient(api_key, api_secret)
        self.commission_rate = 0.001

    def get_balance(self) -> float:
        return self.client.get_account_balance("USDT")

    def get_latest_bar(self, symbol: str, interval: str) -> dict:
        kline = self.client.get_klines(symbol, interval, limit=1)[0]
        return {
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
        }

    def place_order(self, symbol, side, quantity, order_type="market", price=None):
        return self.client.create_order(
            symbol=symbol, side=side.upper(),
            type=order_type.upper(), quantity=quantity,
        )

    def cancel_order(self, order_id: str) -> bool:
        return self.client.cancel_order(order_id)

    def get_positions(self) -> list[dict]:
        return self.client.get_open_positions()
```

## Safety Considerations

1. Always test with paper trading before going live
2. Set conservative risk limits (see [Risk Management](Risk-Management))
3. Monitor the live engine — don't leave it unattended for extended periods
4. Implement kill switches and maximum daily loss limits
5. Start with small position sizes and scale up gradually
6. Be aware of exchange rate limits and API restrictions
