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
EXT = REPO_ROOT / "extensions" / "research_tooling"
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
    version = "0.4.4"
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
    regime = read(REFS / "market-regime.md")
    evidence = read(REFS / "evidence-confidence.md")
    trading_framework = read(REFS / "four-layer-trading-framework.md")
    remote_workflow = read(REMOTE_WORKFLOW)
    upstream_status_text = read(UPSTREAM_STATUS)
    plugin_json_text = read(PLUGIN_JSON)
    readme = read(README)
    extension_readme = read(EXT / "README.md")

    for text, label in [
        (skill, "CIS skill"),
        (workflow, "system workflow"),
        (registry, "module registry"),
        (routing, "module routing"),
        (external, "external modules"),
        (methodology, "TradingAgents methodology"),
        (scoring, "scoring engine"),
        (regime, "market regime"),
        (evidence, "evidence confidence"),
        (readme, "README"),
    ]:
        require_version(text, version, label)

    plugin_json = json.loads(plugin_json_text)
    if plugin_json.get("version") != version:
        raise AssertionError(f"plugin metadata version must equal {version}")

    require(skill, [
        "CIS Core", "Optional Research Tooling", "extensions/research_tooling/",
        "Fail-Closed Evidence", "Critical Dimension Gate", "check_tradingagents_upstream.py",
        "execution_status", "research_quality", "CIS 不自动下单",
        "Tactical R/R Gate", "Evidence Freshness", "tactical_setup_gate.py",
        "Exchange-aware Price / Session Guard", "Quote Freshness", "Setup 生命周期",
        "us_nasdaq_v1", "Tactical Setup Readiness",
    ], "CIS skill")
    require(workflow, [
        "Core Research", "Optional Research Tooling", "extensions/research_tooling/", "fail-closed",
        "Exchange-aware Price/Session Guard", "Quote Freshness Guard", "signal_as_of",
        "invalidated_reprice_required", "setup_expired_reprice_required", "regime_profile",
    ], "workflow")
    require(registry, [
        "Core Analysis", "Extension", "Quant Factor Ranking Engine", "Prediction / Evaluation",
        "Price / Session Guard", "Tactical R/R Gate",
    ], "module registry")
    require(routing, [
        "Optional Research Tooling", "extensions/research_tooling/", "Critical Dimension", "7 天 TTL",
        "tactical_setup_gate.py", "catalyst_event_review", "quote_max_age_seconds",
        "blocked_pending_stop_confirmation", "us_broad_v1",
    ], "module routing")
    require(external, [
        "7 天 TTL", "execution_status", "research_quality", "Optional Research Tooling", "Market Regime",
        "Tactical Price/RR Gate",
    ], "external modules")
    require(methodology, [
        "7天 TTL", "check_tradingagents_upstream.py", "Critical Dimension", "execution_status",
        "Tactical Price/RR Gate",
    ], "TradingAgents methodology")
    require(tradingagents, ["显式测试", "external_decision_candidate", "execution_status", "research_quality", "7 天 TTL"], "original TradingAgents runtime")
    require(anthropic, ["dcf-model", "comps-analysis", "earnings-analysis", "thesis-tracker", "上游 `main`"], "Anthropic policy")
    require(orchestration, ["Optional Research Tooling", "多角色独立性", "最终综合顺序"], "orchestration")
    require(agent_registry, ["CIS Core", "Optional Research Tooling", "Research Manager", "TradingAgents TTL Checker"], "agent registry")
    require(scoring, [
        "audit_status = unverified", "risk_status  = unverified", "Critical Dimension / Context Check Gate",
        "decision_grade", "price_context=True", "catalyst_event_review=True",
    ], "scoring")
    require(regime, [
        "JSON boolean", "high_yield_oas_bps", "realized_vol_20d", "experimental_baseline",
        "signal_as_of", "freshness", "us_broad_v1", "excluded_signals", "fresh coverage",
    ], "market regime")
    require(evidence, [
        "Evidence Freshness Guard", "last_close", "tactical_setup_gate.py", "Evidence Audit 不得 `pass`",
        "quote_max_age_seconds", "exchange + timestamp",
    ], "evidence confidence")
    require(trading_framework, [
        "Tactical Price / Session Guard", "Tactical Risk / Reward Gate", "blocked_do_not_chase", "Entry Zone",
        "hard_price", "close_confirmation", "invalidated_reprice_required", "setup_expired_reprice_required",
    ], "trading framework")
    require(extension_readme, [
        "CIS Core", "可选外围研究工具", "故障不得阻塞 CIS Core", "5 / 20 / 60 trading days",
        "adjusted_close_only",
    ], "research tooling extension")

    core_scripts = ROOT / "scripts"
    required_core = [
        "score_cis.py",
        "analyze_etf_premium.py",
        "classify_market_regime.py",
        "tactical_setup_gate.py",
        "check_tradingagents_upstream.py",
        "run_tradingagents.py",
        "run_tradingagents_remote.py",
        "validate_cis.py",
        "test_score_cis.py",
        "test_analyze_etf_premium.py",
        "test_hardening.py",
        "test_systematic_layers.py",
        "test_tactical_setup_gate.py",
    ]
    for name in required_core:
        read(core_scripts / name)

    optional_names = [
        "quant_factor_engine.py",
        "backtest_factor_strategy.py",
        "prediction_ledger.py",
        "record_cis_research.py",
        "settle_due_predictions.py",
        "evaluate_cis_predictions.py",
    ]
    for name in optional_names:
        if (core_scripts / name).exists():
            raise AssertionError(f"optional research tool leaked into CIS Core: {name}")
        read(EXT / name)
    extension_tests = read(EXT / "test_research_tooling.py")

    score_script = read(core_scripts / "score_cis.py")
    regime_script = read(core_scripts / "classify_market_regime.py")
    tactical_script = read(core_scripts / "tactical_setup_gate.py")
    ttl_script = read(core_scripts / "check_tradingagents_upstream.py")
    local_ta = read(core_scripts / "run_tradingagents.py")
    remote_ta = read(core_scripts / "run_tradingagents_remote.py")
    score_tests = read(core_scripts / "test_score_cis.py")
    tactical_tests = read(core_scripts / "test_tactical_setup_gate.py")
    hardening_tests = read(core_scripts / "test_hardening.py")
    systematic_tests = read(core_scripts / "test_systematic_layers.py")

    ledger_script = read(EXT / "prediction_ledger.py")
    recorder_script = read(EXT / "record_cis_research.py")
    settlement_script = read(EXT / "settle_due_predictions.py")

    require(score_script, [
        "audit_status: str = \"unverified\"", "risk_status: str = \"unverified\"", "CRITICAL_DIMENSIONS",
        "TACTICAL_REQUIRED_CHECKS", "VALID_AUDIT_STATUSES", "tactical_checks_incomplete", "_strict_bool",
    ], "score script")
    require(regime_script, [
        "strict_bool", "high_yield_oas_bps", "realized_vol_20d", "SIGNAL_WEIGHTS",
        "MAX_SIGNAL_AGE_DAYS", "REGIME_PROFILES", "excluded_signals", "not JSON boolean",
    ], "regime script")
    require(tactical_script, [
        "validate_price_context", "evaluate_tactical_setup", "EXPECTED_PRICE_TYPE", "blocked_do_not_chase",
        "rr_target1_worst", "last_close_reference", "SUPPORTED_EXCHANGES", "quote_max_age_seconds",
        "STOP_TYPES", "invalidated_reprice_required", "setup_expired_reprice_required",
    ], "tactical setup script")
    require(ttl_script, ["should_check", "apply_check", "check_ttl_days", "fetch_current_sha"], "TTL script")
    require(local_ta, ["execution_status", "evidence_audit_status", "research_quality", "external_decision_candidate"], "local TradingAgents adapter")
    require(remote_ta, ["execution_status", "evidence_audit_status", "research_quality", "external_decision_candidate"], "remote TradingAgents adapter")
    require(score_tests, [
        "unittest.TestCase", "test_defaults_are_fail_closed", "test_missing_valuation_cannot_be_decision_grade",
        "test_string_false_is_rejected_for_critical_blocked", "test_tactical_requires_price_and_catalyst_checks",
    ], "score tests")
    require(tactical_tests, [
        "TacticalSetupGateTests", "test_weekend_cannot_pretend_to_be_regular_session",
        "test_stale_live_quote_is_rejected", "test_stop_breach_invalidates_hard_stop_setup",
        "test_target1_reached_requires_repricing",
    ], "tactical setup tests")
    require(systematic_tests, [
        "test_numeric_signal_rejects_json_boolean",
        "test_one_stale_signal_is_excluded_when_fresh_coverage_remains_sufficient",
        "test_many_stale_signals_can_still_force_insufficient",
    ], "systematic layer tests")
    require(hardening_tests, ["TradingAgentsTTLTests", "TradingAgentsAdapterTests"], "hardening tests")

    require(ledger_script, ["DEFAULT_HORIZONS_TRADING_DAYS = (5, 20, 60)", "append_event", "record_prediction"], "prediction ledger")
    require(recorder_script, ["CIS_VERSION = \"0.4.4\"", "record_snapshot"], "research recorder")
    require(settlement_script, [
        "_first_index_after", "benchmark_sessions:", "path_metric_basis", "adjusted_close_only",
        "no executable stock price",
    ], "settlement script")
    require(extension_tests, [
        "ResearchRecorderTests", "SettlementTests", "test_default_horizons_are_tactical",
        "test_settlement_enters_after_research_date_and_uses_benchmark_sessions",
    ], "research tooling tests")

    require(remote_workflow, [
        "workflow_dispatch", "request_id:", "ticker:", "analysis_date:",
        "OPENAI_COMPATIBLE_API_KEY", "TRADINGAGENTS_API_KEY", "NVIDIA_API_KEY",
        "Build explicit manual request",
    ], "original TradingAgents workflow")

    upstream_status = json.loads(upstream_status_text)
    if int(upstream_status.get("check_ttl_days", 0)) != 7:
        raise AssertionError("TradingAgents check_ttl_days must equal 7")
    require(upstream_status_text, [
        "observed_sha", "reviewed_sha", "review_status", "last_checked_at",
        "next_check_not_before", "use_time_check_with_7_day_ttl_stable_baseline",
    ], "upstream status")

    if DELETED_UPSTREAM_WATCH.exists():
        raise AssertionError("scheduled TradingAgents upstream watch must remain removed")

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    forbidden_bundles = [SKILLS_ROOT / "public-equity-investing", SKILLS_ROOT / "tradingagents"]
    for path in forbidden_bundles:
        if path.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {path.name}")

    print(f"CIS {version} tactical edge-case validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError, ValueError) as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
