from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cross_section import evaluate_cross_section, spearman  # noqa: E402
from factor_library import available_factors, build_factor_panel  # noqa: E402


def _factor_rows(panel: Iterable[dict[str, Any]], factor: str) -> list[dict[str, Any]]:
    return [
        {
            "date": row["date"],
            "ticker": row["ticker"],
            "factor": row[factor],
            "forward_return": row["forward_return"],
        }
        for row in panel
        if factor in row
    ]


def chronological_split(
    rows: list[dict[str, Any]],
    *,
    test_fraction: float = 0.30,
    min_test_periods: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be in (0, 1)")
    if isinstance(min_test_periods, bool) or min_test_periods < 1:
        raise ValueError("min_test_periods must be an integer >= 1")

    dates = sorted({str(row["date"]) for row in rows})
    if len(dates) < min_test_periods + 1:
        raise ValueError("not enough periods for chronological OOS split")

    test_count = max(min_test_periods, int(math.ceil(len(dates) * test_fraction)))
    if test_count >= len(dates):
        test_count = len(dates) - 1
    split_at = len(dates) - test_count
    train_dates = set(dates[:split_at])
    test_dates = set(dates[split_at:])
    train = [row for row in rows if str(row["date"]) in train_dates]
    test = [row for row in rows if str(row["date"]) in test_dates]
    return train, test, {
        "train_start": dates[0],
        "train_end": dates[split_at - 1],
        "test_start": dates[split_at],
        "test_end": dates[-1],
        "train_periods": split_at,
        "test_periods": test_count,
    }


def estimate_long_short_turnover(
    rows: list[dict[str, Any]],
    *,
    top_fraction: float = 0.20,
) -> float | None:
    if not 0 < top_fraction <= 0.5:
        raise ValueError("top_fraction must be in (0, 0.5]")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["date"])].append(row)

    previous: dict[str, float] | None = None
    turnovers: list[float] = []
    for date_value in sorted(grouped):
        observations = sorted(grouped[date_value], key=lambda item: float(item["factor"]))
        if len(observations) < 3:
            continue
        bucket = max(1, int(math.floor(len(observations) * top_fraction)))
        if bucket * 2 > len(observations):
            bucket = 1
        bottom = observations[:bucket]
        top = observations[-bucket:]
        weights: dict[str, float] = {}
        for row in top:
            weights[str(row["ticker"])] = 1.0 / len(top)
        for row in bottom:
            weights[str(row["ticker"])] = -1.0 / len(bottom)

        if previous is not None:
            names = set(previous) | set(weights)
            turnovers.append(
                0.5
                * sum(
                    abs(weights.get(name, 0.0) - previous.get(name, 0.0))
                    for name in names
                )
            )
        previous = weights
    return mean(turnovers) if turnovers else None


def cost_sensitivity(
    gross_period_return: float | None,
    turnover: float | None,
    *,
    cost_bps: tuple[int, ...] = (0, 5, 10, 20),
) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for bps in cost_bps:
        if gross_period_return is None or turnover is None:
            result[f"{bps}bps"] = None
        else:
            result[f"{bps}bps"] = gross_period_return - turnover * (bps / 10000.0)
    return result


def factor_correlations(
    panel: list[dict[str, Any]],
    factors: list[str],
) -> dict[str, dict[str, float | None]]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in panel:
        by_date[str(row["date"])].append(row)

    matrix: dict[str, dict[str, float | None]] = {factor: {} for factor in factors}
    for left in factors:
        for right in factors:
            if left == right:
                matrix[left][right] = 1.0
                continue
            values: list[float] = []
            for date_value in sorted(by_date):
                paired = [
                    (float(row[left]), float(row[right]))
                    for row in by_date[date_value]
                    if left in row and right in row
                ]
                if len(paired) < 3:
                    continue
                correlation = spearman(
                    [item[0] for item in paired],
                    [item[1] for item in paired],
                )
                if correlation is not None:
                    values.append(correlation)
            matrix[left][right] = mean(values) if values else None
    return matrix


def _quality_status(
    oos: dict[str, Any],
    net_10bps: float | None,
) -> str:
    ic = oos.get("mean_rank_ic")
    hit = oos.get("rank_ic_hit_rate")
    periods = int(oos.get("periods") or 0)
    if periods < 3 or ic is None or hit is None:
        return "insufficient_oos"
    if ic >= 0.02 and hit >= 0.50 and net_10bps is not None and net_10bps > 0:
        return "candidate_for_cis_validation"
    return "research_only"


def mine_alpha_candidates(
    bars: list[dict[str, Any]],
    *,
    forward_horizon: int = 1,
    test_fraction: float = 0.30,
    top_fraction: float = 0.20,
    redundancy_threshold: float = 0.80,
) -> dict[str, Any]:
    if not 0 <= redundancy_threshold <= 1:
        raise ValueError("redundancy_threshold must be in [0, 1]")

    panel = build_factor_panel(bars, forward_horizon=forward_horizon)
    factors = available_factors(panel)
    if not panel or not factors:
        raise ValueError("not enough history to build lightweight factors")

    research: list[dict[str, Any]] = []
    for factor in factors:
        rows = _factor_rows(panel, factor)
        train, test, split = chronological_split(rows, test_fraction=test_fraction)
        train_summary = evaluate_cross_section(
            train,
            top_fraction=top_fraction,
            min_names_per_period=3,
        )
        test_summary = evaluate_cross_section(
            test,
            top_fraction=top_fraction,
            min_names_per_period=3,
        )
        turnover = estimate_long_short_turnover(test, top_fraction=top_fraction)
        costs = cost_sensitivity(test_summary.get("mean_top_bottom_spread"), turnover)
        research.append(
            {
                "factor": factor,
                "split": split,
                "in_sample": train_summary,
                "out_of_sample": test_summary,
                "estimated_oos_turnover": turnover,
                "oos_cost_sensitivity": costs,
                "screen_status": _quality_status(test_summary, costs.get("10bps")),
                "redundant_with": None,
            }
        )

    correlations = factor_correlations(panel, factors)
    ranked = sorted(
        research,
        key=lambda item: (
            item["screen_status"] == "candidate_for_cis_validation",
            item["out_of_sample"].get("mean_rank_ic")
            if item["out_of_sample"].get("mean_rank_ic") is not None
            else float("-inf"),
            item["oos_cost_sensitivity"].get("10bps")
            if item["oos_cost_sensitivity"].get("10bps") is not None
            else float("-inf"),
        ),
        reverse=True,
    )

    kept: list[str] = []
    for item in ranked:
        factor = item["factor"]
        for stronger in kept:
            corr = correlations.get(factor, {}).get(stronger)
            if corr is not None and abs(corr) >= redundancy_threshold:
                item["redundant_with"] = stronger
                if item["screen_status"] == "candidate_for_cis_validation":
                    item["screen_status"] = "redundant_candidate"
                break
        if item["redundant_with"] is None:
            kept.append(factor)

    return {
        "schema_version": "cis.lightweight_alpha_research.v1",
        "engine": "cis_lightweight_alpha_miner",
        "research_status": "unreviewed",
        "decision_authority": "none",
        "input": {
            "bars": len(bars),
            "panel_rows": len(panel),
            "factors_tested": len(factors),
            "forward_horizon": forward_horizon,
            "test_fraction": test_fraction,
            "top_fraction": top_fraction,
        },
        "factors": ranked,
        "factor_correlations": correlations,
        "required_reviews": [
            "point_in_time_data_review",
            "survivorship_bias_review",
            "lookahead_leakage_review",
            "walk_forward_review",
            "transaction_cost_and_capacity_review",
            "factor_exposure_regression",
            "portfolio_risk_review",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CIS lightweight Alpha Research: daily bars -> factor candidates -> OOS diagnostics"
    )
    parser.add_argument("input_csv", help="CSV with date,ticker,close and optional volume")
    parser.add_argument("--forward-horizon", type=int, default=1)
    parser.add_argument("--test-fraction", type=float, default=0.30)
    parser.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument("--redundancy-threshold", type=float, default=0.80)
    parser.add_argument("--output")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        bars = list(csv.DictReader(handle))
    result = mine_alpha_candidates(
        bars,
        forward_horizon=args.forward_horizon,
        test_fraction=args.test_fraction,
        top_fraction=args.top_fraction,
        redundancy_threshold=args.redundancy_threshold,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
