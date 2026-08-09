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


class MarketRegimeTests(unittest.TestCase):
    def test_risk_on(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "signal_as_of": SIGNAL_DATES,
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "realized_vol_20d": 15,
            "high_yield_oas_bps": 320,
            "credit_spread_change_bps_3m": -40,
        })
        self.assertEqual(result["regime"], "risk_on")
        self.assertEqual(result["freshness_status"], "pass")

    def test_insufficient(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "signal_as_of": {"index_above_sma200": "2026-08-09"},
            "index_above_sma200": True,
        })
        self.assertEqual(result["regime"], "insufficient")

    def test_missing_signal_as_of_forces_insufficient(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "realized_vol_20d": 15,
        })
        self.assertEqual(result["regime"], "insufficient")
        self.assertEqual(result["freshness_status"], "missing_signal_as_of")

    def test_stale_market_signal_forces_insufficient(self) -> None:
        dates = dict(SIGNAL_DATES)
        dates["vix"] = "2026-07-20"
        result = classify({
            "as_of": "2026-08-09",
            "signal_as_of": dates,
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "realized_vol_20d": 15,
            "high_yield_oas_bps": 320,
            "credit_spread_change_bps_3m": -40,
        })
        self.assertEqual(result["regime"], "insufficient")
        self.assertEqual(result["freshness_status"], "stale")
        self.assertIn("vix", result["stale_signals"])

    def test_future_signal_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be after as_of"):
            classify({
                "as_of": "2026-08-09",
                "signal_as_of": {"vix": "2026-08-10"},
                "vix": 16,
            })

    def test_string_false_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON boolean"):
            classify({
                "as_of": "2026-08-09",
                "signal_as_of": {"index_above_sma200": "2026-08-09"},
                "index_above_sma200": "false",
            })


if __name__ == "__main__":
    unittest.main()
