from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


MIN_HISTORY_OBSERVATIONS = 20


def _positive(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive number")
    return number


def _premium(price: Any, iopv: Any, label: str) -> float:
    return _positive(price, f"{label}.price") / _positive(iopv, f"{label}.iopv") - 1


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _round_pct(value: float) -> float:
    return round(value * 100, 4)


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError("current must be an object with price and iopv")

    current_premium = _premium(current.get("price"), current.get("iopv"), "current")
    result: dict[str, Any] = {
        "code": payload.get("code"),
        "as_of": payload.get("as_of"),
        "current_premium_pct": _round_pct(current_premium),
        "entry_premium_pct": None,
        "premium_change_pp": None,
        "history": {
            "valid_observations": 0,
            "required_observations": MIN_HISTORY_OBSERVATIONS,
            "status": "insufficient_history",
        },
        "note": "Quantitative premium context only; no trade action is generated.",
    }

    entry = payload.get("entry")
    if entry is not None:
        if not isinstance(entry, dict):
            raise ValueError("entry must be an object with price and iopv")
        entry_premium = _premium(entry.get("price"), entry.get("iopv"), "entry")
        result["entry_premium_pct"] = _round_pct(entry_premium)
        result["premium_change_pp"] = round((current_premium - entry_premium) * 100, 4)

    history_rows = payload.get("history", [])
    if not isinstance(history_rows, list):
        raise ValueError("history must be an array")

    historical_premiums: list[float] = []
    for index, row in enumerate(history_rows):
        if not isinstance(row, dict):
            raise ValueError(f"history[{index}] must be an object")
        historical_premiums.append(
            _premium(row.get("price"), row.get("iopv"), f"history[{index}]")
        )

    if len(historical_premiums) < MIN_HISTORY_OBSERVATIONS:
        result["history"]["valid_observations"] = len(historical_premiums)
        return result

    ordered = sorted(historical_premiums)
    less_or_equal = sum(value <= current_premium for value in ordered)
    percentile = less_or_equal / len(ordered)
    p25 = _quantile(ordered, 0.25)
    p75 = _quantile(ordered, 0.75)
    if current_premium < p25:
        regime = "below_historical_interquartile_range"
    elif current_premium > p75:
        regime = "above_historical_interquartile_range"
    else:
        regime = "within_historical_interquartile_range"
    result["history"] = {
        "valid_observations": len(ordered),
        "required_observations": MIN_HISTORY_OBSERVATIONS,
        "status": "ready",
        "minimum_premium_pct": _round_pct(ordered[0]),
        "p25_premium_pct": _round_pct(p25),
        "median_premium_pct": _round_pct(statistics.median(ordered)),
        "p75_premium_pct": _round_pct(p75),
        "maximum_premium_pct": _round_pct(ordered[-1]),
        "current_percentile_pct": round(percentile * 100, 2),
        "premium_regime": regime,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate current, entry, and historical ETF premium context."
    )
    parser.add_argument("input", type=Path, help="UTF-8 JSON input file")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(analyze(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
