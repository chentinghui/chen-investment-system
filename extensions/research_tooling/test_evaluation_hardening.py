from __future__ import annotations

import unittest

from evaluate_cis_predictions import evaluate


class EvaluationInputHardeningTests(unittest.TestCase):
    def test_duplicate_research_horizon_is_rejected(self) -> None:
        rows = [
            {
                "research_id": "R1",
                "cis_score": "80",
                "realized_return": "0.05",
                "benchmark_return": "0.01",
                "horizon_days": "20",
            },
            {
                "research_id": "R1",
                "cis_score": "80",
                "realized_return": "0.05",
                "benchmark_return": "0.01",
                "horizon_days": "20",
            },
        ]
        with self.assertRaisesRegex(ValueError, "duplicate evaluation outcome"):
            evaluate(rows)

    def test_malformed_realized_return_is_rejected_not_silently_dropped(self) -> None:
        rows = [
            {
                "research_id": "R1",
                "cis_score": "80",
                "realized_return": "bad",
                "benchmark_return": "0.01",
                "horizon_days": "20",
            }
        ]
        with self.assertRaisesRegex(ValueError, "realized_return must be a finite number"):
            evaluate(rows)

    def test_missing_score_is_reported_as_excluded(self) -> None:
        rows = [
            {
                "research_id": "R1",
                "cis_score": "",
                "realized_return": "0.05",
                "benchmark_return": "0.01",
                "horizon_days": "20",
            },
            {
                "research_id": "R2",
                "cis_score": "80",
                "realized_return": "0.04",
                "benchmark_return": "0.01",
                "horizon_days": "20",
            },
        ]
        result = evaluate(rows)
        self.assertEqual(result["input_row_count"], 2)
        self.assertEqual(result["excluded_missing_score_count"], 1)
        self.assertEqual(result["outcome_count"], 1)

    def test_invalid_horizon_is_rejected(self) -> None:
        rows = [
            {
                "research_id": "R1",
                "cis_score": "80",
                "realized_return": "0.05",
                "benchmark_return": "0.01",
                "horizon_days": "20.5",
            }
        ]
        with self.assertRaisesRegex(ValueError, "positive integer"):
            evaluate(rows)


if __name__ == "__main__":
    unittest.main()
