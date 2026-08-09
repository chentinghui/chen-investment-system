from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "cis.alpha_candidate.v1"
SOURCE = "worldquant_brain"
FORBIDDEN_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "brokerage",
    "live_order",
    "live_trade",
    "account_id",
)


@dataclass(frozen=True)
class ValidationPolicy:
    min_sharpe: float = 1.25
    min_turnover: float = 0.01
    max_turnover: float = 0.70
    min_fitness: float = 1.0
    min_annual_return: float = 0.0
    max_abs_drawdown: float = 0.50


def _finite_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _scan_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                hits.append(f"{path}.{key}")
            hits.extend(_scan_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_scan_forbidden_keys(child, f"{path}[{index}]"))
    return hits


def _validate_structure(candidate: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if candidate.get("schema_version") != SCHEMA_VERSION:
        failures.append("schema_version must equal cis.alpha_candidate.v1")
    if candidate.get("source") != SOURCE:
        failures.append("source must equal worldquant_brain")
    if candidate.get("decision_authority") != "none":
        failures.append("decision_authority must equal none")
    if candidate.get("research_status") != "unreviewed":
        failures.append("imported alpha must start as research_status=unreviewed")
    if not str(candidate.get("alpha_id") or "").strip():
        failures.append("alpha_id is required")
    if not str(candidate.get("expression") or "").strip():
        failures.append("expression is required")

    settings = candidate.get("settings")
    if not isinstance(settings, dict):
        failures.append("settings must be an object")
    else:
        for field in ("region", "universe", "delay"):
            if settings.get(field) in (None, ""):
                failures.append(f"settings.{field} is required for reproducible validation")
        delay = settings.get("delay")
        if delay is not None and (isinstance(delay, bool) or not isinstance(delay, int) or delay < 0):
            failures.append("settings.delay must be a non-negative integer")

    if not isinstance(candidate.get("metrics"), dict):
        failures.append("metrics must be an object")

    forbidden = _scan_forbidden_keys(candidate)
    if forbidden:
        failures.append("candidate contains forbidden credential/live-trading fields: " + ", ".join(forbidden))
    return failures


def validate_candidate(
    candidate: dict[str, Any],
    policy: ValidationPolicy = ValidationPolicy(),
) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a JSON object")

    structural_failures = _validate_structure(candidate)
    metrics = candidate.get("metrics") if isinstance(candidate.get("metrics"), dict) else {}
    sharpe = _finite_number(metrics.get("sharpe"))
    turnover = _finite_number(metrics.get("turnover"))
    fitness = _finite_number(metrics.get("fitness"))
    annual_return = _finite_number(metrics.get("annual_return"))
    max_drawdown = _finite_number(metrics.get("max_drawdown"))

    failed_checks: list[str] = []
    warnings: list[str] = []
    missing_core_metrics: list[str] = []

    if sharpe is None:
        missing_core_metrics.append("sharpe")
    elif sharpe < policy.min_sharpe:
        failed_checks.append(f"sharpe<{policy.min_sharpe}")

    if turnover is None:
        missing_core_metrics.append("turnover")
    elif not policy.min_turnover <= turnover <= policy.max_turnover:
        failed_checks.append(f"turnover outside [{policy.min_turnover}, {policy.max_turnover}]")

    if fitness is None:
        warnings.append("fitness unavailable; do not treat screen as fully comparable to BRAIN quality gates")
    elif fitness < policy.min_fitness:
        failed_checks.append(f"fitness<{policy.min_fitness}")

    if annual_return is None:
        warnings.append("annual_return unavailable")
    elif annual_return <= policy.min_annual_return:
        failed_checks.append(f"annual_return<={policy.min_annual_return}")

    if max_drawdown is None:
        warnings.append("max_drawdown unavailable")
    elif abs(max_drawdown) > policy.max_abs_drawdown:
        failed_checks.append(f"abs(max_drawdown)>{policy.max_abs_drawdown}")

    if structural_failures:
        screen_status = "invalid"
    elif missing_core_metrics:
        screen_status = "insufficient"
    elif failed_checks:
        screen_status = "rejected_screen"
    else:
        screen_status = "candidate_for_cis_validation"

    return {
        "schema_version": "cis.alpha_validation.v1",
        "source": SOURCE,
        "alpha_id": candidate.get("alpha_id"),
        "screen_status": screen_status,
        "decision_authority": "none",
        "structural_failures": structural_failures,
        "missing_core_metrics": missing_core_metrics,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "required_next_reviews": [
            "economic_rationale_review",
            "data_leakage_and_lookahead_review",
            "out_of_sample_validation",
            "turnover_cost_and_capacity_review",
            "correlation_and_diversification_review",
        ],
        "policy": {
            "min_sharpe": policy.min_sharpe,
            "min_turnover": policy.min_turnover,
            "max_turnover": policy.max_turnover,
            "min_fitness": policy.min_fitness,
            "min_annual_return": policy.min_annual_return,
            "max_abs_drawdown": policy.max_abs_drawdown,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the CIS research-only gate to a normalized WorldQuant alpha")
    parser.add_argument("candidate_json")
    parser.add_argument("--output")
    parser.add_argument("--min-sharpe", type=float, default=1.25)
    parser.add_argument("--max-turnover", type=float, default=0.70)
    args = parser.parse_args()

    policy = ValidationPolicy(min_sharpe=args.min_sharpe, max_turnover=args.max_turnover)
    candidate = json.loads(Path(args.candidate_json).read_text(encoding="utf-8"))
    result = validate_candidate(candidate, policy)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result["screen_status"] not in {"invalid"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
