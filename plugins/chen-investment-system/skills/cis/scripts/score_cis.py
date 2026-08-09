from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Mapping, Optional

WEIGHTS = {
    "fundamentals": 20,
    "growth": 15,
    "valuation": 15,
    "industry_competitive": 10,
    "technical": 15,
    "catalyst_macro": 10,
    "positioning": 5,
    "risk_resilience": 10,
}

CRITICAL_DIMENSIONS = {
    "generic": ("fundamentals", "valuation", "risk_resilience"),
    "long_term": ("fundamentals", "growth", "valuation", "risk_resilience"),
    "tactical": ("technical", "risk_resilience"),
    "earnings": ("fundamentals", "catalyst_macro", "risk_resilience"),
}

TACTICAL_REQUIRED_CHECKS = ("price_context", "catalyst_event_review")
VALID_AUDIT_STATUSES = {"unverified", "pass", "fail", "unresolved"}
VALID_RISK_STATUSES = {"unverified", "pass", "fail", "unresolved"}
VALID_RISK_OVERRIDES = {"none", "block"}


@dataclass(frozen=True)
class ScoreResult:
    score: Optional[float]
    coverage_pct: float
    grade: str
    research_posture: str
    missing_dimensions: tuple[str, ...]
    missing_critical_dimensions: tuple[str, ...]
    missing_context_checks: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    decision_context: str

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "coverage_pct": self.coverage_pct,
            "grade": self.grade,
            "research_posture": self.research_posture,
            "missing_dimensions": list(self.missing_dimensions),
            "missing_critical_dimensions": list(self.missing_critical_dimensions),
            "missing_context_checks": list(self.missing_context_checks),
            "blocked_reasons": list(self.blocked_reasons),
            "decision_context": self.decision_context,
        }


def _strict_bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be a JSON boolean")
    return value


def _validate(
    scores: Mapping[str, float | int | None],
    decision_context: str,
    audit_status: str,
    risk_status: str,
    risk_override: str,
    critical_blocked: bool,
    context_checks: Mapping[str, bool] | None,
) -> None:
    unknown = set(scores) - set(WEIGHTS)
    if unknown:
        raise ValueError(f"unknown dimensions: {', '.join(sorted(unknown))}")
    if decision_context not in CRITICAL_DIMENSIONS:
        raise ValueError(
            "decision_context must be one of: " + ", ".join(sorted(CRITICAL_DIMENSIONS))
        )
    for name, value in scores.items():
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name} must be numeric or null")
        if not 0 <= float(value) <= 100:
            raise ValueError(f"{name} must be between 0 and 100")

    if audit_status not in VALID_AUDIT_STATUSES:
        raise ValueError("audit_status must be one of: " + ", ".join(sorted(VALID_AUDIT_STATUSES)))
    if risk_status not in VALID_RISK_STATUSES:
        raise ValueError("risk_status must be one of: " + ", ".join(sorted(VALID_RISK_STATUSES)))
    if risk_override not in VALID_RISK_OVERRIDES:
        raise ValueError("risk_override must be one of: " + ", ".join(sorted(VALID_RISK_OVERRIDES)))
    _strict_bool(critical_blocked, "critical_blocked")

    if context_checks is not None:
        unknown_checks = set(context_checks) - set(TACTICAL_REQUIRED_CHECKS)
        if unknown_checks:
            raise ValueError(f"unknown context checks: {', '.join(sorted(unknown_checks))}")
        for name, value in context_checks.items():
            _strict_bool(value, f"context_checks.{name}")


def _posture(score: Optional[float], grade: str) -> str:
    if score is None or grade == "insufficient":
        return "证据不足"
    if score >= 85:
        return "进入深入研究（高优先级）"
    if score >= 75:
        return "进入深入研究"
    if score >= 60:
        return "继续观察"
    return "暂时回避"


def calculate_score(
    scores: Mapping[str, float | int | None],
    *,
    audit_status: str = "unverified",
    risk_status: str = "unverified",
    risk_override: str = "none",
    critical_blocked: bool = False,
    decision_context: str = "generic",
    context_checks: Mapping[str, bool] | None = None,
) -> ScoreResult:
    """Calculate a CIS score using fail-closed quality gates.

    `decision_grade` is available only when coverage is >=85%, evidence audit
    and risk review explicitly pass, all context-critical dimensions exist, and
    any context-specific checks have been completed. Missing dimensions are
    never imputed as zero.
    """
    _validate(
        scores,
        decision_context,
        audit_status,
        risk_status,
        risk_override,
        critical_blocked,
        context_checks,
    )

    available = {k: float(v) for k, v in scores.items() if v is not None}
    available_weight = sum(WEIGHTS[k] for k in available)
    coverage_pct = float(available_weight)

    missing = tuple(k for k in WEIGHTS if k not in available)
    required = CRITICAL_DIMENSIONS[decision_context]
    missing_critical = tuple(k for k in required if k not in available)

    missing_checks: tuple[str, ...] = ()
    if decision_context == "tactical":
        checks = context_checks or {}
        missing_checks = tuple(name for name in TACTICAL_REQUIRED_CHECKS if checks.get(name) is not True)

    weighted = (
        sum(available[k] * WEIGHTS[k] for k in available) / available_weight
        if available_weight
        else None
    )

    blocked: list[str] = []
    if audit_status != "pass":
        blocked.append("audit_not_passed")
    if risk_status != "pass":
        blocked.append("risk_review_not_passed")
    if risk_override == "block":
        blocked.append("risk_override_block")
    if critical_blocked:
        blocked.append("critical_dimension_blocked")
    if missing_critical:
        blocked.append("critical_dimensions_missing")
    if missing_checks:
        blocked.append("tactical_checks_incomplete")

    if coverage_pct < 70:
        grade = "insufficient"
        reported_score = None
    elif coverage_pct < 85:
        grade = "provisional"
        reported_score = round(weighted, 1) if weighted is not None else None
    else:
        reported_score = round(weighted, 1) if weighted is not None else None
        grade = "decision_grade" if not blocked else "provisional"

    posture = _posture(reported_score, grade)
    if blocked:
        if (
            "audit_not_passed" in blocked
            or "critical_dimension_blocked" in blocked
            or "critical_dimensions_missing" in blocked
            or "tactical_checks_incomplete" in blocked
        ):
            posture = "证据不足"
        else:
            posture = f"{posture}（风险门未通过）"

    return ScoreResult(
        score=reported_score,
        coverage_pct=coverage_pct,
        grade=grade,
        research_posture=posture,
        missing_dimensions=missing,
        missing_critical_dimensions=missing_critical,
        missing_context_checks=missing_checks,
        blocked_reasons=tuple(blocked),
        decision_context=decision_context,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate CIS weighted research score.")
    parser.add_argument("input", help="JSON file containing dimension scores")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    result = calculate_score(
        payload.get("scores", {}),
        audit_status=payload.get("audit_status", "unverified"),
        risk_status=payload.get("risk_status", "unverified"),
        risk_override=payload.get("risk_override", "none"),
        critical_blocked=payload.get("critical_blocked", False),
        decision_context=payload.get("decision_context", "generic"),
        context_checks=payload.get("context_checks"),
    )
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
