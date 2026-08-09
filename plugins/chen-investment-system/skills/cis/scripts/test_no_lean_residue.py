from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
CIS_ROOT = ROOT / "plugins" / "chen-investment-system" / "skills" / "cis"
ACTIVE_DOCS = (
    ROOT / "README.md",
    ROOT / "AGENT_ARCHITECTURE.md",
    CIS_ROOT / "SKILL.md",
    CIS_ROOT / "references" / "system-workflow.md",
    CIS_ROOT / "references" / "module-registry.md",
    CIS_ROOT / "references" / "module-routing.md",
    CIS_ROOT / "references" / "external-modules.md",
    CIS_ROOT / "references" / "backtest-validation.md",
    CIS_ROOT / "references" / "integration-decisions.md",
    ROOT / "extensions" / "research_tooling" / "README.md",
)
FORBIDDEN_TOKENS = (
    "QuantConnect",
    "integrations/lean",
    "quantconnect-lean",
    "cis-lean-qqq-engine-test",
    "quantconnect/lean",
)


class NoLeanResidueTests(unittest.TestCase):
    def test_lean_integration_paths_are_absent(self) -> None:
        self.assertFalse((ROOT / "integrations" / "lean").exists())
        self.assertFalse((ROOT / ".github" / "workflows" / "cis-lean-qqq-engine-test.yml").exists())
        self.assertFalse((CIS_ROOT / "references" / "quantconnect-lean.md").exists())

    def test_active_contract_docs_have_no_lean_integration_references(self) -> None:
        for path in ACTIVE_DOCS:
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_TOKENS:
                self.assertNotIn(token, text, f"{token!r} remains in {path.relative_to(ROOT)}")

    def test_upstream_status_has_no_lean_component(self) -> None:
        status_path = ROOT / "runtime" / "tradingagents" / "upstream-status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertNotIn("lean", status)
        self.assertEqual(status.get("upstream"), "TauricResearch/TradingAgents")

    def test_upstream_checker_has_no_lean_runtime_hooks(self) -> None:
        checker = (CIS_ROOT / "scripts" / "check_tradingagents_upstream.py").read_text(encoding="utf-8")
        for token in ("LEAN_TAGS_API", "apply_lean_check", "fetch_latest_lean_tag", "quantconnect/lean"):
            self.assertNotIn(token, checker)


if __name__ == "__main__":
    unittest.main()
