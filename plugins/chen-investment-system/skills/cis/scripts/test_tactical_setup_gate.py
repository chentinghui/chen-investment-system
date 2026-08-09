from __future__ import annotations

import unittest

from tactical_setup_gate import evaluate_tactical_setup, validate_price_context


BASE = {
    "analysis_timestamp": "2026-08-09T14:30:00+08:00",
    "quote_timestamp": "2026-08-09T14:29:30+08:00",
    "market_session": "regular",
    "price_type": "live",
    "current_price": 105,
    "direction": "long",
    "entry_low": 103,
    "entry_high": 106,
    "chase_limit": 108,
    "stop": 99,
    "target1": 118,
    "target2": 125,
}


class TacticalSetupGateTests(unittest.TestCase):
    def test_valid_regular_live_context(self) -> None:
        result = validate_price_context(BASE)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["price_semantics"], "live_current")
        self.assertEqual(result["quote_age_seconds"], 30.0)

    def test_regular_session_rejects_last_close_as_current(self) -> None:
        payload = dict(BASE)
        payload["price_type"] = "last_close"
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            validate_price_context(payload)

    def test_future_quote_is_rejected(self) -> None:
        payload = dict(BASE)
        payload["quote_timestamp"] = "2026-08-09T14:31:00+08:00"
        with self.assertRaisesRegex(ValueError, "cannot be later"):
            validate_price_context(payload)

    def test_attractive_long_setup_in_entry_zone(self) -> None:
        result = evaluate_tactical_setup(BASE)
        self.assertEqual(result["trade_gate"], "eligible_setup")
        self.assertEqual(result["price_location"], "in_entry_zone")
        self.assertGreaterEqual(result["rr_target1_worst"], 1.5)

    def test_beyond_chase_limit_blocks_entry(self) -> None:
        payload = dict(BASE)
        payload["current_price"] = 110
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["price_location"], "beyond_chase_limit")
        self.assertEqual(result["trade_gate"], "blocked_do_not_chase")

    def test_bad_long_geometry_is_rejected(self) -> None:
        payload = dict(BASE)
        payload["stop"] = 104
        with self.assertRaisesRegex(ValueError, "long setup requires"):
            evaluate_tactical_setup(payload)

    def test_closed_market_uses_last_close_reference(self) -> None:
        payload = dict(BASE)
        payload.update({
            "market_session": "closed",
            "price_type": "last_close",
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["price_context"]["price_semantics"], "last_close_reference")

    def test_short_setup_supported(self) -> None:
        payload = dict(BASE)
        payload.update({
            "direction": "short",
            "current_price": 104,
            "entry_low": 103,
            "entry_high": 106,
            "chase_limit": 100,
            "stop": 111,
            "target1": 92,
            "target2": 85,
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["trade_gate"], "eligible_setup")
        self.assertGreater(result["rr_target1_best"], 1.0)


if __name__ == "__main__":
    unittest.main()
