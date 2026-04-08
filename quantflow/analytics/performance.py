"""Performance analytics and reporting."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from quantflow.core.models import Trade, OrderSide


class PerformanceReport:
    """Compute and display backtest performance metrics."""

    def __init__(self, trades: list[Trade], equity_curve: list[float], initial_capital: float) -> None:
        self.trades = trades
        self.equity_curve = np.array(equity_curve, dtype=np.float64)
        self.initial_capital = initial_capital

    @property
    def total_return(self) -> float:
        if len(self.equity_curve) == 0:
            return 0.0
        return (self.equity_curve[-1] - self.initial_capital) / self.initial_capital

    @property
    def total_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.pnl > 0)
        return wins / len(self.trades)

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float("inf")

    @property
    def max_drawdown(self) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        peak = np.maximum.accumulate(self.equity_curve)
        drawdown = (self.equity_curve - peak) / peak
        return float(np.min(drawdown))

    def sharpe_ratio(self, risk_free_rate: float = 0.0, periods: int = 252) -> float:
        """Calculate annualized Sharpe ratio.

        Args:
            risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%).
            periods: Number of trading periods per year (252 for daily).
        """
        if len(self.equity_curve) < 2:
            return 0.0
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        excess = returns - risk_free_rate / periods
        if np.std(excess) == 0:
            return 0.0
        return float(np.mean(excess) / np.std(excess) * np.sqrt(periods))

    def sortino_ratio(self, risk_free_rate: float = 0.0, periods: int = 252) -> float:
        """Calculate annualized Sortino ratio (downside deviation only).

        Args:
            risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%).
            periods: Number of trading periods per year (252 for daily).
        """
        if len(self.equity_curve) < 2:
            return 0.0
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        excess = returns - risk_free_rate / periods
        downside = excess[excess < 0]
        if len(downside) == 0 or np.std(downside) == 0:
            return 0.0
        return float(np.mean(excess) / np.std(downside) * np.sqrt(periods))

    @property
    def avg_trade_pnl(self) -> float:
        return self.total_pnl / self.num_trades if self.num_trades > 0 else 0.0

    @property
    def avg_win(self) -> float:
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        return np.mean(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        return np.mean(losses) if losses else 0.0

    @property
    def max_consecutive_wins(self) -> int:
        return self._max_consecutive(lambda t: t.pnl > 0)

    @property
    def max_consecutive_losses(self) -> int:
        return self._max_consecutive(lambda t: t.pnl < 0)

    def _max_consecutive(self, condition) -> int:
        max_count = count = 0
        for t in self.trades:
            if condition(t):
                count += 1
                max_count = max(max_count, count)
            else:
                count = 0
        return max_count

    def print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("  QUANTFLOW BACKTEST REPORT")
        print("=" * 60)
        print(f"  Initial Capital:      ${self.initial_capital:>14,.2f}")
        print(f"  Final Equity:         ${self.equity_curve[-1] if len(self.equity_curve) else 0:>14,.2f}")
        print(f"  Total Return:         {self.total_return:>14.2%}")
        print(f"  Total PnL:            ${self.total_pnl:>14,.2f}")
        print("-" * 60)
        print(f"  Total Trades:         {self.num_trades:>14d}")
        print(f"  Win Rate:             {self.win_rate:>14.2%}")
        print(f"  Profit Factor:        {self.profit_factor:>14.2f}")
        print(f"  Avg Trade PnL:        ${self.avg_trade_pnl:>14,.2f}")
        print(f"  Avg Win:              ${self.avg_win:>14,.2f}")
        print(f"  Avg Loss:             ${self.avg_loss:>14,.2f}")
        print("-" * 60)
        print(f"  Sharpe Ratio:         {self.sharpe_ratio():>14.2f}")
        print(f"  Sortino Ratio:        {self.sortino_ratio():>14.2f}")
        print(f"  Max Drawdown:         {self.max_drawdown:>14.2%}")
        print(f"  Max Consec. Wins:     {self.max_consecutive_wins:>14d}")
        print(f"  Max Consec. Losses:   {self.max_consecutive_losses:>14d}")
        print("=" * 60 + "\n")

    def plot(self, save_path: str = None) -> None:
        """Plot equity curve and drawdown."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]})

        # Equity curve
        ax1.plot(self.equity_curve, color="#2196F3", linewidth=1.5, label="Equity")
        ax1.axhline(y=self.initial_capital, color="gray", linestyle="--", alpha=0.5)
        ax1.set_title("Equity Curve", fontsize=14)
        ax1.set_ylabel("Equity ($)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Drawdown
        peak = np.maximum.accumulate(self.equity_curve)
        drawdown = (self.equity_curve - peak) / peak * 100
        ax2.fill_between(range(len(drawdown)), drawdown, color="#F44336", alpha=0.4)
        ax2.set_title("Drawdown", fontsize=14)
        ax2.set_ylabel("Drawdown (%)")
        ax2.set_xlabel("Bar")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.show()
