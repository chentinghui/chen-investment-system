from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from classify_market_regime import classify


class MarketRegimeTests(unittest.TestCase):
    def test_risk_on(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "realized_vol_20d": 15,
            "high_yield_oas_bps": 320,
            "credit_spread_change_bps_3m": -40,
        })
        self.assertEqual(result["regime"], "risk_on")

    def test_insufficient(self) -> None:
        result = classify({"as_of": "2026-08-09", "index_above_sma200": True})
        self.assertEqual(result["regime"], "insufficient")

    def test_string_false_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON boolean"):
            classify({"as_of": "2026-08-09", "index_above_sma200": "false"})


if __name__ == "__main__":
    unittest.main()
