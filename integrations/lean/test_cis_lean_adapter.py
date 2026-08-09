from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cis_lean_adapter import (
    build_backtest_command,
    check_readiness,
    discover_result_file,
    parse_result_file,
    parse_result_payload,
    run_backtest,
)


class LeanResultParsingTests(unittest.TestCase):
    def test_parses_standard_statistics_into_cis_contract(self) -> None:
        payload = {
            "runtimeStatistics": {"Return": "25.00%"},
            "statistics": {
                "Compounding Annual Return": "18.50%",
                "Drawdown": "12.25%",
                "Sharpe Ratio": "1.42",
                "Sortino Ratio": "1.88",
                "Net Profit": "25.00%",
                "Win Rate": "61.00%",
                "Loss Rate": "39.00%",
                "Profit-Loss Ratio": "1.70",
                "Annual Standard Deviation": "22.00%",
                "Total Orders": "48",
                "Total Fees": "$123.45",
            },
        }
        result = parse_result_payload(payload)
        self.assertEqual(result["schema_version"], "cis.lean.backtest.v1")
        self.assertEqual(result["engine"], "QuantConnect LEAN")
        self.assertEqual(result["decision_authority"], "none")
        self.assertEqual(result["research_quality"], "unreviewed")
        self.assertAlmostEqual(result["metrics"]["cagr"], 0.185)
        self.assertAlmostEqual(result["metrics"]["max_drawdown"], 0.1225)
        self.assertAlmostEqual(result["metrics"]["sharpe_ratio"], 1.42)
        self.assertEqual(result["metrics"]["total_orders"], 48)
        self.assertEqual(result["metrics"]["total_fees_raw"], "$123.45")

    def test_parses_nested_portfolio_statistics(self) -> None:
        payload = {
            "totalPerformance": {
                "portfolioStatistics": {
                    "compoundingAnnualReturn": "12.00%",
                    "drawdown": "8.00%",
                    "sharpeRatio": "1.1",
                    "winRate": "55.00%",
                }
            }
        }
        result = parse_result_payload(payload)
        self.assertAlmostEqual(result["metrics"]["cagr"], 0.12)
        self.assertAlmostEqual(result["metrics"]["max_drawdown"], 0.08)
        self.assertAlmostEqual(result["metrics"]["win_rate"], 0.55)

    def test_rejects_json_without_backtest_statistics(self) -> None:
        with self.assertRaisesRegex(ValueError, "recognizable backtest statistics"):
            parse_result_payload({"runtimeStatistics": {"Return": "5%"}})

    def test_discovers_result_and_ignores_order_event_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "123-order-events.json").write_text(json.dumps({"events": []}), encoding="utf-8")
            (root / "123.json").write_text(json.dumps({
                "statistics": {
                    "Compounding Annual Return": "9%",
                    "Drawdown": "4%",
                    "Sharpe Ratio": "1.2",
                }
            }), encoding="utf-8")
            found = discover_result_file(root)
            self.assertEqual(found.name, "123.json")
            parsed = parse_result_file(found)
            self.assertAlmostEqual(parsed["metrics"]["cagr"], 0.09)


class LeanRuntimeTests(unittest.TestCase):
    def test_builds_official_local_backtest_command(self) -> None:
        command = build_backtest_command("/tmp/project", "/tmp/results", update_image=True)
        self.assertEqual(command[:2], ["lean", "backtest"])
        self.assertIn("--output", command)
        self.assertEqual(command[-1], "--update")

    @patch("cis_lean_adapter.shutil.which")
    def test_readiness_is_unavailable_when_cli_or_docker_missing(self, which) -> None:
        which.side_effect = lambda value: None if value == "lean" else "/usr/bin/docker"
        result = check_readiness()
        self.assertEqual(result["runtime_readiness"], "unavailable")
        self.assertIn("lean_cli", result["missing"])
        self.assertEqual(result["account_entitlement"], "not_checked")

    @patch("cis_lean_adapter.shutil.which", return_value=None)
    def test_backtest_fails_closed_when_lean_cli_missing(self, _which) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            result = run_backtest(project, Path(tmp) / "results")
        self.assertEqual(result["execution_status"], "unavailable")
        self.assertEqual(result["decision_authority"], "none")
        self.assertEqual(result["runtime_readiness"], "lean_cli_missing")

    @patch("cis_lean_adapter.shutil.which")
    def test_backtest_fails_closed_when_docker_missing(self, which) -> None:
        which.side_effect = lambda value: "/usr/bin/lean" if value == "lean" else None
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            result = run_backtest(project, Path(tmp) / "results")
        self.assertEqual(result["execution_status"], "unavailable")
        self.assertEqual(result["runtime_readiness"], "docker_missing")


if __name__ == "__main__":
    unittest.main()
