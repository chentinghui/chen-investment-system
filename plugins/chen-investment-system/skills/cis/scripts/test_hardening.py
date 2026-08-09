from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from check_tradingagents_upstream import apply_check, should_check
from prediction_ledger import materialize, record_outcome, record_prediction
from run_tradingagents_remote import validate_request


class TradingAgentsTTLTests(unittest.TestCase):
    def test_ttl_skips_before_seven_days(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"last_checked_at": (now - timedelta(days=6)).isoformat(), "check_ttl_days": 7}
        self.assertFalse(should_check(status, now))

    def test_ttl_checks_at_seven_days(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"last_checked_at": (now - timedelta(days=7)).isoformat(), "check_ttl_days": 7}
        self.assertTrue(should_check(status, now))

    def test_new_sha_marks_review_required(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"reviewed_sha": "old", "review_status": "reviewed", "check_ttl_days": 7}
        result = apply_check(status, "new", now)
        self.assertEqual(result["review_status"], "review_required")
        self.assertEqual(result["upstream_check"], "change_detected")


class PredictionLedgerTests(unittest.TestCase):
    def test_prediction_is_immutable_and_outcome_is_separate_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            prediction = {
                "research_id": "MU-20260809-001",
                "as_of": "2026-08-09",
                "ticker": "MU",
                "cis_version": "0.4.2",
                "cis_score": 82,
                "score_status": "provisional",
                "research_posture": "进入深入研究",
                "horizon_days": 90,
                "benchmark": "SOXX",
                "dimension_scores": {"valuation": 70},
            }
            record_prediction(ledger, prediction)
            with self.assertRaisesRegex(ValueError, "already exists"):
                record_prediction(ledger, prediction)

            outcome = {
                "research_id": "MU-20260809-001",
                "evaluation_as_of": "2026-11-07",
                "realized_return": 0.12,
                "benchmark_return": 0.08,
                "max_drawdown_during_horizon": -0.15,
                "falsifier_triggered": False,
            }
            record_outcome(ledger, outcome)
            rows = materialize(ledger)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["cis_score"], 82)
            self.assertEqual(rows[0]["outcome"]["realized_return"], 0.12)


class TradingAgentsAdapterTests(unittest.TestCase):
    def test_manual_request_contract_normalizes_ticker(self) -> None:
        result = validate_request({
            "request_id": "x1",
            "ticker": "mu",
            "analysis_date": "2026-08-09",
            "backend": "ollama",
            "selected_analysts": ["market"],
            "max_debate_rounds": 0,
            "max_risk_rounds": 0,
        })
        self.assertEqual(result["ticker"], "MU")
        self.assertEqual(result["backend"], "ollama")

    def test_openai_compatible_requires_url_and_model(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires deep_model and backend_url"):
            validate_request({
                "request_id": "x2",
                "ticker": "MU",
                "analysis_date": "2026-08-09",
                "backend": "openai_compatible",
                "selected_analysts": ["market"],
            })


if __name__ == "__main__":
    unittest.main()
