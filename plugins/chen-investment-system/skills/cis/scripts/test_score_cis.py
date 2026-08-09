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

    def test_tactical_context_requires_technical_and_risk(self) -> None:
        scores = dict(FULL_80)
        scores.pop("fundamentals")
        scores.pop("valuation")
        result = calculate_score(
            scores,
            audit_status="pass",
            risk_status="pass",
            decision_context="tactical",
        )
        self.assertEqual(result.grade, "provisional")  # coverage is below 85 despite criticals being present
        self.assertEqual(result.missing_critical_dimensions, ())

    def test_risk_block_prevents_decision_grade(self) -> None:
        scores = {key: 90 for key in FULL_80}
        result = calculate_score(scores, audit_status="pass", risk_status="pass", risk_override="block")
        self.assertEqual(result.grade, "provisional")
        self.assertIn("risk_override_block", result.blocked_reasons)

    def test_unverified_audit_never_decision_grade(self) -> None:
        scores = {key: 90 for key in FULL_80}
        result = calculate_score(scores, risk_status="pass")
        self.assertEqual(result.grade, "provisional")
        self.assertEqual(result.research_posture, "证据不足")


if __name__ == "__main__":
    unittest.main()
