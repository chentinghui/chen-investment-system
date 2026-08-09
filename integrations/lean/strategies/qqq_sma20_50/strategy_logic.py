from __future__ import annotations

from dataclasses import dataclass

BUY = "BUY"
SELL = "SELL"


def crossover_signal(
    previous_fast: float | None,
    previous_slow: float | None,
    current_fast: float,
    current_slow: float,
) -> str | None:
    """Return a strict crossover event, not a persistent regime state."""
    if previous_fast is None or previous_slow is None:
        return None
    if previous_fast <= previous_slow and current_fast > current_slow:
        return BUY
    if previous_fast >= previous_slow and current_fast < current_slow:
        return SELL
    return None


def cash_interest_amount(cash: float, annual_rate: float, calendar_days: int) -> float:
    """Simple ACT/365 cash-yield accrual used by the CIS LEAN strategy."""
    if cash <= 0 or annual_rate <= 0 or calendar_days <= 0:
        return 0.0
    return cash * annual_rate * calendar_days / 365.0


@dataclass
class DrawdownTracker:
    peak: float = 0.0
    max_drawdown: float = 0.0

    def update(self, equity_value: float) -> float:
        if equity_value <= 0:
            return self.max_drawdown
        self.peak = max(self.peak, equity_value)
        if self.peak > 0:
            drawdown = equity_value / self.peak - 1.0
            self.max_drawdown = min(self.max_drawdown, drawdown)
        return self.max_drawdown
