from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Any, Iterable


def finite_number(value: Any, *, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def percentile_ranks(values: list[float]) -> list[float]:
    if not values:
        return []
    if len(values) == 1:
        return [0.5]
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        average_position = (i + (j - 1)) / 2.0
        percentile = average_position / (len(indexed) - 1)
        for cursor in range(i, j):
            result[indexed[cursor][0]] = percentile
        i = j
    return result


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    if len(x) < 2:
        return None
    x_mean = mean(x)
    y_mean = mean(y)
    x_dev = [value - x_mean for value in x]
    y_dev = [value - y_mean for value in y]
    x_ss = sum(value * value for value in x_dev)
    y_ss = sum(value * value for value in y_dev)
    if x_ss == 0 or y_ss == 0:
        return None
    covariance = sum(a * b for a, b in zip(x_dev, y_dev, strict=True))
    return covariance / math.sqrt(x_ss * y_ss)


def spearman(x: list[float], y: list[float]) -> float | None:
    return pearson(percentile_ranks(x), percentile_ranks(y))


def _normalize_rows(
    rows: Iterable[dict[str, Any]],
    *,
    date_field: str,
    ticker_field: str,
    factor_field: str,
    return_field: str,
) -> dict[str, list[tuple[str, float, float]]]:
    grouped: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
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
        factor = finite_number(row.get(factor_field), field=factor_field)
        forward_return = finite_number(row.get(return_field), field=return_field)
        if forward_return < -1:
            raise ValueError(f"{return_field} cannot be below -100%")
        grouped[date_value].append((ticker, factor, forward_return))
    return dict(grouped)


def evaluate_cross_section(
    rows: Iterable[dict[str, Any]],
    *,
    date_field: str = "date",
    ticker_field: str = "ticker",
    factor_field: str = "factor",
    return_field: str = "forward_return",
    top_fraction: float = 0.20,
    min_names_per_period: int = 3,
) -> dict[str, Any]:
    if not 0 < top_fraction <= 0.5:
        raise ValueError("top_fraction must be in (0, 0.5]")
    if isinstance(min_names_per_period, bool) or min_names_per_period < 3:
        raise ValueError("min_names_per_period must be an integer >= 3")

    grouped = _normalize_rows(
        rows,
        date_field=date_field,
        ticker_field=ticker_field,
        factor_field=factor_field,
        return_field=return_field,
    )
    period_results: list[dict[str, Any]] = []
    skipped_periods: list[str] = []

    for period in sorted(grouped):
        observations = grouped[period]
        if len(observations) < min_names_per_period:
            skipped_periods.append(period)
            continue
        factors = [item[1] for item in observations]
        returns = [item[2] for item in observations]
        ic = spearman(factors, returns)
        ordered = sorted(observations, key=lambda item: item[1])
        bucket_size = max(1, int(math.floor(len(ordered) * top_fraction)))
        if bucket_size * 2 > len(ordered):
            bucket_size = 1
        bottom = ordered[:bucket_size]
        top = ordered[-bucket_size:]
        spread = mean(item[2] for item in top) - mean(item[2] for item in bottom)
        period_results.append(
            {
                "date": period,
                "names": len(observations),
                "rank_ic": ic,
                "top_bottom_spread": spread,
                "bucket_size": bucket_size,
            }
        )

    valid_ics = [row["rank_ic"] for row in period_results if row["rank_ic"] is not None]
    spreads = [row["top_bottom_spread"] for row in period_results]
    return {
        "periods": len(period_results),
        "observations": sum(row["names"] for row in period_results),
        "mean_rank_ic": mean(valid_ics) if valid_ics else None,
        "rank_ic_hit_rate": (
            sum(1 for value in valid_ics if value > 0) / len(valid_ics) if valid_ics else None
        ),
        "mean_top_bottom_spread": mean(spreads) if spreads else None,
        "skipped_periods": skipped_periods,
        "period_results": period_results,
    }
