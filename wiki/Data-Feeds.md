# Data Feeds

QuantFlow uses a `DataFeed` abstraction to decouple data ingestion from the engine.

## DataFeed Interface

All data feeds implement two methods:

```python
class DataFeed(ABC):
    def load(self) -> pd.DataFrame:
        """Load raw OHLCV data into a DataFrame."""

    def bars(self, symbol: str) -> Iterator[Bar]:
        """Yield Bar objects with rolling close price history."""
```

The `bars()` method is provided by the base class — it calls `load()`, then iterates the DataFrame and yields `Bar` objects with an accumulating `close_prices` numpy array.

## CSVDataFeed

Load OHLCV data from a local CSV file:

```python
from quantflow.data import CSVDataFeed

data = CSVDataFeed("data/sample_ohlcv.csv", date_column="date")
```

Expected CSV format:

```csv
date,open,high,low,close,volume
2020-01-02,100.00,101.50,99.20,100.80,1000000
2020-01-03,100.80,102.00,100.10,101.50,1200000
```

- Column names are case-insensitive (auto-lowercased)
- The date column is parsed as datetime and used as the index
- Data is sorted by date ascending

## YahooDataFeed

Download historical data from Yahoo Finance:

```python
from quantflow.data import YahooDataFeed

data = YahooDataFeed(
    symbol="AAPL",
    start="2020-01-01",
    end="2025-12-31",
    interval="1d"    # 1m, 5m, 15m, 1h, 1d
)
```

Note: Yahoo Finance may rate-limit or block requests. This feed is best for research and prototyping, not production data pipelines.

## Writing a Custom Data Feed

Extend `DataFeed` and implement `load()`:

```python
from quantflow.data.feeds import DataFeed
import pandas as pd

class PostgresDataFeed(DataFeed):
    def __init__(self, connection_string: str, query: str):
        self.conn_str = connection_string
        self.query = query

    def load(self) -> pd.DataFrame:
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.conn_str)
        df = pd.read_sql(self.query, engine, parse_dates=["date"])
        df.set_index("date", inplace=True)
        df.columns = [c.lower() for c in df.columns]
        return df
```

The only requirement is that `load()` returns a DataFrame with:
- A datetime index
- Columns: `open`, `high`, `low`, `close`, `volume` (lowercase)

## Sample Data Generator

For testing without real market data:

```bash
python data/generate_sample.py
```

Generates ~1000 days of synthetic OHLCV data with:
- Slight upward drift (realistic for equity markets)
- Random volatility
- Weekend gaps skipped
- Realistic volume distribution
