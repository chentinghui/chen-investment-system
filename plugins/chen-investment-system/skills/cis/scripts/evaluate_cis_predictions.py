from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def parse_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
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
    return {
        "count": len(items),
        "mean_realized_return": mean(realized) if realized else None,
        "positive_return_rate": sum(1 for r in realized if r > 0) / len(realized) if realized else None,
        "mean_excess_return": mean(excess) if excess else None,
        "positive_excess_rate": sum(1 for r in excess if r > 0) / len(excess) if excess else None,
    }


def evaluate(rows: list[dict[str, str]]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    for row in rows:
        score = parse_float(row.get("cis_score"))
        realized = parse_float(row.get("realized_return"))
        benchmark = parse_float(row.get("benchmark_return"))
        if score is None or realized is None:
            continue
        parsed.append(
            {
                "cis_score": score,
                "realized_return": realized,
                "excess_return": realized - benchmark if benchmark is not None else None,
                "regime": (row.get("regime") or "unknown").strip() or "unknown",
            }
        )

    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in parsed:
        by_bucket[score_bucket(item["cis_score"])].append(item)
        by_regime[item["regime"]].append(item)

    scores = [item["cis_score"] for item in parsed]
    returns = [item["realized_return"] for item in parsed]
    excess_pairs = [(item["cis_score"], item["excess_return"]) for item in parsed if item["excess_return"] is not None]

    return {
        "status": "calibration_report",
        "sample_count": len(parsed),
        "score_return_correlation": pearson(scores, returns),
        "score_excess_return_correlation": pearson(
            [x for x, _ in excess_pairs], [y for _, y in excess_pairs]
        ) if excess_pairs else None,
        "score_buckets": {bucket: summarize(items) for bucket, items in sorted(by_bucket.items())},
        "regimes": {regime: summarize(items) for regime, items in sorted(by_regime.items())},
        "warning": "This report diagnoses calibration only. It must not automatically rewrite CIS production weights or thresholds.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate historical CIS predictions")
    parser.add_argument("input_csv", help="CSV with cis_score,realized_return[,benchmark_return,regime]")
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
