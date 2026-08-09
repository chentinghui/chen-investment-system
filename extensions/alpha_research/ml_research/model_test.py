from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


FACTOR_ENGINE_DIR = Path(__file__).resolve().parents[1] / "factor_engine"
if str(FACTOR_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(FACTOR_ENGINE_DIR))

from cross_section import evaluate_cross_section, finite_number  # noqa: E402


ALLOWED_SPLITS = {"train", "validation", "test"}


def evaluate_model_rows(
    rows: list[dict[str, Any]],
    *,
    prediction_field: str = "prediction",
    split_field: str = "split",
    require_test: bool = True,
    min_names_per_period: int = 3,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in ALLOWED_SPLITS}
    for index, row in enumerate(rows):
        split = str(row.get(split_field) or "").strip().lower()
        if split not in ALLOWED_SPLITS:
            raise ValueError(f"row {index} has invalid split: {split!r}")
        copied = dict(row)
        copied["__cis_prediction"] = finite_number(row.get(prediction_field), field=prediction_field)
        grouped[split].append(copied)

    if require_test and not grouped["test"]:
        raise ValueError("test split is required for out-of-sample model validation")

    diagnostics: dict[str, Any] = {}
    for split in ("train", "validation", "test"):
        split_rows = grouped[split]
        diagnostics[split] = (
            evaluate_cross_section(
                split_rows,
                factor_field="__cis_prediction",
                return_field="forward_return",
                min_names_per_period=min_names_per_period,
            )
            if split_rows
            else None
        )

    test_summary = diagnostics.get("test") or {}
    test_periods = int(test_summary.get("periods", 0) or 0)
    if not grouped["test"]:
        oos_status = "missing"
    elif test_periods < 3:
        oos_status = "insufficient"
    else:
        oos_status = "present"

    return {
        "schema_version": "cis.alpha_model_test.v1",
        "engine": "cis_alpha_model_test",
        "decision_authority": "none",
        "research_quality": "unreviewed",
        "model_training_performed": False,
        "prediction_field": prediction_field,
        "oos_status": oos_status,
        "split_diagnostics": diagnostics,
        "required_reviews": [
            "feature_timestamp_and_leakage_review",
            "purged_or_non_overlapping_split_review_when_applicable",
            "hyperparameter_selection_bias_review",
            "regime_stability_review",
            "transaction_cost_and_capacity_review",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate externally generated ML predictions without fitting a model inside CIS"
    )
    parser.add_argument("input_csv", help="CSV with split,date,ticker,prediction,forward_return")
    parser.add_argument("--prediction-field", default="prediction")
    parser.add_argument("--split-field", default="split")
    parser.add_argument("--allow-missing-test", action="store_true")
    parser.add_argument("--min-names", type=int, default=3)
    parser.add_argument("--output")
    args = parser.parse_args()

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    result = evaluate_model_rows(
        rows,
        prediction_field=args.prediction_field,
        split_field=args.split_field,
        require_test=not args.allow_missing_test,
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
