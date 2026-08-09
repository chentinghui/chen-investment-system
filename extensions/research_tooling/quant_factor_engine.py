from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_FACTORS: dict[str, dict[str, Any]] = {
    "momentum_6m": {"weight": 0.15, "direction": "high"},
    "momentum_12m_ex1m": {"weight": 0.10, "direction": "high"},
    "revenue_growth": {"weight": 0.10, "direction": "high"},
    "eps_growth": {"weight": 0.10, "direction": "high"},
    "fcf_margin": {"weight": 0.10, "direction": "high"},
    "roe": {"weight": 0.05, "direction": "high"},
    "earnings_revision_90d": {"weight": 0.10, "direction": "high"},
    "valuation_fcf_yield": {"weight": 0.10, "direction": "high"},
    "relative_strength": {"weight": 0.10, "direction": "high"},
    "volatility": {"weight": 0.05, "direction": "low"},
    "max_drawdown_1y": {"weight": 0.05, "direction": "low", "transform": "abs"},
}
MIN_FACTOR_OBSERVATIONS = 2


def parse_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def transform_value(value: float, spec: dict[str, Any]) -> float:
    transform = spec.get("transform", "identity")
    if transform in {None, "identity"}:
        return value
    if transform == "abs":
        return abs(value)
    raise ValueError(f"unsupported factor transform: {transform}")


def average_percentile_ranks(values: dict[int, float]) -> dict[int, float]:
    if not values:
        return {}
    ordered = sorted(values.items(), key=lambda item: item[1])
    n = len(ordered)
    if n == 1:
        return {ordered[0][0]: 50.0}
    result: dict[int, float] = {}
    i = 0
    while i < n:
        j = i + 1
        while j < n and ordered[j][1] == ordered[i][1]:
            j += 1
        average_index = (i + (j - 1)) / 2.0
        pct = 100.0 * average_index / (n - 1)
        for k in range(i, j):
            result[ordered[k][0]] = pct
        i = j
    return result


def _normalize_factor_config(factors: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(factors, dict) or not factors:
        raise ValueError("factor config must contain a non-empty factors object")
    total = 0.0
    normalized: dict[str, dict[str, Any]] = {}
    for name, spec in factors.items():
        if not isinstance(spec, dict):
            raise ValueError(f"factor {name} spec must be an object")
        raw_weight = spec.get("weight")
        if isinstance(raw_weight, bool):
            raise ValueError(f"factor {name} weight must be a positive finite number")
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"factor {name} weight must be a positive finite number") from exc
        direction = str(spec.get("direction", "high")).lower()
        transform = str(spec.get("transform", "identity")).lower()
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError(f"factor {name} weight must be a positive finite number")
        if direction not in {"high", "low"}:
            raise ValueError(f"factor {name} direction must be high or low")
        if transform not in {"identity", "abs"}:
            raise ValueError(f"factor {name} transform must be identity or abs")
        normalized[name] = {"weight": weight, "direction": direction, "transform": transform}
        total += weight
    if not math.isfinite(total) or total <= 0:
        raise ValueError("factor weights must sum to a positive finite number")
    for spec in normalized.values():
        spec["weight"] = spec["weight"] / total
    return normalized


def load_factor_config(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return _normalize_factor_config(DEFAULT_FACTORS)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    factors = payload.get("factors", payload)
    return _normalize_factor_config(factors)


def validate_as_of(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise ValueError("input contains no rows")
    values = {(row.get("as_of") or "").strip() for row in rows}
    if "" in values:
        raise ValueError("every row must contain as_of for point-in-time ranking")
    if len(values) != 1:
        raise ValueError("all rows must share the same as_of for cross-sectional ranking")
    value = next(iter(values))
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("as_of must be YYYY-MM-DD") from exc
    return value


def _validate_cross_section(rows: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        ticker = str(row.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError(f"row {index} has empty ticker")
        if ticker in seen:
            raise ValueError(f"duplicate ticker in cross-section: {ticker}")
        seen.add(ticker)


def score_rows(
    rows: list[dict[str, str]],
    factors: dict[str, dict[str, Any]],
    min_coverage: float = 0.70,
    *,
    enforce_same_as_of: bool = True,
    min_factor_observations: int = MIN_FACTOR_OBSERVATIONS,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    if "ticker" not in rows[0]:
        raise ValueError("input CSV must contain ticker column")
    if not 0 < min_coverage <= 1:
        raise ValueError("min_coverage must be in (0, 1]")
    if isinstance(min_factor_observations, bool) or min_factor_observations < 2:
        raise ValueError("min_factor_observations must be an integer >= 2")
    if enforce_same_as_of:
        validate_as_of(rows)
    _validate_cross_section(rows)
    normalized_factors = _normalize_factor_config(factors)

    factor_ranks: dict[str, dict[int, float]] = {}
    factor_observations: dict[str, int] = {}
    for factor, spec in normalized_factors.items():
        available: dict[int, float] = {}
        for idx, row in enumerate(rows):
            parsed = parse_float(row.get(factor))
            if parsed is None:
                continue
            available[idx] = transform_value(parsed, spec)
        factor_observations[factor] = len(available)
        if len(available) < min_factor_observations:
            factor_ranks[factor] = {}
            continue
        ranks = average_percentile_ranks(available)
        if spec["direction"] == "low":
            ranks = {idx: 100.0 - score for idx, score in ranks.items()}
        factor_ranks[factor] = ranks

    total_weight = sum(float(spec["weight"]) for spec in normalized_factors.values())
    results: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        available_weight = 0.0
        weighted_sum = 0.0
        scores: dict[str, float] = {}
        for factor, spec in normalized_factors.items():
            if idx not in factor_ranks[factor]:
                continue
            weight = float(spec["weight"])
            score = factor_ranks[factor][idx]
            scores[factor] = round(score, 2)
            available_weight += weight
            weighted_sum += score * weight
        coverage = available_weight / total_weight if total_weight else 0.0
        if coverage < min_coverage or available_weight == 0:
            quant_score = None
            status = "insufficient"
        else:
            quant_score = round(weighted_sum / available_weight, 2)
            status = "ready" if coverage >= 0.85 else "provisional"
        results.append({
            "ticker": row["ticker"].strip().upper(),
            "as_of": row.get("as_of") or None,
            "quant_score": quant_score,
            "factor_coverage": round(coverage, 4),
            "status": status,
            "factor_scores": scores,
            "factor_observation_counts": factor_observations,
        })
    return sorted(results, key=lambda item: (
        item["quant_score"] is not None,
        item["quant_score"] if item["quant_score"] is not None else -1,
    ), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional CIS cross-sectional quant factor ranking engine")
    parser.add_argument("input_csv")
    parser.add_argument("--config", help="Optional factor config JSON")
    parser.add_argument("--min-coverage", type=float, default=0.70)
    parser.add_argument("--min-factor-observations", type=int, default=MIN_FACTOR_OBSERVATIONS)
    parser.add_argument("--universe", default="unspecified")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()
    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    factors = load_factor_config(args.config)
    as_of = validate_as_of(rows)
    payload = {
        "engine": "cis_quant_factor_ranking",
        "status": "experimental_uncalibrated_optional_extension",
        "universe": args.universe,
        "as_of": as_of,
        "min_factor_observations": args.min_factor_observations,
        "factor_config": factors,
        "results": score_rows(
            rows,
            factors,
            args.min_coverage,
            min_factor_observations=args.min_factor_observations,
        ),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
