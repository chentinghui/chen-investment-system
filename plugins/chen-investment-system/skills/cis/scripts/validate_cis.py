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
VALIDATE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "cis-validate.yml"
DELETED_UPSTREAM_WATCH = REPO_ROOT / ".github" / "workflows" / "cis-tradingagents-upstream-watch.yml"
UPSTREAM_STATUS = REPO_ROOT / "runtime" / "tradingagents" / "upstream-status.json"
PLUGIN_JSON = ROOT.parents[1] / ".codex-plugin" / "plugin.json"
README = REPO_ROOT / "README.md"
ROOT_ARCHITECTURE = REPO_ROOT / "AGENT_ARCHITECTURE.md"
AGENTS_README = ROOT.parents[1] / "agents" / "README.md"
EVIDENCE_AGENT = ROOT.parents[1] / "agents" / "evidence-auditor.md"
RISK_AGENT = ROOT.parents[1] / "agents" / "risk-manager.md"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{label} missing: {', '.join(missing)}")


def forbid(text: str, tokens: list[str], label: str) -> None:
    present = [token for token in tokens if token in text]
    if present:
        raise AssertionError(f"{label} contains forbidden legacy/security tokens: {', '.join(present)}")


def require_version(text: str, version: str, label: str) -> None:
    if version not in text:
        raise AssertionError(f"{label} is not aligned to {version}")


def main() -> int:
    version = "0.4.5"
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
    agent_contract = read(REFS / "agent-contract.md")
    scoring = read(REFS / "scoring-engine.md")
    regime = read(REFS / "market-regime.md")
    evidence = read(REFS / "evidence-confidence.md")
    trading_framework = read(REFS / "four-layer-trading-framework.md")
    etf_reference = read(REFS / "cross-border-etf-premium.md")
    quant_reference = read(REFS / "quant-engine.md")
    backtest_reference = read(REFS / "backtest-validation.md")
    performance_reference = read(REFS / "performance-loop.md")
    evaluation_cases = read(REFS / "evaluation-cases.md")
    remote_workflow = read(REMOTE_WORKFLOW)
    validate_workflow = read(VALIDATE_WORKFLOW)
    upstream_status_text = read(UPSTREAM_STATUS)
    plugin_json_text = read(PLUGIN_JSON)
    readme = read(README)
    root_architecture = read(ROOT_ARCHITECTURE)
    agents_readme = read(AGENTS_README)
    evidence_agent = read(EVIDENCE_AGENT)
    risk_agent = read(RISK_AGENT)
    extension_readme = read(EXT / "README.md")

    versioned_docs = [
        (skill, "CIS skill"),
        (workflow, "system workflow"),
        (registry, "module registry"),
        (routing, "module routing"),
        (external, "external modules"),
        (methodology, "TradingAgents methodology"),
        (tradingagents, "original TradingAgents runtime"),
        (orchestration, "agent orchestration"),
        (agent_registry, "agent registry"),
        (agent_contract, "agent contract"),
        (scoring, "scoring engine"),
        (regime, "market regime"),
        (evidence, "evidence confidence"),
        (trading_framework, "four-layer framework"),
        (etf_reference, "ETF premium discipline"),
        (quant_reference, "quant engine"),
        (backtest_reference, "backtest policy"),
        (performance_reference, "performance loop"),
        (evaluation_cases, "evaluation cases"),
        (readme, "README"),
        (root_architecture, "root architecture"),
        (agents_readme, "agents README"),
        (extension_readme, "extension README"),
    ]
    for text, label in versioned_docs:
        require_version(text, version, label)

    plugin_json = json.loads(plugin_json_text)
    if plugin_json.get("version") != version:
        raise AssertionError(f"plugin metadata version must equal {version}")

    require(skill, [
        "CIS Core", "Optional Research Tooling", "extensions/research_tooling/",
        "Fail-Closed Evidence", "Critical Dimension Gate", "check_tradingagents_upstream.py",
        "execution_status", "research_quality", "CIS 不自动下单",
        "Tactical R/R Gate", "Evidence Freshness", "tactical_setup_gate.py",
        "Quote Freshness", "Setup 生命周期", "quote observation session",
        "US-equity common session baseline", "reviewed_sha", "trusted publisher",
        "allowlist", "unique `research_id`",
    ], "CIS skill")
    require(workflow, [
        "Core Research", "Optional Research Tooling", "extensions/research_tooling/", "fail-closed",
        "Quote Freshness", "signal_as_of", "invalidated_reprice_required",
        "setup_expired_reprice_required", "regime_profile", "唯一日期", "allowlist",
    ], "workflow")
    require(registry, [
        "Core Analysis", "Extension", "Quant Factor Ranking Engine", "Prediction / Evaluation",
        "Price / Session Guard", "Tactical R/R Gate", "trusted publisher", "reviewed_sha",
    ], "module registry")
    require(routing, [
        "Optional Research Tooling", "extensions/research_tooling/", "Critical Dimension", "7 天 TTL",
        "tactical_setup_gate.py", "catalyst_event_review", "quote_max_age_seconds",
        "blocked_pending_stop_confirmation", "us_broad_v1", "unique `research_id`",
        "Trusted Publisher", "NVIDIA_API_KEY", "OPENAI_COMPATIBLE_API_KEY",
    ], "module routing")
    require(external, [
        "7 天 TTL", "execution_status", "research_quality", "Optional Research Tooling", "Market Regime",
        "reviewed_sha", "NVIDIA_API_KEY", "OPENAI_COMPATIBLE_API_KEY",
    ], "external modules")
    require(methodology, [
        "7天 TTL", "check_tradingagents_upstream.py", "Critical Dimension", "execution_status",
        "Agent ↔ Score 契约", "reviewed_sha", "quote observation session",
    ], "TradingAgents methodology")
    require(tradingagents, [
        "显式测试", "external_decision_candidate", "execution_status", "research_quality", "7 天 TTL",
        "contents: read", "Trusted Publisher", "reviewed_sha", "provider_profile",
    ], "original TradingAgents runtime")
    require(anthropic, ["dcf-model", "comps-analysis", "earnings-analysis", "thesis-tracker", "上游 `main`"], "Anthropic policy")
    require(orchestration, ["Optional Research Tooling", "多角色独立性", "最终综合顺序", "contents: read"], "orchestration")
    require(agent_registry, ["CIS Core", "Optional Research Tooling", "Research Manager", "TradingAgents TTL Checker", "risk_status"], "agent registry")
    require(agent_contract, [
        "audit_status = unverified | pass | fail | unresolved",
        "risk_status = unverified | pass | fail | unresolved",
        "risk_override = none | block",
    ], "agent contract")
    require(scoring, [
        "audit_status = unverified", "risk_status  = unverified", "Critical Dimension / Context Check Gate",
        "decision_grade", "price_context=True", "catalyst_event_review=True", "必填", "持久失效",
    ], "scoring")
    require(regime, [
        "JSON boolean", "high_yield_oas_bps", "realized_vol_20d", "experimental_baseline",
        "signal_as_of", "freshness", "us_broad_v1", "excluded_signals", "fresh coverage",
    ], "market regime")
    require(evidence, [
        "Evidence Freshness Guard", "last_close", "tactical_setup_gate.py", "Evidence Audit 不得 `pass`",
        "quote_max_age_seconds", "quote observation session", "US-equity common session baseline",
    ], "evidence confidence")
    require(trading_framework, [
        "Tactical Price / Session Guard", "Tactical Risk / Reward Gate", "blocked_do_not_chase", "Entry Zone",
        "hard_price", "close_confirmation", "technical_invalidation", "Stop Type（必填）", "旧计划也不能复活",
    ], "trading framework")
    require(etf_reference, ["唯一日期", "JSON boolean", "20 个有效"], "ETF reference")
    require(quant_reference, ["ticker 必须唯一", "min_factor_observations", "有限正数"], "quant reference")
    require(backtest_reference, ["Cross-section uniqueness", "(date,ticker)", "低于 -100%"], "backtest reference")
    require(performance_reference, ["unique `research_id`", "相关结果", "pooled correlation", "allowlist", "next_session_close_to_close_adjusted_price_return"], "performance reference")
    require(extension_readme, [
        "CIS Core", "可选外围研究工具", "5 / 20 / 60 trading days", "allowlist",
        "next_session_close_to_close_adjusted_price_return", "unique `research_id`",
    ], "research tooling extension")
    require(root_architecture, ["ChatGPT-native TradingAgents Methodology", "Core 与 Extension", "contents: read", "risk_status"], "root architecture")
    require(agents_readme, ["ChatGPT-native TradingAgents Methodology", "risk_status", "extensions/research_tooling/"], "agents README")

    # Machine-facing Agent contracts must exactly align with score_cis.py.
    require(evidence_agent, ["audit_status: pass | unresolved | fail", "`conditional` 不再作为机器接口状态"], "evidence auditor")
    require(risk_agent, ["risk_status: pass | unresolved | fail", "risk_override: none | block", "不再使用机器枚举 `caution`"], "risk manager")

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
    etf_script = read(core_scripts / "analyze_etf_premium.py")
    score_tests = read(core_scripts / "test_score_cis.py")
    tactical_tests = read(core_scripts / "test_tactical_setup_gate.py")
    hardening_tests = read(core_scripts / "test_hardening.py")
    systematic_tests = read(core_scripts / "test_systematic_layers.py")

    quant_script = read(EXT / "quant_factor_engine.py")
    backtest_script = read(EXT / "backtest_factor_strategy.py")
    ledger_script = read(EXT / "prediction_ledger.py")
    recorder_script = read(EXT / "record_cis_research.py")
    settlement_script = read(EXT / "settle_due_predictions.py")
    evaluation_script = read(EXT / "evaluate_cis_predictions.py")

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
        "quote_observation_session", "stop_type is required", "invalidation_confirmed",
        "invalidated_reprice_required", "setup_expired_reprice_required",
    ], "tactical setup script")
    require(etf_script, ["isinstance(value, bool)", "duplicate historical premium date", "unique_dates", ".date is required"], "ETF premium script")
    require(ttl_script, ["should_check", "apply_check", "check_ttl_days", "fetch_current_sha"], "TTL script")
    require(local_ta, ["execution_status", "evidence_audit_status", "research_quality", "external_decision_candidate"], "local TradingAgents adapter")
    require(remote_ta, [
        "ALLOWED_REQUEST_FIELDS", "provider_profile", "NVIDIA_BASE_URL", "credential_env",
        "unknown or forbidden request fields", "NVIDIA_API_KEY", "OPENAI_COMPATIBLE_API_KEY",
        "external_decision_candidate",
    ], "remote TradingAgents adapter")
    forbid(remote_ta, ["TRADINGAGENTS_API_KEY"], "remote TradingAgents adapter")

    require(score_tests, [
        "unittest.TestCase", "test_defaults_are_fail_closed", "test_missing_valuation_cannot_be_decision_grade",
        "test_string_false_is_rejected_for_critical_blocked", "test_tactical_requires_price_and_catalyst_checks",
    ], "score tests")
    require(tactical_tests, [
        "TacticalSetupGateTests", "test_weekend_cannot_pretend_to_be_regular_session",
        "test_regular_session_rejects_premarket_observation_even_if_age_is_allowed",
        "test_stop_type_is_required", "test_confirmed_stop_remains_invalidated_after_price_recovers",
        "test_technical_invalidation_can_invalidate_without_numeric_stop_breach",
    ], "tactical setup tests")
    require(systematic_tests, [
        "test_numeric_signal_rejects_json_boolean",
        "test_one_stale_signal_is_excluded_when_fresh_coverage_remains_sufficient",
        "test_many_stale_signals_can_still_force_insufficient",
    ], "systematic layer tests")
    require(hardening_tests, [
        "TradingAgentsTTLTests", "TradingAgentsAdapterTests",
        "test_nvidia_key_cannot_be_routed_to_arbitrary_endpoint",
        "test_unknown_request_fields_are_rejected_to_avoid_secret_echo",
    ], "hardening tests")

    require(quant_script, ["duplicate ticker in cross-section", "MIN_FACTOR_OBSERVATIONS", "positive finite number"], "quant script")
    require(backtest_script, ["duplicate ticker within period", "below -100%", "finite non-negative"], "backtest script")
    require(ledger_script, [
        "DEFAULT_HORIZONS_TRADING_DAYS = (5, 20, 60)", "PUBLIC_PREDICTION_ALLOWED_FIELDS",
        "PUBLIC_OUTCOME_ALLOWED_FIELDS", "not allowed in the public ledger", "schema_version", "record_prediction",
    ], "prediction ledger")
    require(recorder_script, ["CIS_VERSION = \"0.4.5\"", "PUBLIC_PREDICTION_ALLOWED_FIELDS", "record_snapshot"], "research recorder")
    require(settlement_script, [
        "_first_index_after", "benchmark_sessions:", "path_metric_basis", "adjusted_close_only",
        "next_session_close_to_close_adjusted_price_return", "terminal_event_handling",
        "no usable adjusted closes",
    ], "settlement script")
    require(evaluation_script, [
        "mixed_horizons", "unique_research_count", "horizon_diagnostics",
        "Correlations are never pooled across different horizons",
    ], "evaluation script")
    require(extension_tests, [
        "ResearchRecorderTests", "SettlementTests", "test_default_horizons_are_tactical",
        "test_duplicate_ticker_is_rejected", "test_duplicate_period_ticker_is_rejected",
        "test_public_ledger_rejects_unapproved_free_form_fields",
        "test_mixed_horizons_do_not_pool_correlations_or_inflate_unique_research",
    ], "research tooling tests")

    # Workflow security invariant: untrusted third-party code never runs with the
    # repository write token, and cloud credentials are provider-specific.
    require(remote_workflow, [
        "permissions:\n  contents: read", "provider_profile:", "reviewed_sha",
        "Install pinned TradingAgents upstream", "PINNED_SHA", "actions/upload-artifact@v4",
        "actions/download-artifact@v4", "Trusted Publisher", "contents: write",
        "NVIDIA_API_KEY", "OPENAI_COMPATIBLE_API_KEY",
    ], "original TradingAgents workflow")
    forbid(remote_workflow, ["TRADINGAGENTS_API_KEY", "git clone --depth 1 https://github.com/TauricResearch/TradingAgents.git"], "original TradingAgents workflow")

    require(validate_workflow, [
        "Compile CIS Core", "Compile Optional Research Tooling", "Run CIS Core unit tests",
        "Run Optional Research Tooling unit tests",
    ], "CIS validate workflow")

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

    print(f"CIS {version} contract and security validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError, ValueError) as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
