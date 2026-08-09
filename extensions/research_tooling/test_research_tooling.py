from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from backtest_factor_strategy import run_backtest
from evaluate_cis_predictions import evaluate
from prediction_ledger import DEFAULT_HORIZONS_TRADING_DAYS, materialize, record_outcome, record_prediction
from quant_factor_engine import score_rows
from record_cis_research import normalize_snapshot, record_snapshot
from settle_due_predictions import DailyBar, settle_prediction


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

    def test_mixed_as_of_is_rejected(self) -> None:
        rows = [
            {"ticker": "AAA", "as_of": "2026-08-09", "quality": "10"},
            {"ticker": "BBB", "as_of": "2026-08-08", "quality": "5"},
        ]
        with self.assertRaisesRegex(ValueError, "same as_of"):
            score_rows(rows, {"quality": {"weight": 1.0, "direction": "high"}})


class BacktestTests(unittest.TestCase):
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


class PredictionLedgerTests(unittest.TestCase):
    def test_default_horizons_are_tactical(self) -> None:
        self.assertEqual(DEFAULT_HORIZONS_TRADING_DAYS, (5, 20, 60))

    def test_prediction_is_immutable_and_outcome_is_separate_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            prediction = {
                "research_id": "MU-20260809-001",
                "as_of": "2026-08-09",
                "ticker": "MU",
                "cis_version": "0.4.3",
                "cis_score": 82,
                "score_status": "provisional",
                "research_posture": "进入深入研究",
                "horizon_days": 20,
                "benchmark": "SOXX",
                "dimension_scores": {"valuation": 70},
            }
            record_prediction(ledger, prediction)
            with self.assertRaisesRegex(ValueError, "already exists"):
                record_prediction(ledger, prediction)
            outcome = {
                "research_id": "MU-20260809-001",
                "horizon_trading_days": 20,
                "evaluation_as_of": "2026-09-08",
                "realized_return": 0.12,
                "benchmark_return": 0.08,
                "max_drawdown_during_horizon": -0.15,
                "falsifier_triggered": False,
            }
            record_outcome(ledger, outcome)
            rows = materialize(ledger)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["outcomes"][0]["realized_return"], 0.12)


class ResearchRecorderTests(unittest.TestCase):
    def test_snapshot_defaults_to_tactical_horizons(self) -> None:
        snapshot = normalize_snapshot({
            "ticker": "mu",
            "as_of": "2026-08-09",
            "score_status": "provisional",
            "research_posture": "继续观察",
            "benchmark": "SOXX",
        })
        self.assertEqual(snapshot["ticker"], "MU")
        self.assertEqual(snapshot["horizons_trading_days"], [5, 20, 60])

    def test_record_snapshot_writes_prediction_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "predictions.jsonl"
            event = record_snapshot(ledger, {
                "ticker": "NVDA",
                "as_of": "2026-08-09",
                "score_status": "provisional",
                "research_posture": "继续观察",
                "benchmark": "QQQ",
            })
            self.assertEqual(event["event_type"], "prediction")
            self.assertEqual(event["horizons_trading_days"], [5, 20, 60])


class SettlementTests(unittest.TestCase):
    def test_settlement_enters_after_research_date_and_uses_benchmark_sessions(self) -> None:
        sessions = [
            date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5),
            date(2026, 8, 6), date(2026, 8, 7), date(2026, 8, 10),
        ]
        benchmark = [DailyBar(day, 200 + index) for index, day in enumerate(sessions)]
        stock = [DailyBar(day, value) for day, value in zip(sessions, [100, 101, 102, 103, 104, 110])]

        def fake_fetcher(symbol: str, start: date, end: date) -> list[DailyBar]:
            return benchmark if symbol == "SPY" else stock

        outcomes, warnings = settle_prediction(
            {
                "research_id": "AAA-1",
                "as_of": "2026-08-01",
                "ticker": "AAA",
                "benchmark": "SPY",
                "horizons_trading_days": [5],
            },
            set(),
            today=date(2026, 8, 10),
            fetcher=fake_fetcher,
        )
        self.assertEqual(warnings, [])
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["entry_session_date"], "2026-08-03")
        self.assertEqual(outcomes[0]["exit_session_date"], "2026-08-10")
        self.assertEqual(outcomes[0]["horizon_calendar_basis"], "benchmark_sessions:SPY")
        self.assertEqual(outcomes[0]["path_metric_basis"], "adjusted_close_only")

    def test_missing_stock_price_on_next_session_is_left_unresolved(self) -> None:
        benchmark = [
            DailyBar(date(2026, 8, 3), 200),
            DailyBar(date(2026, 8, 4), 201),
        ]
        stock = [DailyBar(date(2026, 8, 4), 100)]

        def fake_fetcher(symbol: str, start: date, end: date) -> list[DailyBar]:
            return benchmark if symbol == "SPY" else stock

        outcomes, warnings = settle_prediction(
            {
                "research_id": "HALT-1",
                "as_of": "2026-08-01",
                "ticker": "HALT",
                "benchmark": "SPY",
                "horizons_trading_days": [1],
            },
            set(),
            today=date(2026, 8, 4),
            fetcher=fake_fetcher,
        )
        self.assertEqual(outcomes, [])
        self.assertTrue(any("no executable stock price" in warning for warning in warnings))


class EvaluationTests(unittest.TestCase):
    def test_high_scores_show_higher_returns_in_synthetic_sample(self) -> None:
        rows = [
            {"cis_score": "90", "realized_return": "0.20", "benchmark_return": "0.05", "horizon_days": "20", "valuation": "90"},
            {"cis_score": "80", "realized_return": "0.10", "benchmark_return": "0.04", "horizon_days": "20", "valuation": "80"},
            {"cis_score": "50", "realized_return": "-0.10", "benchmark_return": "0.02", "horizon_days": "60", "valuation": "40"},
        ]
        result = evaluate(rows)
        self.assertEqual(result["sample_count"], 3)
        self.assertGreater(result["score_return_correlation"], 0)
        self.assertGreater(result["dimension_diagnostics"]["valuation"]["excess_return_correlation"], 0)


if __name__ == "__main__":
    unittest.main()
