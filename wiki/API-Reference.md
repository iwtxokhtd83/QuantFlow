# API Reference

## Core Models

### `quantflow.core.models.Bar`

```python
@dataclass
class Bar:
    symbol: str                              # ticker symbol
    timestamp: datetime                      # bar timestamp
    open: float                              # open price
    high: float                              # high price
    low: float                               # low price
    close: float                             # close price
    volume: float                            # trading volume
    close_prices: Optional[np.ndarray]       # rolling close price history

    @property mid -> float                   # (high + low) / 2
    @property spread -> float                # high - low
    @property body -> float                  # abs(close - open)
    @property is_bullish -> bool             # close > open
```

### `quantflow.core.models.Order`

```python
@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide                          # BUY | SELL
    order_type: OrderType                    # MARKET | LIMIT | STOP | STOP_LIMIT
    quantity: float
    price: Optional[float]                   # limit price
    stop_price: Optional[float]              # stop trigger price
    status: OrderStatus                      # PENDING | SUBMITTED | FILLED | ...
    created_at: datetime
    filled_at: Optional[datetime]
    filled_price: Optional[float]
    commission: float
```

### `quantflow.core.models.Trade`

```python
@dataclass
class Trade:
    id: str
    symbol: str
    side: OrderSide
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    commission: float

    @property pnl -> float                   # net profit/loss after commission
    @property pnl_pct -> float               # percentage return
    @property duration -> timedelta           # trade duration
```

### `quantflow.core.models.Position`

```python
@dataclass
class Position:
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float                     # updated each bar
    stop_loss: Optional[float]
    take_profit: Optional[float]

    @property market_value -> float           # quantity * current_price
    @property cost_basis -> float             # quantity * entry_price
    def unrealized_pnl(current_price=None) -> float
```

## Event System

### `quantflow.core.events.EventBus`

```python
class EventBus:
    def subscribe(event_type: EventType, handler: Callable) -> None
    def unsubscribe(event_type: EventType, handler: Callable) -> None
    def publish(event: Event) -> None
```

### `quantflow.core.events.Event`

```python
@dataclass
class Event:
    type: EventType
    data: Any
    timestamp: datetime
```

## Data Feeds

### `quantflow.data.feeds.DataFeed` (abstract)

```python
class DataFeed(ABC):
    def load() -> pd.DataFrame              # load raw OHLCV data
    def bars(symbol: str) -> Iterator[Bar]   # yield Bar objects
```

### `quantflow.data.feeds.CSVDataFeed`

```python
class CSVDataFeed(DataFeed):
    def __init__(filepath: str, date_column: str = "date")
```

### `quantflow.data.feeds.YahooDataFeed`

```python
class YahooDataFeed(DataFeed):
    def __init__(symbol: str, start: str, end: str, interval: str = "1d")
```

## Strategies

### `quantflow.strategies.base.Strategy` (abstract)

```python
class Strategy(ABC):
    name: str

    def on_bar(bar: Bar, portfolio) -> Signal    # required
    def on_start() -> None                        # optional
    def on_stop() -> None                         # optional
    def buy(size, stop_loss, take_profit) -> Signal
    def sell(size, stop_loss, take_profit) -> Signal
    def hold() -> Signal
```

### `quantflow.strategies.base.Signal`

```python
@dataclass
class Signal:
    type: SignalType                  # BUY | SELL | HOLD
    size: Optional[float]
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    metadata: Optional[dict]
```

## Engine

### `quantflow.engine.backtest.BacktestEngine`

```python
@dataclass
class BacktestEngine:
    data_feed: DataFeed
    strategy: Strategy
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    symbol: str = "UNKNOWN"
    risk_manager: RiskManager = RiskManager()

    def run() -> PerformanceReport
```

### `quantflow.engine.live.LiveEngine`

```python
@dataclass
class LiveEngine:
    strategy: Strategy
    broker: Broker
    symbol: str = "AAPL"
    interval: str = "1m"
    risk_manager: RiskManager = RiskManager()

    def start() -> None       # blocking
    def stop() -> None
```

## Risk

### `quantflow.risk.manager.RiskManager`

```python
@dataclass
class RiskManager:
    max_position_pct: float = 0.10
    max_drawdown_pct: float = 0.20
    max_open_positions: int = 10
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15

    def check(signal, current_price, equity, equity_peak, open_position_count) -> Signal
    def reset() -> None
```

## Portfolio

### `quantflow.portfolio.manager.Portfolio`

```python
@dataclass
class Portfolio:
    initial_capital: float = 100000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    short_margin_rate: float = 1.0

    @property cash -> float
    @property equity -> float                # cash + current market value of positions
    @property open_position_count -> int
    def has_position(symbol: str) -> bool
    def update_market_prices(symbol, current_price) -> None
    def execute_signal(signal, symbol, current_price, timestamp) -> Optional[Order]
    def check_stops(symbol, current_price, timestamp) -> Optional[Order]
    def update_equity() -> None
```

## Analytics

### `quantflow.analytics.performance.PerformanceReport`

```python
class PerformanceReport:
    trades: list[Trade]
    equity_curve: np.ndarray
    initial_capital: float

    @property total_return -> float
    @property total_pnl -> float
    @property num_trades -> int
    @property win_rate -> float
    @property profit_factor -> float
    @property max_drawdown -> float
    @property avg_trade_pnl -> float
    @property avg_win -> float
    @property avg_loss -> float
    @property max_consecutive_wins -> int
    @property max_consecutive_losses -> int

    def sharpe_ratio(risk_free_rate=0.0, periods=252) -> float
    def sortino_ratio(risk_free_rate=0.0, periods=252) -> float

    def print_summary() -> None
    def plot(save_path: str = None) -> None
```

## Brokers

### `quantflow.brokers.base.Broker` (abstract)

```python
class Broker(ABC):
    commission_rate: float = 0.001

    def get_balance() -> float
    def get_latest_bar(symbol, interval) -> Optional[dict]
    def place_order(symbol, side, quantity, order_type, price) -> dict
    def cancel_order(order_id) -> bool
    def get_positions() -> list[dict]
```

### `quantflow.brokers.paper.PaperBroker`

```python
class PaperBroker(Broker):
    def __init__(initial_capital: float = 100000.0, commission_rate: float = 0.001)
```
