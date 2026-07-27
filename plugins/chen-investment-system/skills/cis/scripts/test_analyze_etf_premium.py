from __future__ import annotations

import unittest

from analyze_etf_premium import analyze


class AnalyzeEtfPremiumTests(unittest.TestCase):
    def test_compares_current_entry_and_history(self) -> None:
        result = analyze(
            {
                "code": "159509",
                "as_of": "2026-07-24",
                "current": {"price": 2.565, "iopv": 2.1864},
                "entry": {"price": 2.45, "iopv": 2.1},
                "history": [
                    {"date": "2026-05-01", "price": 1.15, "iopv": 1.0},
                    {"date": "2026-05-02", "price": 1.16, "iopv": 1.0},
                    {"date": "2026-05-03", "price": 1.17, "iopv": 1.0},
                    {"date": "2026-05-04", "price": 1.18, "iopv": 1.0},
                    {"date": "2026-05-05", "price": 1.19, "iopv": 1.0},
                ],
            }
        )
        self.assertEqual(result["current_premium_pct"], 17.3161)
        self.assertEqual(result["entry_premium_pct"], 16.6667)
        self.assertEqual(result["premium_change_pp"], 0.6495)
        self.assertEqual(result["history"]["status"], "ready")
        self.assertEqual(
            result["history"]["premium_regime"],
            "within_historical_interquartile_range",
        )

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
