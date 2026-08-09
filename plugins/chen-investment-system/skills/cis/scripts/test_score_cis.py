from __future__ import annotations

import unittest

from score_cis import calculate_score


FULL_80 = {
    "fundamentals": 80,
    "growth": 80,
    "valuation": 80,
    "industry_competitive": 80,
    "technical": 80,
    "catalyst_macro": 80,
    "positioning": 80,
    "risk_resilience": 80,
}


class ScoreCISTests(unittest.TestCase):
    def test_full_equal_scores_require_explicit_gates(self) -> None:
        result = calculate_score(FULL_80, audit_status="pass", risk_status="pass")
        self.assertEqual(result.score, 80.0)
        self.assertEqual(result.coverage_pct, 100.0)
        self.assertEqual(result.grade, "decision_grade")
        self.assertEqual(result.research_posture, "进入深入研究")

    def test_defaults_are_fail_closed(self) -> None:
        result = calculate_score(FULL_80)
        self.assertEqual(result.grade, "provisional")
        self.assertIn("audit_not_passed", result.blocked_reasons)
        self.assertIn("risk_review_not_passed", result.blocked_reasons)

    def test_low_coverage_suppresses_total(self) -> None:
        result = calculate_score({"fundamentals": 90, "growth": 90, "valuation": 90})
        self.assertEqual(result.coverage_pct, 50.0)
        self.assertIsNone(result.score)
        self.assertEqual(result.grade, "insufficient")

    def test_missing_valuation_cannot_be_decision_grade_at_85_coverage(self) -> None:
        scores = dict(FULL_80)
        scores.pop("valuation")
        result = calculate_score(scores, audit_status="pass", risk_status="pass")
        self.assertEqual(result.coverage_pct, 85.0)
        self.assertEqual(result.grade, "provisional")
        self.assertIn("valuation", result.missing_critical_dimensions)
        self.assertIn("critical_dimensions_missing", result.blocked_reasons)

    def test_tactical_context_still_obeys_global_coverage_gate(self) -> None:
        scores = dict(FULL_80)
        scores.pop("fundamentals")
        scores.pop("valuation")
        result = calculate_score(
            scores,
            audit_status="pass",
            risk_status="pass",
            decision_context="tactical",
            context_checks={"price_context": True, "catalyst_event_review": True},
        )
        self.assertEqual(result.coverage_pct, 65.0)
        self.assertEqual(result.grade, "insufficient")
        self.assertIsNone(result.score)
        self.assertEqual(result.missing_critical_dimensions, ())

    def test_tactical_requires_price_and_catalyst_checks(self) -> None:
        result = calculate_score(
            FULL_80,
            audit_status="pass",
            risk_status="pass",
            decision_context="tactical",
        )
        self.assertEqual(result.grade, "provisional")
        self.assertIn("tactical_checks_incomplete", result.blocked_reasons)
        self.assertEqual(
            set(result.missing_context_checks),
            {"price_context", "catalyst_event_review"},
        )

    def test_tactical_can_be_decision_grade_after_required_checks(self) -> None:
        result = calculate_score(
            FULL_80,
            audit_status="pass",
            risk_status="pass",
            decision_context="tactical",
            context_checks={"price_context": True, "catalyst_event_review": True},
        )
        self.assertEqual(result.grade, "decision_grade")
        self.assertEqual(result.missing_context_checks, ())

    def test_risk_block_prevents_decision_grade(self) -> None:
        scores = {key: 90 for key in FULL_80}
        result = calculate_score(scores, audit_status="pass", risk_status="pass", risk_override="block")
        self.assertEqual(result.grade, "provisional")
        self.assertIn("risk_override_block", result.blocked_reasons)
        self.assertIn("风险门未通过", result.research_posture)

    def test_critical_block_is_reported_as_evidence_quality_block_not_risk_block(self) -> None:
        scores = {key: 90 for key in FULL_80}
        result = calculate_score(
            scores,
            audit_status="pass",
            risk_status="pass",
            critical_blocked=True,
        )
        self.assertEqual(result.grade, "provisional")
        self.assertIn("critical_dimension_blocked", result.blocked_reasons)
        self.assertEqual(result.research_posture, "证据不足")

    def test_unverified_audit_never_decision_grade(self) -> None:
        scores = {key: 90 for key in FULL_80}
        result = calculate_score(scores, risk_status="pass")
        self.assertEqual(result.grade, "provisional")
        self.assertEqual(result.research_posture, "证据不足")

    def test_string_false_is_rejected_for_critical_blocked(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON boolean"):
            calculate_score(FULL_80, critical_blocked="false")  # type: ignore[arg-type]

    def test_invalid_gate_status_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "audit_status"):
            calculate_score(FULL_80, audit_status="pas")

    def test_context_checks_require_real_booleans(self) -> None:
        with self.assertRaisesRegex(ValueError, "context_checks.price_context"):
            calculate_score(
                FULL_80,
                decision_context="tactical",
                context_checks={"price_context": "true"},  # type: ignore[dict-item]
            )


if __name__ == "__main__":
    unittest.main()
