"""Risk management module — position sizing, drawdown limits, exposure controls."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from quantflow.core.models import OrderSide
from quantflow.strategies.base import Signal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class RiskManager:
    """Enforces risk rules before orders are placed."""

    max_position_pct: float = 0.10       # max % of capital per position
    max_drawdown_pct: float = 0.20       # halt trading at this drawdown
    max_open_positions: int = 10
    stop_loss_pct: float = 0.05          # default stop loss
    take_profit_pct: float = 0.15        # default take profit
    _halted: bool = field(default=False, init=False)

    def check(self, signal: Signal, current_price: float, equity: float,
              equity_peak: float, open_position_count: int) -> Signal:
        """Validate and potentially modify a signal based on risk rules.

        Args:
            signal: The trading signal to validate.
            current_price: Current market price of the asset.
            equity: Total portfolio equity (cash + position market values).
            equity_peak: Highest equity value seen so far.
            open_position_count: Number of currently open positions.
        """
        if signal.type == SignalType.HOLD:
            return signal

        # Drawdown check — uses total equity, not just cash
        if equity < equity_peak * (1 - self.max_drawdown_pct):
            if not self._halted:
                logger.warning("Max drawdown breached (%.1f%%). Trading halted.",
                               self.max_drawdown_pct * 100)
                self._halted = True
            return Signal(SignalType.HOLD)

        if self._halted:
            return Signal(SignalType.HOLD)

        # Position count check
        if signal.type == SignalType.BUY and open_position_count >= self.max_open_positions:
            logger.info("Max open positions reached (%d). Skipping buy.", self.max_open_positions)
            return Signal(SignalType.HOLD)

        # Position sizing — cap to max_position_pct of equity
        max_value = equity * self.max_position_pct
        max_size = max_value / current_price if current_price > 0 else 0
        if signal.size and signal.size * current_price > max_value:
            signal.size = int(max_size)
            logger.info("Position sized down to %d shares (%.1f%% cap).", signal.size, self.max_position_pct * 100)

        if signal.size is not None and signal.size <= 0:
            return Signal(SignalType.HOLD)

        # Apply default stop loss / take profit if not set
        if signal.stop_loss is None:
            if signal.type == SignalType.BUY:
                signal.stop_loss = current_price * (1 - self.stop_loss_pct)
            else:
                signal.stop_loss = current_price * (1 + self.stop_loss_pct)

        if signal.take_profit is None:
            if signal.type == SignalType.BUY:
                signal.take_profit = current_price * (1 + self.take_profit_pct)
            else:
                signal.take_profit = current_price * (1 - self.take_profit_pct)

        return signal

    def reset(self) -> None:
        self._halted = False
