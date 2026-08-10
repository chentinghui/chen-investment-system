from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


alpha_import = load_module("cis_alpha_import", "worldquant/alpha_import.py")
alpha_validator = load_module("cis_alpha_validator", "worldquant/alpha_validator.py")
cross_section = load_module("cis_cross_section", "factor_engine/cross_section.py")
factor_test = load_module("cis_factor_test", "factor_engine/factor_test.py")
factor_library = load_module("cis_factor_library", "factor_engine/factor_library.py")
alpha_miner = load_module("cis_alpha_miner", "factor_engine/alpha_miner.py")
model_test = load_module("cis_model_test", "ml_research/model_test.py")


class WorldQuantImportTests(unittest.TestCase):
    def test_normalizes_export_and_percent_metrics(self) -> None:
        payload = {
            "id": "alpha-001",
            "name": "Mean Reversion",
            "expression": "-group_rank(close-open, subindustry)",
            "settings": {
                "region": "USA",
                "universe": "TOP3000",
                "delay": 1,
                "neutralization": "SUBINDUSTRY",
                "decay": 10,
                "truncation": 0.01,
            },
            "metrics": {
                "sharpe": 1.7,
                "return": "9%",
                "turnover": "29%",
                "fitness": 1.2,
                "drawdown": "12%",
            },
        }
        result = alpha_import.normalize_worldquant_alpha(payload)
        self.assertEqual(result["schema_version"], "cis.alpha_candidate.v1")
        self.assertEqual(result["source"], "worldquant_brain")
        self.assertEqual(result["decision_authority"], "none")
        self.assertAlmostEqual(result["metrics"]["annual_return"], 0.09)
        self.assertAlmostEqual(result["metrics"]["turnover"], 0.29)
        self.assertAlmostEqual(result["metrics"]["max_drawdown"], 0.12)

    def test_missing_id_gets_stable_fingerprint(self) -> None:
        payload = {
            "expression": "rank(close)",
            "settings": {"region": "USA", "universe": "TOP3000", "delay": 1},
        }
        first = alpha_import.normalize_worldquant_alpha(payload)
        second = alpha_import.normalize_worldquant_alpha(payload)
        self.assertEqual(first["alpha_id"], second["alpha_id"])
        self.assertTrue(first["alpha_id"].startswith("wq-"))


class AlphaValidatorTests(unittest.TestCase):
    def _candidate(self):
        return alpha_import.normalize_worldquant_alpha(
            {
                "id": "alpha-002",
                "expression": "rank(close)",
                "settings": {"region": "USA", "universe": "TOP3000", "delay": 1},
                "metrics": {
                    "sharpe": 1.8,
                    "turnover": 0.25,
                    "fitness": 1.3,
                    "annual_return": 0.08,
                    "max_drawdown": 0.15,
                },
            }
        )

    def test_good_screen_is_candidate_not_trade_authority(self) -> None:
        result = alpha_validator.validate_candidate(self._candidate())
        self.assertEqual(result["screen_status"], "candidate_for_cis_validation")
        self.assertEqual(result["decision_authority"], "none")
        self.assertIn("out_of_sample_validation", result["required_next_reviews"])

    def test_missing_core_metrics_is_insufficient(self) -> None:
        candidate = self._candidate()
        candidate["metrics"]["sharpe"] = None
        result = alpha_validator.validate_candidate(candidate)
        self.assertEqual(result["screen_status"], "insufficient")
        self.assertIn("sharpe", result["missing_core_metrics"])

    def test_live_trading_or_secret_fields_are_rejected(self) -> None:
        candidate = self._candidate()
        candidate["api_key"] = "do-not-store-this"
        result = alpha_validator.validate_candidate(candidate)
        self.assertEqual(result["screen_status"], "invalid")
        self.assertTrue(any("forbidden" in item for item in result["structural_failures"]))


class CrossSectionTests(unittest.TestCase):
    def test_positive_factor_has_positive_ic_and_spread(self) -> None:
        rows = [
            {"date": "2026-01-02", "ticker": "A", "factor": 1, "forward_return": 0.01},
            {"date": "2026-01-02", "ticker": "B", "factor": 2, "forward_return": 0.02},
            {"date": "2026-01-02", "ticker": "C", "factor": 3, "forward_return": 0.03},
            {"date": "2026-01-02", "ticker": "D", "factor": 4, "forward_return": 0.04},
            {"date": "2026-01-02", "ticker": "E", "factor": 5, "forward_return": 0.05},
        ]
        result = cross_section.evaluate_cross_section(rows)
        self.assertAlmostEqual(result["mean_rank_ic"], 1.0)
        self.assertGreater(result["mean_top_bottom_spread"], 0)

    def test_duplicate_date_ticker_is_rejected(self) -> None:
        rows = [
            {"date": "2026-01-02", "ticker": "A", "factor": 1, "forward_return": 0.01},
            {"date": "2026-01-02", "ticker": "A", "factor": 2, "forward_return": 0.02},
            {"date": "2026-01-02", "ticker": "B", "factor": 3, "forward_return": 0.03},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate date/ticker"):
            cross_section.evaluate_cross_section(rows)

    def test_factor_direction_low_is_supported(self) -> None:
        rows = [
            {"date": "2026-01-02", "ticker": "A", "value": 1, "forward_return": 0.03},
            {"date": "2026-01-02", "ticker": "B", "value": 2, "forward_return": 0.02},
            {"date": "2026-01-02", "ticker": "C", "value": 3, "forward_return": 0.01},
        ]
        result = factor_test.evaluate_factor_rows(rows, factor_field="value", direction="low")
        self.assertGreater(result["summary"]["mean_rank_ic"], 0)


class LightweightAlphaResearchTests(unittest.TestCase):
    @staticmethod
    def _bars(days: int = 45) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        start = date(2026, 1, 1)
        for ticker_index, ticker in enumerate(("A", "B", "C", "D", "E"), start=1):
            close = 100.0
            for day_index in range(days):
                close *= 1.0 + ticker_index * 0.0005 + day_index * 0.00001
                rows.append(
                    {
                        "date": (start + timedelta(days=day_index)).isoformat(),
                        "ticker": ticker,
                        "close": close,
                        "volume": 1_000_000 + ticker_index * 10_000 + day_index * 1_000,
                    }
                )
        return rows

    def test_factor_panel_uses_past_for_features_and_future_for_label(self) -> None:
        bars = []
        start = date(2026, 1, 1)
        for day_index in range(25):
            bars.append(
                {
                    "date": (start + timedelta(days=day_index)).isoformat(),
                    "ticker": "A",
                    "close": 100 + day_index,
                    "volume": 1000 + day_index,
                }
            )
        panel = factor_library.build_factor_panel(bars)
        first = panel[0]
        self.assertEqual(first["date"], (start + timedelta(days=20)).isoformat())
        self.assertAlmostEqual(first["momentum_5"], 120 / 115 - 1)
        self.assertAlmostEqual(first["forward_return"], 121 / 120 - 1)
        self.assertEqual(first["reversal_5"], -first["momentum_5"])

    def test_miner_runs_oos_cost_and_redundancy_without_trade_authority(self) -> None:
        result = alpha_miner.mine_alpha_candidates(self._bars())
        self.assertEqual(result["schema_version"], "cis.lightweight_alpha_research.v1")
        self.assertEqual(result["decision_authority"], "none")
        self.assertGreaterEqual(result["input"]["factors_tested"], 4)
        self.assertTrue(result["factors"])
        for factor in result["factors"]:
            self.assertGreaterEqual(factor["split"]["test_periods"], 3)
            zero_cost = factor["oos_cost_sensitivity"]["0bps"]
            high_cost = factor["oos_cost_sensitivity"]["20bps"]
            if zero_cost is not None and high_cost is not None:
                self.assertLessEqual(high_cost, zero_cost)
        reversal = next(item for item in result["factors"] if item["factor"] == "reversal_5")
        momentum = result["factor_correlations"]["reversal_5"]["momentum_5"]
        self.assertAlmostEqual(momentum, -1.0)
        self.assertIsNotNone(reversal["redundant_with"])


class ModelTestTests(unittest.TestCase):
    def test_requires_test_split_by_default(self) -> None:
        rows = [
            {"split": "train", "date": "2026-01-02", "ticker": "A", "prediction": 1, "forward_return": 0.01},
            {"split": "train", "date": "2026-01-02", "ticker": "B", "prediction": 2, "forward_return": 0.02},
            {"split": "train", "date": "2026-01-02", "ticker": "C", "prediction": 3, "forward_return": 0.03},
        ]
        with self.assertRaisesRegex(ValueError, "test split is required"):
            model_test.evaluate_model_rows(rows)

    def test_reports_present_oos_after_three_test_periods(self) -> None:
        rows = []
        for day in ("2026-01-02", "2026-01-05", "2026-01-06"):
            rows.extend(
                [
                    {"split": "test", "date": day, "ticker": "A", "prediction": 1, "forward_return": 0.01},
                    {"split": "test", "date": day, "ticker": "B", "prediction": 2, "forward_return": 0.02},
                    {"split": "test", "date": day, "ticker": "C", "prediction": 3, "forward_return": 0.03},
                ]
            )
        result = model_test.evaluate_model_rows(rows)
        self.assertEqual(result["oos_status"], "present")
        self.assertFalse(result["model_training_performed"])
        self.assertEqual(result["decision_authority"], "none")


if __name__ == "__main__":
    unittest.main()
