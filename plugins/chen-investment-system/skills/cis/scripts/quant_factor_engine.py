from __future__ import annotations

import argparse
import csv
import json
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
    "max_drawdown_1y": {"weight": 0.05, "direction": "low"},
}


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def average_percentile_ranks(values: dict[int, float]) -> dict[int, float]:
    """Return 0-100 percentile ranks using average rank for ties."""
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


def load_factor_config(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return DEFAULT_FACTORS
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    factors = payload.get("factors", payload)
    if not isinstance(factors, dict) or not factors:
        raise ValueError("factor config must contain a non-empty factors object")
    total = 0.0
    normalized: dict[str, dict[str, Any]] = {}
    for name, spec in factors.items():
        weight = float(spec["weight"])
        direction = str(spec.get("direction", "high")).lower()
        if weight <= 0:
            raise ValueError(f"factor {name} weight must be positive")
        if direction not in {"high", "low"}:
            raise ValueError(f"factor {name} direction must be high or low")
        normalized[name] = {"weight": weight, "direction": direction}
        total += weight
    for spec in normalized.values():
        spec["weight"] = spec["weight"] / total
    return normalized


def score_rows(
    rows: list[dict[str, str]],
    factors: dict[str, dict[str, Any]],
    min_coverage: float = 0.70,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    if "ticker" not in rows[0]:
        raise ValueError("input CSV must contain ticker column")

    factor_ranks: dict[str, dict[int, float]] = {}
    for factor, spec in factors.items():
        available = {
            idx: value
            for idx, row in enumerate(rows)
            if (value := parse_float(row.get(factor))) is not None
        }
        ranks = average_percentile_ranks(available)
        if spec["direction"] == "low":
            ranks = {idx: 100.0 - score for idx, score in ranks.items()}
        factor_ranks[factor] = ranks

    total_weight = sum(float(spec["weight"]) for spec in factors.values())
    results: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        available_weight = 0.0
        weighted_sum = 0.0
        scores: dict[str, float] = {}
        for factor, spec in factors.items():
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

        results.append(
            {
                "ticker": row["ticker"],
                "as_of": row.get("as_of") or None,
                "quant_score": quant_score,
                "factor_coverage": round(coverage, 4),
                "status": status,
                "factor_scores": scores,
            }
        )

    return sorted(
        results,
        key=lambda item: (
            item["quant_score"] is not None,
            item["quant_score"] if item["quant_score"] is not None else -1,
        ),
        reverse=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CIS cross-sectional quant factor engine")
    parser.add_argument("input_csv")
    parser.add_argument("--config", help="Optional factor config JSON")
    parser.add_argument("--min-coverage", type=float, default=0.70)
    parser.add_argument("--universe", default="unspecified")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    factors = load_factor_config(args.config)
    payload = {
        "engine": "cis_quant_research",
        "status": "experimental_uncalibrated",
        "universe": args.universe,
        "factor_config": factors,
        "results": score_rows(rows, factors, args.min_coverage),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
