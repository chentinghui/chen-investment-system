from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_tradingagents_upstream.py")
SPEC = importlib.util.spec_from_file_location("cis_upstream_ttl", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UpstreamTTLTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)

    def test_should_check_respects_seven_day_ttl(self) -> None:
        status = {
            "check_ttl_days": 7,
            "last_checked_at": MODULE.iso_z(self.now - timedelta(days=6)),
        }
        self.assertFalse(MODULE.should_check(status, self.now))
        status["last_checked_at"] = MODULE.iso_z(self.now - timedelta(days=7))
        self.assertTrue(MODULE.should_check(status, self.now))
        self.assertTrue(MODULE.should_check(status, self.now, force=True))

    def test_missing_last_checked_is_due(self) -> None:
        self.assertTrue(MODULE.should_check({"check_ttl_days": 7}, self.now))

    def test_reviewed_sha_stays_current(self) -> None:
        status = {
            "reviewed_sha": "abc123",
            "review_status": "reviewed_current",
            "check_ttl_days": 7,
        }
        refreshed = MODULE.apply_check(status, "abc123", self.now)
        self.assertEqual(refreshed["observed_sha"], "abc123")
        self.assertEqual(refreshed["upstream_check"], "current")
        self.assertTrue(refreshed["review_status"].startswith("reviewed"))
        self.assertEqual(
            refreshed["next_check_not_before"],
            MODULE.iso_z(self.now + timedelta(days=7)),
        )

    def test_changed_sha_requires_review(self) -> None:
        status = {
            "reviewed_sha": "abc123",
            "review_status": "reviewed_current",
            "check_ttl_days": 7,
        }
        refreshed = MODULE.apply_check(status, "def456", self.now)
        self.assertEqual(refreshed["observed_sha"], "def456")
        self.assertEqual(refreshed["reviewed_sha"], "abc123")
        self.assertEqual(refreshed["review_status"], "review_required")
        self.assertEqual(refreshed["upstream_check"], "change_detected")

    def test_checker_exposes_no_lean_helpers(self) -> None:
        self.assertFalse(hasattr(MODULE, "apply_lean_check"))
        self.assertFalse(hasattr(MODULE, "fetch_latest_lean_tag"))
        self.assertFalse(hasattr(MODULE, "latest_numeric_lean_tag"))


if __name__ == "__main__":
    unittest.main()
