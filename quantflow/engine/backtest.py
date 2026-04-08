"""Backtest engine — event-driven simulation of historical data."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from quantflow.analytics.performance import PerformanceReport
from quantflow.core.events import Event, EventBus, EventType
from quantflow.data.feeds import DataFeed
from quantflow.portfolio.manager import Portfolio
from quantflow.risk.manager import RiskManager
from quantflow.strategies.base import Strategy

logger = logging.getLogger(__name__)


@dataclass
class BacktestEngine:
    """Run a strategy against historical data."""

    data_feed: DataFeed
    strategy: Strategy
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    symbol: str = "UNKNOWN"
    risk_manager: RiskManager = field(default_factory=RiskManager)

    def run(self) -> PerformanceReport:
        event_bus = EventBus()
        portfolio = Portfolio(
            initial_capital=self.initial_capital,
            commission_rate=self.commission,
            slippage_rate=self.slippage,
        )

        logger.info("Starting backtest: %s on %s", self.strategy.name, self.symbol)
        event_bus.publish(Event(EventType.ENGINE_START))
        self.strategy.on_start()

        bar_count = 0
        for bar in self.data_feed.bars(symbol=self.symbol):
            bar_count += 1
            event_bus.publish(Event(EventType.BAR, data=bar))

            # Update market prices and check stops
            portfolio.update_market_prices(bar.symbol, bar.close)
            portfolio.check_stops(bar.symbol, bar.close, bar.timestamp)

            # Get strategy signal
            signal = self.strategy.on_bar(bar, portfolio)

            # Risk check — uses total equity for drawdown calculation
            signal = self.risk_manager.check(
                signal=signal,
                current_price=bar.close,
                equity=portfolio.equity,
                equity_peak=portfolio.equity_peak,
                open_position_count=portfolio.open_position_count,
            )

            # Execute
            portfolio.execute_signal(signal, bar.symbol, bar.close, bar.timestamp)
            portfolio.update_equity()

        self.strategy.on_stop()
        event_bus.publish(Event(EventType.ENGINE_STOP))
        logger.info("Backtest complete: %d bars, %d trades", bar_count, len(portfolio.trades))

        return PerformanceReport(
            trades=portfolio.trades,
            equity_curve=portfolio.equity_curve,
            initial_capital=self.initial_capital,
        )
