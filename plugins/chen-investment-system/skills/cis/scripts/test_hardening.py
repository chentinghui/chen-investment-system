from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from check_tradingagents_upstream import apply_check, should_check
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
