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
        if value is None or isinstance(value, bool) or str(value).strip() == "":
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _required_float(value: Any, label: str, row_index: int) -> float:
    if _is_missing(value) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number at row {row_index}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number at row {row_index}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number at row {row_index}")
    return number


def _optional_float(value: Any, label: str, row_index: int) -> float | None:
    if _is_missing(value):
        return None
    return _required_float(value, label, row_index)


def _positive_horizon(value: Any, row_index: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"horizon_trading_days must be a positive integer at row {row_index}")
    if type(value) is int:
        horizon = value
    elif isinstance(value, str) and value.strip().isdigit():
        horizon = int(value.strip())
    else:
        raise ValueError(f"horizon_trading_days must be a positive integer at row {row_index}")
    if horizon <= 0:
        raise ValueError(f"horizon_trading_days must be a positive integer at row {row_index}")
    return horizon


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


def sample_status(count: int, *, independence_known: bool) -> str:
    if count < 30:
        return "insufficient_sample"
    if count < 100:
        return "exploratory_sample"
    if not independence_known:
        return "exploratory_independence_unverified"
    return "calibration_candidate"


def _sample_basis(items: list[dict[str, Any]]) -> tuple[int, bool, str]:
    ids = [str(item.get("research_id") or "").strip() for item in items]
    if ids and all(ids):
        unique_count = len(set(ids))
        return unique_count, True, "unique_research_id"
    return len(items), False, "row_count_research_id_missing"


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    realized = [item["realized_return"] for item in items]
    excess = [item["excess_return"] for item in items if item["excess_return"] is not None]
    sample_count, independence_known, basis = _sample_basis(items)
    return {
        "outcome_count": len(items),
        "independent_sample_count": sample_count,
        "sample_basis": basis,
        "sample_status": sample_status(sample_count, independence_known=independence_known),
        "mean_realized_return": mean(realized) if realized else None,
        "positive_return_rate": sum(1 for r in realized if r > 0) / len(realized) if realized else None,
        "mean_excess_return": mean(excess) if excess else None,
        "positive_excess_rate": sum(1 for r in excess if r > 0) / len(excess) if excess else None,
    }


def _dimension_diagnostics(items: list[dict[str, Any]]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for name in DIMENSIONS:
        pairs = [
            (item["dimensions"][name], item["excess_return"])
            for item in items
            if item["dimensions"][name] is not None and item["excess_return"] is not None
        ]
        xs = [float(x) for x, _ in pairs]
        ys = [float(y) for _, y in pairs]
        count, independence_known, basis = _sample_basis(
            [item for item in items if item["dimensions"][name] is not None and item["excess_return"] is not None]
        )
        diagnostics[name] = {
            "outcome_count": len(pairs),
            "independent_sample_count": count,
            "sample_basis": basis,
            "sample_status": sample_status(count, independence_known=independence_known),
            "excess_return_correlation": pearson(xs, ys) if pairs else None,
            "excess_return_rank_correlation": spearman(xs, ys) if pairs else None,
        }
    return diagnostics


def _diagnose_horizon(items: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(items)
    scores = [item["cis_score"] for item in items]
    returns = [item["realized_return"] for item in items]
    excess_pairs = [
        (item["cis_score"], item["excess_return"])
        for item in items
        if item["excess_return"] is not None
    ]
    by_score: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_sector: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_score[score_bucket(item["cis_score"])].append(item)
        by_regime[item["regime"]].append(item)
        by_sector[item["sector"]].append(item)
    return {
        **summary,
        "score_return_correlation": pearson(scores, returns),
        "score_excess_return_correlation": pearson(
            [x for x, _ in excess_pairs], [y for _, y in excess_pairs]
        ) if excess_pairs else None,
        "score_buckets": {k: summarize(v) for k, v in sorted(by_score.items())},
        "regimes": {k: summarize(v) for k, v in sorted(by_regime.items())},
        "sectors": {k: summarize(v) for k, v in sorted(by_sector.items())},
        "dimension_diagnostics": _dimension_diagnostics(items),
    }


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    seen_outcomes: set[tuple[str, int]] = set()
    excluded_missing_score_count = 0

    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"evaluation row {row_index} must be an object")

        realized = _required_float(row.get("realized_return"), "realized_return", row_index)
        if realized < -1:
            raise ValueError(f"realized_return cannot be below -100% at row {row_index}")

        benchmark = _optional_float(row.get("benchmark_return"), "benchmark_return", row_index)
        if benchmark is not None and benchmark < -1:
            raise ValueError(f"benchmark_return cannot be below -100% at row {row_index}")

        raw_horizon = row.get("horizon_trading_days", row.get("horizon_days"))
        horizon = _positive_horizon(raw_horizon, row_index)
        research_id = str(row.get("research_id") or "").strip() or None
        if research_id:
            duplicate_key = (research_id, horizon)
            if duplicate_key in seen_outcomes:
                raise ValueError(
                    f"duplicate evaluation outcome for research_id={research_id}, horizon={horizon}"
                )
            seen_outcomes.add(duplicate_key)

        if _is_missing(row.get("cis_score")):
            excluded_missing_score_count += 1
            continue
        score = _required_float(row.get("cis_score"), "cis_score", row_index)
        if not 0 <= score <= 100:
            raise ValueError(f"cis_score must be between 0 and 100 at row {row_index}")

        dimensions: dict[str, float | None] = {}
        for name in DIMENSIONS:
            raw_dimension = row.get(name) if name in row else row.get(f"dimension_{name}")
            value = _optional_float(raw_dimension, name, row_index)
            if value is not None and not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100 at row {row_index}")
            dimensions[name] = value

        parsed.append({
            "research_id": research_id,
            "ticker": str(row.get("ticker") or "").strip().upper() or None,
            "cis_score": score,
            "realized_return": realized,
            "excess_return": realized - benchmark if benchmark is not None else None,
            "horizon": str(horizon),
            "regime": str(row.get("regime") or "unknown"),
            "sector": str(row.get("sector") or "unknown"),
            "dimensions": dimensions,
        })

    by_horizon: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in parsed:
        by_horizon[item["horizon"]].append(item)

    independent_count, independence_known, sample_basis = _sample_basis(parsed)
    mixed_horizons = len(by_horizon) > 1
    horizon_diagnostics = {
        horizon: _diagnose_horizon(items)
        for horizon, items in sorted(by_horizon.items())
    }

    if not mixed_horizons and by_horizon:
        only = next(iter(horizon_diagnostics.values()))
        global_score_return = only["score_return_correlation"]
        global_score_excess = only["score_excess_return_correlation"]
        global_dimensions = only["dimension_diagnostics"]
    else:
        global_score_return = None
        global_score_excess = None
        global_dimensions = {}

    return {
        "status": "optional_calibration_report",
        "input_row_count": len(rows),
        "excluded_missing_score_count": excluded_missing_score_count,
        "sample_count": len(parsed),
        "outcome_count": len(parsed),
        "unique_research_count": independent_count,
        "sample_basis": sample_basis,
        "sample_status": sample_status(independent_count, independence_known=independence_known),
        "mixed_horizons": mixed_horizons,
        "score_return_correlation": global_score_return,
        "score_excess_return_correlation": global_score_excess,
        "dimension_diagnostics": global_dimensions,
        "horizons": {k: summarize(v) for k, v in sorted(by_horizon.items())},
        "horizon_diagnostics": horizon_diagnostics,
        "warning": (
            "Optional calibration only. Correlations are never pooled across different horizons; "
            "sample thresholds use unique research_id when available. Multiple horizons from one research "
            "are correlated outcomes, not independent experiments. Missing scores are reported as exclusions; "
            "malformed outcome data is rejected, never silently dropped. Never auto-rewrite CIS production weights."
        ),
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
    try:
        result = evaluate(rows)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
