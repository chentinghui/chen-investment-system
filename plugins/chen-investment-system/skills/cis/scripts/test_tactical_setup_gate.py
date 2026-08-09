from __future__ import annotations

import unittest

from tactical_setup_gate import evaluate_tactical_setup, validate_price_context


BASE = {
    "analysis_timestamp": "2026-08-10T10:30:00-04:00",
    "quote_timestamp": "2026-08-10T10:29:30-04:00",
    "exchange": "XNAS",
    "market_session": "regular",
    "price_type": "live",
    "quote_max_age_seconds": 120,
    "current_price": 105,
    "direction": "long",
    "entry_low": 103,
    "entry_high": 106,
    "chase_limit": 108,
    "stop": 99,
    "stop_type": "hard_price",
    "target1": 118,
    "target2": 125,
}


class TacticalSetupGateTests(unittest.TestCase):
    def test_valid_regular_live_context(self) -> None:
        result = validate_price_context(BASE)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["price_semantics"], "live_current")
        self.assertEqual(result["quote_age_seconds"], 30.0)
        self.assertEqual(result["market_session"], "regular")
        self.assertEqual(result["quote_observation_session"], "regular")
        self.assertEqual(result["quote_freshness_status"], "fresh")

    def test_regular_session_rejects_last_close_as_current(self) -> None:
        payload = dict(BASE)
        payload["price_type"] = "last_close"
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            validate_price_context(payload)

    def test_regular_session_rejects_premarket_observation_even_if_age_is_allowed(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-10T09:35:00-04:00",
            "quote_timestamp": "2026-08-10T09:00:00-04:00",
            "quote_max_age_seconds": 3600,
        })
        with self.assertRaisesRegex(ValueError, "belongs to premarket"):
            validate_price_context(payload)

    def test_future_quote_is_rejected(self) -> None:
        payload = dict(BASE)
        payload["quote_timestamp"] = "2026-08-10T10:31:00-04:00"
        with self.assertRaisesRegex(ValueError, "cannot be later"):
            validate_price_context(payload)

    def test_weekend_cannot_pretend_to_be_regular_session(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-09T10:30:00-04:00",
            "quote_timestamp": "2026-08-09T10:29:30-04:00",
        })
        with self.assertRaisesRegex(ValueError, "expected closed"):
            validate_price_context(payload)

    def test_stale_live_quote_is_rejected(self) -> None:
        payload = dict(BASE)
        payload["quote_timestamp"] = "2026-08-10T10:20:00-04:00"
        with self.assertRaisesRegex(ValueError, "quote is stale"):
            validate_price_context(payload)

    def test_active_quote_age_policy_cannot_be_unbounded(self) -> None:
        payload = dict(BASE)
        payload["quote_max_age_seconds"] = 7200
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            validate_price_context(payload)

    def test_attractive_long_setup_in_entry_zone(self) -> None:
        result = evaluate_tactical_setup(BASE)
        self.assertEqual(result["trade_gate"], "eligible_setup")
        self.assertEqual(result["price_location"], "in_entry_zone")
        self.assertGreaterEqual(result["rr_target1_worst"], 1.5)

    def test_stop_type_is_required(self) -> None:
        payload = dict(BASE)
        payload.pop("stop_type")
        with self.assertRaisesRegex(ValueError, "stop_type is required"):
            evaluate_tactical_setup(payload)

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

    def test_chase_limit_cannot_be_beyond_target1(self) -> None:
        payload = dict(BASE)
        payload["chase_limit"] = 120
        with self.assertRaisesRegex(ValueError, "chase_limit"):
            evaluate_tactical_setup(payload)

    def test_stop_breach_invalidates_hard_stop_setup(self) -> None:
        payload = dict(BASE)
        payload["current_price"] = 98
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["setup_state"], "invalidated")
        self.assertEqual(result["trade_gate"], "invalidated_reprice_required")

    def test_close_confirmation_stop_can_wait_for_confirmation(self) -> None:
        payload = dict(BASE)
        payload.update({
            "current_price": 98,
            "stop_type": "close_confirmation",
            "stop_confirmation_met": False,
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["setup_state"], "stop_breached_unconfirmed")
        self.assertEqual(result["trade_gate"], "blocked_pending_stop_confirmation")

    def test_close_confirmation_stop_invalidates_when_confirmed(self) -> None:
        payload = dict(BASE)
        payload.update({
            "current_price": 98,
            "stop_type": "close_confirmation",
            "stop_confirmation_met": True,
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["trade_gate"], "invalidated_reprice_required")

    def test_confirmed_stop_remains_invalidated_after_price_recovers(self) -> None:
        payload = dict(BASE)
        payload.update({
            "current_price": 105,
            "stop_type": "close_confirmation",
            "stop_confirmation_met": True,
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["setup_state"], "invalidated")
        self.assertEqual(result["price_location"], "invalidation_confirmed")
        self.assertEqual(result["trade_gate"], "invalidated_reprice_required")

    def test_technical_invalidation_can_invalidate_without_numeric_stop_breach(self) -> None:
        payload = dict(BASE)
        payload.update({
            "current_price": 105,
            "stop_type": "technical_invalidation",
            "stop_confirmation_met": True,
        })
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["trade_gate"], "invalidated_reprice_required")

    def test_target1_reached_requires_repricing(self) -> None:
        payload = dict(BASE)
        payload["current_price"] = 119
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["setup_state"], "expired_target_reached")
        self.assertEqual(result["trade_gate"], "setup_expired_reprice_required")

    def test_closed_market_uses_most_recent_last_close_reference(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-09T10:30:00-04:00",
            "quote_timestamp": "2026-08-07T16:00:00-04:00",
            "market_session": "closed",
            "price_type": "last_close",
            "quote_session_date": "2026-08-07",
        })
        payload.pop("quote_max_age_seconds")
        result = evaluate_tactical_setup(payload)
        self.assertEqual(result["price_context"]["price_semantics"], "last_close_reference")
        self.assertEqual(result["price_context"]["quote_session_date"], "2026-08-07")

    def test_closed_market_rejects_old_last_close(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-09T10:30:00-04:00",
            "quote_timestamp": "2026-08-06T16:00:00-04:00",
            "market_session": "closed",
            "price_type": "last_close",
            "quote_session_date": "2026-08-06",
        })
        payload.pop("quote_max_age_seconds")
        with self.assertRaisesRegex(ValueError, "most recent completed session"):
            evaluate_tactical_setup(payload)

    def test_closed_market_rejects_quote_timestamp_date_mismatch(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-09T10:30:00-04:00",
            "quote_timestamp": "2026-08-06T16:00:00-04:00",
            "market_session": "closed",
            "price_type": "last_close",
            "quote_session_date": "2026-08-07",
        })
        payload.pop("quote_max_age_seconds")
        with self.assertRaisesRegex(ValueError, "quote_timestamp date"):
            evaluate_tactical_setup(payload)

    def test_closed_market_rejects_preclose_timestamp_as_last_close(self) -> None:
        payload = dict(BASE)
        payload.update({
            "analysis_timestamp": "2026-08-09T10:30:00-04:00",
            "quote_timestamp": "2026-08-07T09:00:00-04:00",
            "market_session": "closed",
            "price_type": "last_close",
            "quote_session_date": "2026-08-07",
        })
        payload.pop("quote_max_age_seconds")
        with self.assertRaisesRegex(ValueError, "at or after the session regular close"):
            evaluate_tactical_setup(payload)

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
