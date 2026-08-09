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
            {"ticker": "AAA", "as_of": "2026-08-09", "quality": "10", "volatility": "10"},
            {"ticker": "BBB", "as_of": "2026-08-09", "quality": "5", "volatility": "20"},
            {"ticker": "CCC", "as_of": "2026-08-09", "quality": "1", "volatility": "30"},
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
        rows = [{"ticker": "AAA", "as_of": "2026-08-09", "a": "1", "b": ""}]
        factors = {
            "a": {"weight": 0.5, "direction": "high"},
            "b": {"weight": 0.5, "direction": "high"},
        }
        result = score_rows(rows, factors, min_coverage=0.7)[0]
        self.assertIsNone(result["quant_score"])
        self.assertEqual(result["status"], "insufficient")

    def test_mixed_as_of_is_rejected(self) -> None:
        rows = [
            {"ticker": "AAA", "as_of": "2026-08-09", "quality": "10"},
            {"ticker": "BBB", "as_of": "2026-08-08", "quality": "5"},
        ]
        with self.assertRaisesRegex(ValueError, "same as_of"):
            score_rows(rows, {"quality": {"weight": 1.0, "direction": "high"}})

    def test_signed_max_drawdown_uses_absolute_magnitude(self) -> None:
        rows = [
            {"ticker": "SAFE", "as_of": "2026-08-09", "max_drawdown_1y": "-0.10"},
            {"ticker": "RISKY", "as_of": "2026-08-09", "max_drawdown_1y": "-0.50"},
        ]
        factors = {"max_drawdown_1y": {"weight": 1.0, "direction": "low", "transform": "abs"}}
        result = score_rows(rows, factors)
        self.assertEqual(result[0]["ticker"], "SAFE")


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

    def test_turnover_cost_drops_when_holdings_do_not_change(self) -> None:
        rows = [
            {"date": "2026-01", "ticker": "A", "score": "90", "forward_return": "0.01"},
            {"date": "2026-01", "ticker": "B", "score": "10", "forward_return": "0.01"},
            {"date": "2026-02", "ticker": "A", "score": "90", "forward_return": "0.01"},
            {"date": "2026-02", "ticker": "B", "score": "10", "forward_return": "0.01"},
        ]
        result = run_backtest(rows, top_fraction=0.5, top_n=1, cost_bps=100, periods_per_year=12)
        self.assertEqual(result["period_details"][0]["turnover"], 1.0)
        self.assertEqual(result["period_details"][1]["turnover"], 0.0)
        self.assertGreater(result["period_details"][0]["transaction_cost"], 0)
        self.assertEqual(result["period_details"][1]["transaction_cost"], 0.0)

    def test_reports_oos_segment(self) -> None:
        rows = [
            {"date": "2025-12", "ticker": "A", "score": "90", "forward_return": "0.01"},
            {"date": "2026-01", "ticker": "A", "score": "90", "forward_return": "0.02"},
            {"date": "2026-02", "ticker": "A", "score": "90", "forward_return": "0.03"},
        ]
        result = run_backtest(
            rows, top_fraction=1.0, top_n=1, cost_bps=0, periods_per_year=12,
            train_end="2025-12", validation_end="2026-01"
        )
        self.assertIn("out_of_sample", result["metrics_by_segment"])
        self.assertEqual(result["metrics_by_segment"]["out_of_sample"]["periods"], 1)


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


class PerformanceLoopTests(unittest.TestCase):
    def test_high_scores_show_higher_returns_in_synthetic_sample(self) -> None:
        rows = [
            {"cis_score": "90", "realized_return": "0.20", "benchmark_return": "0.05", "regime": "risk_on", "horizon_days": "30", "valuation": "90"},
            {"cis_score": "80", "realized_return": "0.10", "benchmark_return": "0.04", "regime": "neutral", "horizon_days": "30", "valuation": "80"},
            {"cis_score": "50", "realized_return": "-0.10", "benchmark_return": "0.02", "regime": "risk_off", "horizon_days": "90", "valuation": "40"},
        ]
        result = evaluate(rows)
        self.assertEqual(result["sample_count"], 3)
        self.assertGreater(result["score_return_correlation"], 0)
        self.assertGreater(result["score_buckets"]["85-100"]["mean_realized_return"], 0)
        self.assertIn("0-30d", result["horizons"])
        self.assertGreater(result["dimension_diagnostics"]["valuation"]["return_correlation"], 0)


if __name__ == "__main__":
    unittest.main()
