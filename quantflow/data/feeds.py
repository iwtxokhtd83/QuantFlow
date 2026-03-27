"""Data feed implementations for market data ingestion."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional

import numpy as np
import pandas as pd

from quantflow.core.models import Bar

logger = logging.getLogger(__name__)


class DataFeed(ABC):
    """Abstract base class for all data feeds."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load raw OHLCV data into a DataFrame."""

    def bars(self, symbol: str = "UNKNOWN") -> Iterator[Bar]:
        """Yield Bar objects with rolling close price history."""
        df = self.load()
        closes = []
        for _, row in df.iterrows():
            closes.append(row["close"])
            yield Bar(
                symbol=symbol,
                timestamp=row.name if isinstance(row.name, pd.Timestamp) else pd.Timestamp(row.get("date", row.name)),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0)),
                close_prices=np.array(closes, dtype=np.float64),
            )


class CSVDataFeed(DataFeed):
    """Load OHLCV data from a CSV file."""

    def __init__(self, filepath: str, date_column: str = "date") -> None:
        self.filepath = Path(filepath)
        self.date_column = date_column

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.filepath, parse_dates=[self.date_column])
        df.set_index(self.date_column, inplace=True)
        df.sort_index(inplace=True)
        df.columns = [c.lower().strip() for c in df.columns]
        logger.info("Loaded %d bars from %s", len(df), self.filepath)
        return df


class YahooDataFeed(DataFeed):
    """Download OHLCV data from Yahoo Finance (via public CSV endpoint)."""

    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/download"

    def __init__(self, symbol: str, start: str, end: str, interval: str = "1d") -> None:
        self.symbol = symbol
        self.start = start
        self.end = end
        self.interval = interval

    def load(self) -> pd.DataFrame:
        import requests
        from datetime import datetime

        period1 = int(datetime.strptime(self.start, "%Y-%m-%d").timestamp())
        period2 = int(datetime.strptime(self.end, "%Y-%m-%d").timestamp())
        url = f"{self.BASE_URL}/{self.symbol}?period1={period1}&period2={period2}&interval={self.interval}&events=history"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()

        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), parse_dates=["Date"])
        df.set_index("Date", inplace=True)
        df.columns = [c.lower().strip() for c in df.columns]
        df.rename(columns={"adj close": "adj_close"}, inplace=True)
        logger.info("Downloaded %d bars for %s", len(df), self.symbol)
        return df
