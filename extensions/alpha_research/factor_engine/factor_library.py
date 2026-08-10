from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, pstdev
from typing import Any, Iterable


DEFAULT_FACTOR_NAMES = (
    "momentum_5",
    "momentum_20",
    "reversal_5",
    "low_volatility_20",
    "volume_surprise_20",
)


def _finite(value: Any, *, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _normalized_bars(
    rows: Iterable[dict[str, Any]],
    *,
    date_field: str,
    ticker_field: str,
    close_field: str,
    volume_field: str,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()

    for index, row in enumerate(rows):
        date_value = str(row.get(date_field) or "").strip()
        ticker = str(row.get(ticker_field) or "").strip().upper()
        if not date_value:
            raise ValueError(f"row {index} has empty {date_field}")
        if not ticker:
            raise ValueError(f"row {index} has empty {ticker_field}")
        key = (date_value, ticker)
        if key in seen:
            raise ValueError(f"duplicate date/ticker observation: {date_value} {ticker}")
        seen.add(key)

        close = _finite(row.get(close_field), field=close_field)
        if close <= 0:
            raise ValueError(f"{close_field} must be > 0")

        volume_raw = row.get(volume_field)
        volume = None
        if volume_raw not in (None, ""):
            volume = _finite(volume_raw, field=volume_field)
            if volume < 0:
                raise ValueError(f"{volume_field} cannot be negative")

        grouped[ticker].append(
            {"date": date_value, "ticker": ticker, "close": close, "volume": volume}
        )

    for ticker in grouped:
        grouped[ticker].sort(key=lambda item: item["date"])
    return dict(grouped)


def build_factor_panel(
    rows: Iterable[dict[str, Any]],
    *,
    date_field: str = "date",
    ticker_field: str = "ticker",
    close_field: str = "close",
    volume_field: str = "volume",
    forward_horizon: int = 1,
) -> list[dict[str, Any]]:
    """Build point-in-time factor rows from daily bars.

    Features only use observations at or before the row date. forward_return is
    a research label from a later close and is never used to construct factors.
    """
    if isinstance(forward_horizon, bool) or forward_horizon < 1:
        raise ValueError("forward_horizon must be an integer >= 1")

    grouped = _normalized_bars(
        rows,
        date_field=date_field,
        ticker_field=ticker_field,
        close_field=close_field,
        volume_field=volume_field,
    )
    panel: list[dict[str, Any]] = []

    for ticker, bars in grouped.items():
        closes = [item["close"] for item in bars]
        volumes = [item["volume"] for item in bars]
        one_day_returns: list[float | None] = [None]
        for idx in range(1, len(closes)):
            one_day_returns.append(closes[idx] / closes[idx - 1] - 1.0)

        for idx, bar in enumerate(bars):
            future_idx = idx + forward_horizon
            if idx < 20 or future_idx >= len(bars):
                continue

            momentum_5 = closes[idx] / closes[idx - 5] - 1.0
            momentum_20 = closes[idx] / closes[idx - 20] - 1.0
            recent_returns = [
                value for value in one_day_returns[idx - 19 : idx + 1] if value is not None
            ]
            if len(recent_returns) < 20:
                continue

            row: dict[str, Any] = {
                "date": bar["date"],
                "ticker": ticker,
                "forward_return": closes[future_idx] / closes[idx] - 1.0,
                "momentum_5": momentum_5,
                "momentum_20": momentum_20,
                "reversal_5": -momentum_5,
                "low_volatility_20": -pstdev(recent_returns),
            }

            current_volume = volumes[idx]
            prior_volumes = volumes[idx - 20 : idx]
            if current_volume is not None and all(value is not None for value in prior_volumes):
                baseline = mean(float(value) for value in prior_volumes)
                if baseline > 0:
                    row["volume_surprise_20"] = current_volume / baseline - 1.0

            panel.append(row)

    panel.sort(key=lambda item: (item["date"], item["ticker"]))
    return panel


def available_factors(panel: Iterable[dict[str, Any]]) -> list[str]:
    present: set[str] = set()
    for row in panel:
        for factor in DEFAULT_FACTOR_NAMES:
            if factor in row:
                present.add(factor)
    return [factor for factor in DEFAULT_FACTOR_NAMES if factor in present]
