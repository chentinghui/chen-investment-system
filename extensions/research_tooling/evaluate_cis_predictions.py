from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from prediction_ledger import materialize

DIMENSIONS = (
    "fundamentals", "growth", "valuation", "industry_competitive",
    "technical", "catalyst_macro", "positioning", "risk_resilience",
)


def parse_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar, ybar = mean(xs), mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xvar = sum((x - xbar) ** 2 for x in xs)
    yvar = sum((y - ybar) ** 2 for y in ys)
    denominator = math.sqrt(xvar * yvar)
    return numerator / denominator if denominator else None


def _ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[indexed[k][0]] = avg
        i = j
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    return pearson(_ranks(xs), _ranks(ys))


def score_bucket(score: float) -> str:
    if score >= 85:
        return "85-100"
    if score >= 75:
        return "75-84"
    if score >= 60:
        return "60-74"
    return "0-59"


def sample_status(count: int) -> str:
    if count < 30:
        return "insufficient_sample"
    if count < 100:
        return "exploratory_sample"
    return "calibration_candidate"


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    realized = [item["realized_return"] for item in items]
    excess = [item["excess_return"] for item in items if item["excess_return"] is not None]
    return {
        "count": len(items),
        "sample_status": sample_status(len(items)),
        "mean_realized_return": mean(realized) if realized else None,
        "positive_return_rate": sum(1 for r in realized if r > 0) / len(realized) if realized else None,
        "mean_excess_return": mean(excess) if excess else None,
        "positive_excess_rate": sum(1 for r in excess if r > 0) / len(excess) if excess else None,
    }


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    for row in rows:
        score = parse_float(row.get("cis_score"))
        realized = parse_float(row.get("realized_return"))
        benchmark = parse_float(row.get("benchmark_return"))
        if score is None or realized is None:
            continue
        parsed.append({
            "cis_score": score,
            "realized_return": realized,
            "excess_return": realized - benchmark if benchmark is not None else None,
            "horizon": str(row.get("horizon_trading_days", row.get("horizon_days", "unknown"))),
            "regime": str(row.get("regime") or "unknown"),
            "sector": str(row.get("sector") or "unknown"),
            "dimensions": {
                name: parse_float(row.get(name) if name in row else row.get(f"dimension_{name}"))
                for name in DIMENSIONS
            },
        })

    by_score: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_horizon: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_sector: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in parsed:
        by_score[score_bucket(item["cis_score"])].append(item)
        by_horizon[item["horizon"]].append(item)
        by_regime[item["regime"]].append(item)
        by_sector[item["sector"]].append(item)

    scores = [item["cis_score"] for item in parsed]
    returns = [item["realized_return"] for item in parsed]
    excess_pairs = [(item["cis_score"], item["excess_return"]) for item in parsed if item["excess_return"] is not None]

    dimension_diagnostics: dict[str, Any] = {}
    for name in DIMENSIONS:
        pairs = [(item["dimensions"][name], item["excess_return"]) for item in parsed if item["dimensions"][name] is not None and item["excess_return"] is not None]
        xs = [float(x) for x, _ in pairs]
        ys = [float(y) for _, y in pairs]
        dimension_diagnostics[name] = {
            "sample_count": len(pairs),
            "sample_status": sample_status(len(pairs)),
            "excess_return_correlation": pearson(xs, ys) if pairs else None,
            "excess_return_rank_correlation": spearman(xs, ys) if pairs else None,
        }

    return {
        "status": "optional_calibration_report",
        "sample_count": len(parsed),
        "sample_status": sample_status(len(parsed)),
        "score_return_correlation": pearson(scores, returns),
        "score_excess_return_correlation": pearson([x for x, _ in excess_pairs], [y for _, y in excess_pairs]) if excess_pairs else None,
        "score_buckets": {k: summarize(v) for k, v in sorted(by_score.items())},
        "horizons": {k: summarize(v) for k, v in sorted(by_horizon.items())},
        "regimes": {k: summarize(v) for k, v in sorted(by_regime.items())},
        "sectors": {k: summarize(v) for k, v in sorted(by_sector.items())},
        "dimension_diagnostics": dimension_diagnostics,
        "warning": "Optional calibration only. Never auto-rewrite CIS production weights or block normal CIS analysis.",
    }


def rows_from_ledger(ledger: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prediction in materialize(ledger):
        dimensions = prediction.get("dimension_scores") or {}
        for outcome in prediction.get("outcomes", []):
            row = {
                "research_id": prediction.get("research_id"),
                "ticker": prediction.get("ticker"),
                "cis_score": prediction.get("cis_score"),
                "regime": prediction.get("regime", "unknown"),
                "sector": prediction.get("sector", "unknown"),
                "horizon_trading_days": outcome.get("horizon_trading_days"),
                "realized_return": outcome.get("realized_return"),
                "benchmark_return": outcome.get("benchmark_return"),
            }
            for name in DIMENSIONS:
                row[name] = dimensions.get(name)
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional CIS historical prediction evaluator")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-csv")
    source.add_argument("--ledger", type=Path)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.ledger:
        rows = rows_from_ledger(args.ledger)
    else:
        with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    text = json.dumps(evaluate(rows), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
