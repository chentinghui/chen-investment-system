from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

DIMENSIONS = (
    "fundamentals",
    "growth",
    "valuation",
    "industry_competitive",
    "technical",
    "catalyst_macro",
    "positioning",
    "risk_resilience",
)


def parse_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def score_bucket(score: float) -> str:
    if score >= 85:
        return "85-100"
    if score >= 75:
        return "75-84"
    if score >= 60:
        return "60-74"
    return "0-59"


def horizon_bucket(days: float | None) -> str:
    if days is None:
        return "unknown"
    if days <= 30:
        return "0-30d"
    if days <= 90:
        return "31-90d"
    if days <= 365:
        return "91-365d"
    return "365d+"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar, ybar = mean(xs), mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xvar = sum((x - xbar) ** 2 for x in xs)
    yvar = sum((y - ybar) ** 2 for y in ys)
    denominator = math.sqrt(xvar * yvar)
    return numerator / denominator if denominator else None


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    realized = [item["realized_return"] for item in items]
    excess = [item["excess_return"] for item in items if item["excess_return"] is not None]
    drawdowns = [item["max_drawdown"] for item in items if item.get("max_drawdown") is not None]
    falsifiers = [item["falsifier_triggered"] for item in items if item.get("falsifier_triggered") is not None]
    return {
        "count": len(items),
        "mean_realized_return": mean(realized) if realized else None,
        "positive_return_rate": sum(1 for r in realized if r > 0) / len(realized) if realized else None,
        "mean_excess_return": mean(excess) if excess else None,
        "positive_excess_rate": sum(1 for r in excess if r > 0) / len(excess) if excess else None,
        "mean_max_drawdown": mean(drawdowns) if drawdowns else None,
        "falsifier_trigger_rate": sum(1 for x in falsifiers if x) / len(falsifiers) if falsifiers else None,
    }


def parse_bool(value: Any) -> bool | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def evaluate(rows: list[dict[str, str]]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    for row in rows:
        score = parse_float(row.get("cis_score"))
        realized = parse_float(row.get("realized_return"))
        benchmark = parse_float(row.get("benchmark_return"))
        if score is None or realized is None:
            continue
        dimensions = {
            name: parse_float(row.get(name) if name in row else row.get(f"dimension_{name}"))
            for name in DIMENSIONS
        }
        parsed.append(
            {
                "cis_score": score,
                "realized_return": realized,
                "excess_return": realized - benchmark if benchmark is not None else None,
                "regime": (row.get("regime") or "unknown").strip() or "unknown",
                "horizon_days": parse_float(row.get("horizon_days")),
                "max_drawdown": parse_float(row.get("max_drawdown_during_horizon")),
                "falsifier_triggered": parse_bool(row.get("falsifier_triggered")),
                "dimensions": dimensions,
            }
        )

    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_horizon: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in parsed:
        by_bucket[score_bucket(item["cis_score"])].append(item)
        by_regime[item["regime"]].append(item)
        by_horizon[horizon_bucket(item["horizon_days"])].append(item)

    scores = [item["cis_score"] for item in parsed]
    returns = [item["realized_return"] for item in parsed]
    excess_pairs = [(item["cis_score"], item["excess_return"]) for item in parsed if item["excess_return"] is not None]

    dimension_diagnostics: dict[str, Any] = {}
    for name in DIMENSIONS:
        raw_pairs = [
            (item["dimensions"][name], item["realized_return"], item["excess_return"])
            for item in parsed
            if item["dimensions"][name] is not None
        ]
        excess_dimension_pairs = [(float(x), float(excess)) for x, _, excess in raw_pairs if excess is not None]
        dimension_diagnostics[name] = {
            "sample_count": len(raw_pairs),
            "return_correlation": pearson(
                [float(x) for x, _, _ in raw_pairs],
                [float(ret) for _, ret, _ in raw_pairs],
            ) if raw_pairs else None,
            "excess_return_correlation": pearson(
                [x for x, _ in excess_dimension_pairs],
                [y for _, y in excess_dimension_pairs],
            ) if excess_dimension_pairs else None,
        }

    return {
        "status": "calibration_report",
        "sample_count": len(parsed),
        "score_return_correlation": pearson(scores, returns),
        "score_excess_return_correlation": pearson(
            [x for x, _ in excess_pairs], [y for _, y in excess_pairs]
        ) if excess_pairs else None,
        "score_buckets": {bucket: summarize(items) for bucket, items in sorted(by_bucket.items())},
        "regimes": {regime: summarize(items) for regime, items in sorted(by_regime.items())},
        "horizons": {bucket: summarize(items) for bucket, items in sorted(by_horizon.items())},
        "dimension_diagnostics": dimension_diagnostics,
        "warning": "Calibration diagnostics only. Do not automatically rewrite CIS production weights or thresholds.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate historical CIS predictions")
    parser.add_argument("input_csv", help="CSV with cis_score,realized_return and optional horizon/dimension fields")
    parser.add_argument("--output")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {"cis_score", "realized_return"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"input CSV must contain: {', '.join(sorted(required))}")

    text = json.dumps(evaluate(rows), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
