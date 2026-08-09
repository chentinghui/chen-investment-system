from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from classify_market_regime import classify


SIGNAL_DATES = {
    "index_above_sma200": "2026-08-09",
    "sma50_slope_pct": "2026-08-09",
    "breadth_above_sma200_pct": "2026-08-09",
    "vix": "2026-08-09",
    "realized_vol_20d": "2026-08-09",
    "high_yield_oas_bps": "2026-08-08",
    "credit_spread_change_bps_3m": "2026-08-08",
}


def full_payload() -> dict:
    return {
        "as_of": "2026-08-09",
        "regime_profile": "us_nasdaq_v1",
        "signal_as_of": dict(SIGNAL_DATES),
        "index_above_sma200": True,
        "sma50_slope_pct": 2.0,
        "breadth_above_sma200_pct": 70,
        "vix": 16,
        "realized_vol_20d": 15,
        "high_yield_oas_bps": 320,
        "credit_spread_change_bps_3m": -40,
    }


class MarketRegimeTests(unittest.TestCase):
    def test_risk_on(self) -> None:
        result = classify(full_payload())
        self.assertEqual(result["regime"], "risk_on")
        self.assertEqual(result["freshness_status"], "pass")
        self.assertEqual(result["profile_definition"]["trend_proxy"], "QQQ")

    def test_profile_is_required(self) -> None:
        payload = full_payload()
        payload.pop("regime_profile")
        with self.assertRaisesRegex(ValueError, "regime_profile"):
            classify(payload)

    def test_insufficient(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "regime_profile": "us_broad_v1",
            "signal_as_of": {"index_above_sma200": "2026-08-09"},
            "index_above_sma200": True,
        })
        self.assertEqual(result["regime"], "insufficient")

    def test_missing_signal_as_of_forces_insufficient_when_fresh_coverage_is_too_low(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "regime_profile": "us_broad_v1",
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "realized_vol_20d": 15,
        })
        self.assertEqual(result["regime"], "insufficient")
        self.assertEqual(result["freshness_status"], "insufficient_freshness")
        self.assertGreater(len(result["missing_signal_dates"]), 0)

    def test_one_stale_signal_is_excluded_when_fresh_coverage_remains_sufficient(self) -> None:
        payload = full_payload()
        payload["signal_as_of"]["vix"] = "2026-07-20"
        result = classify(payload)
        self.assertEqual(result["regime"], "risk_on")
        self.assertEqual(result["freshness_status"], "partial")
        self.assertIn("vix", result["stale_signals"])
        self.assertIn("vix", result["excluded_signals"])
        self.assertNotIn("vix", result["signals_used"])

    def test_many_stale_signals_can_still_force_insufficient(self) -> None:
        payload = full_payload()
        for name in (
            "index_above_sma200",
            "sma50_slope_pct",
            "breadth_above_sma200_pct",
            "vix",
            "realized_vol_20d",
        ):
            payload["signal_as_of"][name] = "2026-07-20"
        result = classify(payload)
        self.assertEqual(result["regime"], "insufficient")
        self.assertEqual(result["freshness_status"], "insufficient_freshness")

    def test_future_signal_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be after as_of"):
            classify({
                "as_of": "2026-08-09",
                "regime_profile": "us_broad_v1",
                "signal_as_of": {"vix": "2026-08-10"},
                "vix": 16,
            })

    def test_string_false_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON boolean"):
            classify({
                "as_of": "2026-08-09",
                "regime_profile": "us_broad_v1",
                "signal_as_of": {"index_above_sma200": "2026-08-09"},
                "index_above_sma200": "false",
            })

    def test_numeric_signal_rejects_json_boolean(self) -> None:
        with self.assertRaisesRegex(ValueError, "not JSON boolean"):
            classify({
                "as_of": "2026-08-09",
                "regime_profile": "us_broad_v1",
                "signal_as_of": {"vix": "2026-08-09"},
                "vix": True,
            })


if __name__ == "__main__":
    unittest.main()
