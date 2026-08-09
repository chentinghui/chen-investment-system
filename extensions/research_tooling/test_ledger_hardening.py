from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from prediction_ledger import record_outcome, record_prediction


class PredictionLedgerIntegerHorizonTests(unittest.TestCase):
    def _base_prediction(self) -> dict:
        return {
            "research_id": "STRICT-HORIZON-1",
            "as_of": "2026-08-09",
            "ticker": "NVDA",
            "cis_version": "0.4.5",
            "score_status": "provisional",
            "research_posture": "继续观察",
            "benchmark": "QQQ",
        }

    def test_fractional_prediction_horizon_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            payload = self._base_prediction()
            payload["horizons_trading_days"] = [20.5]
            with self.assertRaisesRegex(ValueError, "positive integer"):
                record_prediction(ledger, payload)

    def test_string_prediction_horizon_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            payload = self._base_prediction()
            payload["horizons_trading_days"] = ["20"]
            with self.assertRaisesRegex(ValueError, "positive integer"):
                record_prediction(ledger, payload)

    def test_fractional_outcome_horizon_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            prediction = self._base_prediction()
            prediction["horizons_trading_days"] = [20]
            record_prediction(ledger, prediction)
            with self.assertRaisesRegex(ValueError, "positive integer"):
                record_outcome(ledger, {
                    "research_id": "STRICT-HORIZON-1",
                    "horizon_trading_days": 20.5,
                    "evaluation_as_of": "2026-09-08",
                    "realized_return": 0.05,
                    "benchmark_return": 0.02,
                    "max_drawdown_during_horizon": -0.04,
                })


if __name__ == "__main__":
    unittest.main()
