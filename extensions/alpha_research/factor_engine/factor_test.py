from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cross_section import evaluate_cross_section, finite_number  # noqa: E402


def evaluate_factor_rows(
    rows: list[dict[str, Any]],
    *,
    factor_field: str = "factor",
    direction: str = "high",
    top_fraction: float = 0.20,
    min_names_per_period: int = 3,
) -> dict[str, Any]:
    normalized_direction = direction.strip().lower()
    if normalized_direction not in {"high", "low"}:
        raise ValueError("direction must be high or low")

    prepared: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        factor = finite_number(row.get(factor_field), field=factor_field)
        copied["__cis_factor"] = factor if normalized_direction == "high" else -factor
        prepared.append(copied)

    summary = evaluate_cross_section(
        prepared,
        factor_field="__cis_factor",
        return_field="forward_return",
        top_fraction=top_fraction,
        min_names_per_period=min_names_per_period,
    )
    return {
        "schema_version": "cis.alpha_factor_test.v1",
        "engine": "cis_alpha_factor_test",
        "decision_authority": "none",
        "research_quality": "unreviewed",
        "factor_field": factor_field,
        "direction": normalized_direction,
        "summary": summary,
        "required_reviews": [
            "point_in_time_data_review",
            "survivorship_bias_review",
            "lookahead_leakage_review",
            "out_of_sample_review",
            "transaction_cost_review",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CIS cross-sectional factor diagnostic for Alpha Research")
    parser.add_argument("input_csv", help="CSV with date,ticker,factor,forward_return columns")
    parser.add_argument("--factor-field", default="factor")
    parser.add_argument("--direction", choices=("high", "low"), default="high")
    parser.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument("--min-names", type=int, default=3)
    parser.add_argument("--output")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    result = evaluate_factor_rows(
        rows,
        factor_field=args.factor_field,
        direction=args.direction,
        top_fraction=args.top_fraction,
        min_names_per_period=args.min_names,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
