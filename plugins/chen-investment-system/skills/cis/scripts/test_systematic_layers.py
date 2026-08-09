from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from backtest_factor_strategy import run_backtest
from classify_market_regime import classify
from evaluate_cis_predictions import evaluate
from quant_factor_engine import score_rows


class QuantEngineTests(unittest.TestCase):
    def test_cross_section_ranks_high_quality_stock_higher(self) -> None:
        rows = [
            {"ticker": "AAA", "quality": "10", "volatility": "10"},
            {"ticker": "BBB", "quality": "5", "volatility": "20"},
            {"ticker": "CCC", "quality": "1", "volatility": "30"},
        ]
        factors = {
            "quality": {"weight": 0.8, "direction": "high"},
            "volatility": {"weight": 0.2, "direction": "low"},
        }
        result = score_rows(rows, factors, min_coverage=0.7)
        self.assertEqual(result[0]["ticker"], "AAA")
        self.assertEqual(result[-1]["ticker"], "CCC")
        self.assertEqual(result[0]["status"], "ready")

    def test_missing_factors_use_coverage_gate(self) -> None:
        rows = [{"ticker": "AAA", "a": "1", "b": ""}]
        factors = {
            "a": {"weight": 0.5, "direction": "high"},
            "b": {"weight": 0.5, "direction": "high"},
        }
        result = score_rows(rows, factors, min_coverage=0.7)[0]
        self.assertIsNone(result["quant_score"])
        self.assertEqual(result["status"], "insufficient")


class BacktestTests(unittest.TestCase):
    def test_selects_high_score_and_computes_positive_metrics(self) -> None:
        rows = [
            {"date": "2026-01", "ticker": "A", "score": "90", "forward_return": "0.10", "benchmark_return": "0.02"},
            {"date": "2026-01", "ticker": "B", "score": "20", "forward_return": "-0.05", "benchmark_return": "0.02"},
            {"date": "2026-02", "ticker": "A", "score": "80", "forward_return": "0.08", "benchmark_return": "0.01"},
            {"date": "2026-02", "ticker": "B", "score": "10", "forward_return": "-0.02", "benchmark_return": "0.01"},
        ]
        result = run_backtest(rows, top_fraction=0.5, top_n=1, cost_bps=0, periods_per_year=12)
        self.assertEqual(result["periods"], 2)
        self.assertGreater(result["metrics"]["cagr"], 0)
        self.assertGreater(result["metrics"]["mean_excess_return_per_period"], 0)


class MarketRegimeTests(unittest.TestCase):
    def test_risk_on(self) -> None:
        result = classify({
            "as_of": "2026-08-09",
            "index_above_sma200": True,
            "sma50_slope_pct": 2.0,
            "breadth_above_sma200_pct": 70,
            "vix": 16,
            "credit_spread_change_bps_3m": -10,
        })
        self.assertEqual(result["regime"], "risk_on")

    def test_insufficient(self) -> None:
        result = classify({"index_above_sma200": True})
        self.assertEqual(result["regime"], "insufficient")


class PerformanceLoopTests(unittest.TestCase):
    def test_high_scores_show_higher_returns_in_synthetic_sample(self) -> None:
        rows = [
            {"cis_score": "90", "realized_return": "0.20", "benchmark_return": "0.05", "regime": "risk_on"},
            {"cis_score": "80", "realized_return": "0.10", "benchmark_return": "0.04", "regime": "neutral"},
            {"cis_score": "50", "realized_return": "-0.10", "benchmark_return": "0.02", "regime": "risk_off"},
        ]
        result = evaluate(rows)
        self.assertEqual(result["sample_count"], 3)
        self.assertGreater(result["score_return_correlation"], 0)
        self.assertGreater(result["score_buckets"]["85-100"]["mean_realized_return"], 0)


if __name__ == "__main__":
    unittest.main()
