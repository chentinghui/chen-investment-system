from __future__ import annotations

import unittest

from analyze_etf_premium import MIN_HISTORY_OBSERVATIONS, analyze


class AnalyzeEtfPremiumTests(unittest.TestCase):
    def test_compares_current_entry_and_history(self) -> None:
        history = [
            {"date": f"2026-05-{day:02d}", "price": 1.10 + day / 100.0, "iopv": 1.0}
            for day in range(1, MIN_HISTORY_OBSERVATIONS + 1)
        ]
        result = analyze(
            {
                "code": "159509",
                "as_of": "2026-07-24",
                "current": {"price": 2.565, "iopv": 2.1864},
                "entry": {"price": 2.45, "iopv": 2.1},
                "history": history,
            }
        )
        self.assertEqual(result["current_premium_pct"], 17.3161)
        self.assertEqual(result["entry_premium_pct"], 16.6667)
        self.assertEqual(result["premium_change_pp"], 0.6495)
        self.assertEqual(result["history"]["status"], "ready")
        self.assertEqual(result["history"]["required_observations"], 20)
        self.assertEqual(result["history"]["valid_observations"], 20)
        self.assertEqual(
            result["history"]["premium_regime"],
            "within_historical_interquartile_range",
        )

    def test_five_observations_are_not_enough_for_historical_regime(self) -> None:
        result = analyze(
            {
                "current": {"price": 1.2, "iopv": 1.0},
                "history": [
                    {"price": 1.15 + i / 100.0, "iopv": 1.0}
                    for i in range(5)
                ],
            }
        )
        self.assertEqual(result["history"]["status"], "insufficient_history")
        self.assertEqual(result["history"]["valid_observations"], 5)
        self.assertEqual(result["history"]["required_observations"], 20)

    def test_requires_enough_history_before_regime_claim(self) -> None:
        result = analyze(
            {
                "current": {"price": 1.2, "iopv": 1.0},
                "history": [
                    {"price": 1.18, "iopv": 1.0},
                    {"price": 1.19, "iopv": 1.0},
                ],
            }
        )
        self.assertEqual(result["history"]["status"], "insufficient_history")
        self.assertIsNone(result["entry_premium_pct"])

    def test_rejects_non_positive_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive number"):
            analyze({"current": {"price": 1.0, "iopv": 0}})


if __name__ == "__main__":
    unittest.main()
