from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
SKILL = ROOT / "SKILL.md"
REFS = ROOT / "references"
REPO_ROOT = ROOT.parents[3]
REMOTE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "cis-tradingagents.yml"
DELETED_UPSTREAM_WATCH = REPO_ROOT / ".github" / "workflows" / "cis-tradingagents-upstream-watch.yml"
UPSTREAM_STATUS = REPO_ROOT / "runtime" / "tradingagents" / "upstream-status.json"
PLUGIN_JSON = ROOT.parents[1] / ".codex-plugin" / "plugin.json"
README = REPO_ROOT / "README.md"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{label} missing: {', '.join(missing)}")


def require_version(text: str, version: str, label: str) -> None:
    if version not in text:
        raise AssertionError(f"{label} is not aligned to {version}")


def main() -> int:
    version = "0.4.2"
    skill = read(SKILL)
    workflow = read(REFS / "system-workflow.md")
    registry = read(REFS / "module-registry.md")
    routing = read(REFS / "module-routing.md")
    external = read(REFS / "external-modules.md")
    methodology = read(REFS / "tradingagents-methodology.md")
    tradingagents = read(REFS / "tradingagents.md")
    anthropic = read(REFS / "anthropic-financial-services.md")
    orchestration = read(REFS / "agent-orchestration.md")
    agent_registry = read(REFS / "agent-registry.md")
    scoring = read(REFS / "scoring-engine.md")
    quant = read(REFS / "quant-engine.md")
    backtest = read(REFS / "backtest-validation.md")
    regime = read(REFS / "market-regime.md")
    performance = read(REFS / "performance-loop.md")
    remote_workflow = read(REMOTE_WORKFLOW)
    upstream_status_text = read(UPSTREAM_STATUS)
    plugin_json_text = read(PLUGIN_JSON)
    readme = read(README)

    score_script = read(ROOT / "scripts" / "score_cis.py")
    quant_script = read(ROOT / "scripts" / "quant_factor_engine.py")
    backtest_script = read(ROOT / "scripts" / "backtest_factor_strategy.py")
    regime_script = read(ROOT / "scripts" / "classify_market_regime.py")
    performance_script = read(ROOT / "scripts" / "evaluate_cis_predictions.py")
    ttl_script = read(ROOT / "scripts" / "check_tradingagents_upstream.py")
    ledger_script = read(ROOT / "scripts" / "prediction_ledger.py")
    local_ta = read(ROOT / "scripts" / "run_tradingagents.py")
    remote_ta = read(ROOT / "scripts" / "run_tradingagents_remote.py")
    score_tests = read(ROOT / "scripts" / "test_score_cis.py")
    hardening_tests = read(ROOT / "scripts" / "test_hardening.py")

    if DELETED_UPSTREAM_WATCH.exists():
        raise AssertionError("scheduled TradingAgents upstream watch must remain removed")

    for text, label in [
        (skill, "CIS skill"), (workflow, "system workflow"), (registry, "module registry"),
        (routing, "module routing"), (external, "external modules"),
        (methodology, "TradingAgents methodology"), (scoring, "scoring engine"),
        (quant, "quant policy"), (backtest, "backtest policy"), (regime, "market regime"),
        (performance, "performance loop"), (readme, "README"),
    ]:
        require_version(text, version, label)

    plugin_json = json.loads(plugin_json_text)
    if plugin_json.get("version") != version:
        raise AssertionError(f"plugin metadata version must equal {version}")

    require(skill, [
        "Fail-Closed", "Critical Dimension Gate", "check_tradingagents_upstream.py",
        "Prediction Ledger", "execution_status", "research_quality", "Quant Factor Ranking",
        "同一 as_of", "CIS 不自动下单",
    ], "CIS skill")
    require(workflow, ["fail-closed", "Critical Dimension Gate", "Prediction Ledger", "out-of-sample", "execution_status"], "workflow")
    require(registry, ["TradingAgents TTL Checker", "Quant Factor Ranking Engine", "Prediction Ledger", "fail_closed_gate"], "module registry")
    require(routing, ["Critical Dimension", "同一 `as_of`", "max_drawdown_1y", "Prediction Ledger", "execution_status"], "module routing")
    require(external, ["check_tradingagents_upstream.py", "execution_status", "evidence_audit_status", "research_quality", "不使用定时 GitHub Actions"], "external modules")
    require(methodology, ["7天 TTL", "check_tradingagents_upstream.py", "Critical Dimension", "execution_status"], "TradingAgents methodology")
    require(tradingagents, ["显式测试", "external_decision_candidate", "execution_status", "research_quality", "7 天 TTL"], "original TradingAgents runtime")
    require(anthropic, ["dcf-model", "comps-analysis", "earnings-analysis", "thesis-tracker"], "Anthropic policy")
    require(orchestration, ["多角色独立性", "Quant", "Market Regime", "Performance", "最终综合顺序"], "orchestration")
    require(agent_registry, ["Prediction Ledger", "Critical Dimension Gate", "TradingAgents TTL Checker", "Research Manager"], "agent registry")
    require(scoring, ["audit_status = unverified", "risk_status  = unverified", "Critical Dimension Gate", "valuation", "decision_grade"], "scoring")
    require(quant, ["quant_score", "cis_score", "experimental_uncalibrated", "point-in-time", "max_drawdown_1y"], "quant policy")
    require(backtest, ["one_way_turnover", "out_of_sample", "交易成本", "换手"], "backtest policy")
    require(regime, ["JSON boolean", "high_yield_oas_bps", "realized_vol_20d", "experimental_baseline"], "market regime")
    require(performance, ["predictions.jsonl", "append-only", "horizon", "dimension", "禁止"], "performance loop")

    require(score_script, ["audit_status: str = \"unverified\"", "risk_status: str = \"unverified\"", "CRITICAL_DIMENSIONS", "critical_dimensions_missing"], "score script")
    require(quant_script, ["transform_value", "validate_as_of", "same as_of", '"transform": "abs"'], "quant script")
    require(backtest_script, ["one_way_turnover", "transaction_cost", "metrics_by_segment", "out_of_sample"], "backtest script")
    require(regime_script, ["strict_bool", "high_yield_oas_bps", "realized_vol_20d", "SIGNAL_WEIGHTS"], "regime script")
    require(performance_script, ["horizon_bucket", "dimension_diagnostics", "max_drawdown", "falsifier_triggered"], "performance script")
    require(ttl_script, ["should_check", "apply_check", "check_ttl_days", "fetch_current_sha"], "TTL script")
    require(ledger_script, ["event_type", "prediction", "outcome", "research_id", "append_event"], "prediction ledger")
    require(local_ta, ["execution_status", "evidence_audit_status", "research_quality", "external_decision_candidate"], "local TradingAgents adapter")
    require(remote_ta, ["execution_status", "evidence_audit_status", "research_quality", "external_decision_candidate"], "remote TradingAgents adapter")
    require(score_tests, ["unittest.TestCase", "test_defaults_are_fail_closed", "test_missing_valuation_cannot_be_decision_grade"], "score tests")
    require(hardening_tests, ["TradingAgentsTTLTests", "PredictionLedgerTests", "TradingAgentsAdapterTests"], "hardening tests")

    require(remote_workflow, [
        "workflow_dispatch", "request_id:", "ticker:", "analysis_date:",
        "OPENAI_COMPATIBLE_API_KEY", "TRADINGAGENTS_API_KEY", "NVIDIA_API_KEY",
        "Build explicit manual request",
    ], "original TradingAgents workflow")

    upstream_status = json.loads(upstream_status_text)
    if int(upstream_status.get("check_ttl_days", 0)) != 7:
        raise AssertionError("TradingAgents check_ttl_days must equal 7")
    require(upstream_status_text, ["observed_sha", "reviewed_sha", "review_status", "last_checked_at", "next_check_not_before", "use_time_check_with_7_day_ttl_stable_baseline"], "upstream status")

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    forbidden_bundles = [SKILLS_ROOT / "public-equity-investing", SKILLS_ROOT / "tradingagents"]
    for path in forbidden_bundles:
        if path.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {path.name}")

    print(f"CIS {version} plugin validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
