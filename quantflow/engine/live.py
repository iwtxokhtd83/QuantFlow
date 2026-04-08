"""Live trading engine — real-time strategy execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from quantflow.brokers.base import Broker
from quantflow.core.events import Event, EventBus, EventType
from quantflow.core.models import Bar
from quantflow.portfolio.manager import Portfolio
from quantflow.risk.manager import RiskManager
from quantflow.strategies.base import Strategy

logger = logging.getLogger(__name__)


@dataclass
class LiveEngine:
    """Run a strategy in real-time against a broker."""

    strategy: Strategy
    broker: Broker
    symbol: str = "AAPL"
    interval: str = "1m"
    risk_manager: RiskManager = field(default_factory=RiskManager)
    _running: bool = field(default=False, init=False)

    def start(self) -> None:
        event_bus = EventBus()
        portfolio = Portfolio(
            initial_capital=self.broker.get_balance(),
            commission_rate=self.broker.commission_rate,
        )

        logger.info("Starting live engine: %s on %s", self.strategy.name, self.symbol)
        event_bus.publish(Event(EventType.ENGINE_START))
        self.strategy.on_start()
        self._running = True

        close_history: list[float] = []

        while self._running:
            try:
                bar_data = self.broker.get_latest_bar(self.symbol, self.interval)
                if bar_data is None:
                    time.sleep(1)
                    continue

                close_history.append(bar_data["close"])
                bar = Bar(
                    symbol=self.symbol,
                    timestamp=datetime.utcnow(),
                    open=bar_data["open"],
                    high=bar_data["high"],
                    low=bar_data["low"],
                    close=bar_data["close"],
                    volume=bar_data.get("volume", 0),
                    close_prices=np.array(close_history, dtype=np.float64),
                )

                event_bus.publish(Event(EventType.BAR, data=bar))
                portfolio.update_market_prices(bar.symbol, bar.close)
                portfolio.check_stops(bar.symbol, bar.close, bar.timestamp)

                signal = self.strategy.on_bar(bar, portfolio)
                signal = self.risk_manager.check(
                    signal=signal,
                    current_price=bar.close,
                    equity=portfolio.equity,
                    equity_peak=portfolio.equity_peak,
                    open_position_count=portfolio.open_position_count,
                )

                portfolio.execute_signal(signal, bar.symbol, bar.close, bar.timestamp)
                portfolio.update_equity()

                # Wait for next bar
                interval_seconds = self._parse_interval(self.interval)
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("Live engine stopped by user.")
                break
            except Exception as e:
                logger.error("Live engine error: %s", e)
                time.sleep(5)

        self.strategy.on_stop()
        event_bus.publish(Event(EventType.ENGINE_STOP))

    def stop(self) -> None:
        self._running = False

    @staticmethod
    def _parse_interval(interval: str) -> int:
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return int(interval[:-1]) * units.get(interval[-1], 60)
