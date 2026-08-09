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

    def test_latest_numeric_lean_tag_ignores_latest_alias(self) -> None:
        payload = {
            "results": [
                {"name": "latest"},
                {"name": "17947"},
                {"name": "17949"},
                {"name": "research"},
                {"name": "17948"},
            ]
        }
        self.assertEqual(MODULE.latest_numeric_lean_tag(payload), "17949")

    def test_lean_change_requires_review_and_never_auto_upgrades(self) -> None:
        status = {
            "reviewed_tag": "17948",
            "review_status": "reviewed_pinned_engine_baseline",
            "check_ttl_days": 7,
            "pinned_image": "quantconnect/lean:17948",
        }
        refreshed = MODULE.apply_lean_check(status, "17949", self.now)
        self.assertEqual(refreshed["observed_tag"], "17949")
        self.assertEqual(refreshed["reviewed_tag"], "17948")
        self.assertEqual(refreshed["review_status"], "review_required")
        self.assertEqual(refreshed["upstream_check"], "change_detected")
        self.assertFalse(refreshed["auto_upgrade"])
        self.assertTrue(refreshed["validation_required_before_upgrade"])
        self.assertEqual(refreshed["pinned_image"], "quantconnect/lean:17948")

    def test_lean_reviewed_tag_stays_current(self) -> None:
        status = {
            "reviewed_tag": "17948",
            "review_status": "reviewed_pinned_engine_baseline",
            "check_ttl_days": 7,
        }
        refreshed = MODULE.apply_lean_check(status, "17948", self.now)
        self.assertEqual(refreshed["upstream_check"], "current")
        self.assertTrue(refreshed["review_status"].startswith("reviewed"))
        self.assertEqual(
            refreshed["next_check_not_before"],
            MODULE.iso_z(self.now + timedelta(days=7)),
        )


if __name__ == "__main__":
    unittest.main()
