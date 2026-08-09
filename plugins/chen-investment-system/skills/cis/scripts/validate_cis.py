from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CIS_VERSION = "0.4.5"
ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT.parents[1]
REPO_ROOT = ROOT.parents[3]
REFS = ROOT / "references"
SCRIPTS = ROOT / "scripts"
EXT = REPO_ROOT / "extensions" / "research_tooling"
LEAN = REPO_ROOT / "integrations" / "lean"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, tokens: tuple[str, ...], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{label} missing contract tokens: {', '.join(missing)}")


def forbid(text: str, tokens: tuple[str, ...], label: str) -> None:
    present = [token for token in tokens if token in text]
    if present:
        raise AssertionError(f"{label} contains forbidden tokens: {', '.join(present)}")


def require_version(text: str, label: str) -> None:
    if CIS_VERSION not in text:
        raise AssertionError(f"{label} is not aligned to CIS {CIS_VERSION}")


def main() -> int:
    skill = read(ROOT / "SKILL.md")
    docs = {
        "system workflow": read(REFS / "system-workflow.md"),
        "module registry": read(REFS / "module-registry.md"),
        "module routing": read(REFS / "module-routing.md"),
        "external modules": read(REFS / "external-modules.md"),
        "TradingAgents methodology": read(REFS / "tradingagents-methodology.md"),
        "original TradingAgents": read(REFS / "tradingagents.md"),
        "agent orchestration": read(REFS / "agent-orchestration.md"),
        "agent registry": read(REFS / "agent-registry.md"),
        "agent contract": read(REFS / "agent-contract.md"),
        "scoring": read(REFS / "scoring-engine.md"),
        "regime": read(REFS / "market-regime.md"),
        "evidence": read(REFS / "evidence-confidence.md"),
        "four-layer": read(REFS / "four-layer-trading-framework.md"),
        "ETF premium": read(REFS / "cross-border-etf-premium.md"),
        "quant": read(REFS / "quant-engine.md"),
        "QuantConnect LEAN": read(REFS / "quantconnect-lean.md"),
        "backtest": read(REFS / "backtest-validation.md"),
        "performance": read(REFS / "performance-loop.md"),
        "evaluation cases": read(REFS / "evaluation-cases.md"),
        "root README": read(REPO_ROOT / "README.md"),
        "root architecture": read(REPO_ROOT / "AGENT_ARCHITECTURE.md"),
        "agents README": read(PLUGIN_ROOT / "agents" / "README.md"),
        "extension README": read(EXT / "README.md"),
        "LEAN integration README": read(LEAN / "README.md"),
    }
    require_version(skill, "CIS skill")
    for label, text in docs.items():
        require_version(text, label)

    plugin_json = json.loads(read(PLUGIN_ROOT / ".codex-plugin" / "plugin.json"))
    if plugin_json.get("version") != CIS_VERSION:
        raise AssertionError(f"plugin metadata version must equal {CIS_VERSION}")

    require(skill, (
        "CIS Core",
        "External Quant Validation",
        "Optional Research Tooling",
        "extensions/research_tooling/",
        "integrations/lean/cis_lean_adapter.py",
        "references/quantconnect-lean.md",
        "QuantConnect LEAN",
        "check_tradingagents_upstream.py",
        "audit_status = unverified | pass | fail | unresolved",
        "risk_status  = unverified | pass | fail | unresolved",
        "risk_override = none | block",
        "quote_timestamp",
        "US-equity common session baseline",
        "stop_confirmation_met=true",
        "reviewed_sha",
        "allowlist",
        "不得当成三个独立样本",
    ), "CIS skill")
    require(docs["module routing"], (
        "price_context",
        "catalyst_event_review",
        "quote_max_age_seconds",
        "invalidated_reprice_required",
        "setup_expired_reprice_required",
        "unique `research_id`",
        "Trusted Publisher",
        "QuantConnect LEAN",
        "integrations/lean/cis_lean_adapter.py",
        "research_quality=unreviewed",
    ), "module routing")
    require(docs["performance"], (
        "5 / 20 / 60 trading days",
        "unique `research_id`",
        "pooled correlation",
        "allowlist",
        "next_session_close_to_close_adjusted_price_return",
    ), "performance loop")
    require(docs["QuantConnect LEAN"], (
        "external_quant_validation",
        "decision_authority = none",
        "execution_status = success | invalid_input | unavailable | error",
        "research_quality = unreviewed",
        "integrations/lean/cis_lean_adapter.py",
        "不启用 LEAN live trading",
    ), "QuantConnect LEAN reference")
    require(docs["backtest"], (
        "QuantConnect LEAN",
        "external_quant_validation",
        "research_quality = unreviewed",
        "Execution realism",
        "integrations/lean/cis_lean_adapter.py",
    ), "backtest validation")

    evidence_agent = read(PLUGIN_ROOT / "agents" / "evidence-auditor.md")
    risk_agent = read(PLUGIN_ROOT / "agents" / "risk-manager.md")
    require(evidence_agent, (
        "audit_status: pass | unresolved | fail",
        "`conditional` 不再作为机器接口状态",
    ), "evidence auditor")
    require(risk_agent, (
        "risk_status: pass | unresolved | fail",
        "risk_override: none | block",
        "不再使用机器枚举 `caution`",
    ), "risk manager")

    required_core = (
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
    )
    for name in required_core:
        read(SCRIPTS / name)

    optional_names = (
        "quant_factor_engine.py",
        "backtest_factor_strategy.py",
        "prediction_ledger.py",
        "record_cis_research.py",
        "settle_due_predictions.py",
        "evaluate_cis_predictions.py",
    )
    for name in optional_names:
        if (SCRIPTS / name).exists():
            raise AssertionError(f"optional research tool leaked into CIS Core: {name}")
        read(EXT / name)

    lean_adapter = read(LEAN / "cis_lean_adapter.py")
    lean_tests = read(LEAN / "test_cis_lean_adapter.py")
    require(lean_adapter, (
        'SCHEMA_VERSION = "cis.lean.backtest.v1"',
        'ENGINE_NAME = "QuantConnect LEAN"',
        'ENGINE_ROLE = "external_quant_validation"',
        '"decision_authority": "none"',
        '"research_quality": "unreviewed"',
        '"runtime_readiness": "lean_cli_missing"',
        '"runtime_readiness": "docker_missing"',
        '"statistics_raw"',
        '"backtest"',
        '"--output"',
    ), "LEAN adapter")
    require(lean_tests, (
        "test_parses_standard_statistics_into_cis_contract",
        "test_parses_nested_portfolio_statistics",
        "test_discovers_result_and_ignores_order_event_json",
        "test_readiness_is_unavailable_when_cli_or_docker_missing",
        "test_backtest_fails_closed_when_lean_cli_missing",
        "test_backtest_fails_closed_when_docker_missing",
    ), "LEAN adapter tests")

    score = read(SCRIPTS / "score_cis.py")
    tactical = read(SCRIPTS / "tactical_setup_gate.py")
    etf = read(SCRIPTS / "analyze_etf_premium.py")
    regime = read(SCRIPTS / "classify_market_regime.py")
    remote = read(SCRIPTS / "run_tradingagents_remote.py")
    ttl = read(SCRIPTS / "check_tradingagents_upstream.py")

    require(score, (
        "VALID_AUDIT_STATUSES",
        "VALID_RISK_STATUSES",
        "VALID_RISK_OVERRIDES",
        "_strict_bool",
        "TACTICAL_REQUIRED_CHECKS",
    ), "score_cis.py")
    require(tactical, (
        "quote_observation_session",
        "stop_type is required",
        "invalidation_confirmed",
        "blocked_pending_stop_confirmation",
        "invalidated_reprice_required",
        "setup_expired_reprice_required",
        "MAX_ALLOWED_ACTIVE_QUOTE_AGE_SECONDS",
    ), "tactical_setup_gate.py")
    require(etf, (
        "isinstance(value, bool)",
        "duplicate historical premium date",
        "unique_dates",
        ".date is required",
    ), "analyze_etf_premium.py")
    require(regime, (
        "REGIME_PROFILES",
        "MAX_SIGNAL_AGE_DAYS",
        "excluded_signals",
        "not JSON boolean",
    ), "classify_market_regime.py")
    require(ttl, ("should_check", "apply_check", "check_ttl_days", "fetch_current_sha"), "TTL checker")
    require(remote, (
        "ALLOWED_REQUEST_FIELDS",
        "provider_profile",
        "NVIDIA_BASE_URL",
        "credential_env",
        "unknown or forbidden request fields",
        "NVIDIA_API_KEY",
        "OPENAI_COMPATIBLE_API_KEY",
    ), "remote TradingAgents adapter")
    forbid(remote, ("TRADINGAGENTS_API_KEY",), "remote TradingAgents adapter")

    quant = read(EXT / "quant_factor_engine.py")
    backtest = read(EXT / "backtest_factor_strategy.py")
    ledger = read(EXT / "prediction_ledger.py")
    recorder = read(EXT / "record_cis_research.py")
    settlement = read(EXT / "settle_due_predictions.py")
    evaluation = read(EXT / "evaluate_cis_predictions.py")
    extension_tests = read(EXT / "test_research_tooling.py")

    require(quant, (
        "duplicate ticker in cross-section",
        "MIN_FACTOR_OBSERVATIONS",
        "positive finite number",
    ), "quant extension")
    require(backtest, (
        "duplicate ticker within period",
        "below -100%",
        "finite non-negative",
    ), "backtest extension")
    require(ledger, (
        "DEFAULT_HORIZONS_TRADING_DAYS = (5, 20, 60)",
        "PUBLIC_PREDICTION_ALLOWED_FIELDS",
        "PUBLIC_OUTCOME_ALLOWED_FIELDS",
        "not allowed in the public ledger",
    ), "prediction ledger")
    require(recorder, (
        'CIS_VERSION = "0.4.5"',
        "PUBLIC_PREDICTION_ALLOWED_FIELDS",
        "record_snapshot",
    ), "research recorder")
    require(settlement, (
        "no usable adjusted closes",
        "next_session_close_to_close_adjusted_price_return",
        "terminal_event_handling",
        "adjusted_close_only",
    ), "settlement extension")
    require(evaluation, (
        "mixed_horizons",
        "unique_research_count",
        "horizon_diagnostics",
        "Correlations are never pooled across different horizons",
    ), "evaluation extension")

    tactical_tests = read(SCRIPTS / "test_tactical_setup_gate.py")
    etf_tests = read(SCRIPTS / "test_analyze_etf_premium.py")
    hardening_tests = read(SCRIPTS / "test_hardening.py")
    systematic_tests = read(SCRIPTS / "test_systematic_layers.py")
    require(tactical_tests, (
        "test_regular_session_rejects_premarket_observation_even_if_age_is_allowed",
        "test_stop_type_is_required",
        "test_confirmed_stop_remains_invalidated_after_price_recovers",
        "test_technical_invalidation_can_invalidate_without_numeric_stop_breach",
    ), "tactical tests")
    require(etf_tests, (
        "test_rejects_json_boolean_as_numeric_price",
        "test_duplicate_history_dates_are_rejected",
    ), "ETF tests")
    require(hardening_tests, (
        "test_nvidia_key_cannot_be_routed_to_arbitrary_endpoint",
        "test_custom_endpoint_uses_only_generic_compatible_key",
        "test_unknown_request_fields_are_rejected_to_avoid_secret_echo",
    ), "security tests")
    require(systematic_tests, (
        "test_numeric_signal_rejects_json_boolean",
        "test_one_stale_signal_is_excluded_when_fresh_coverage_remains_sufficient",
    ), "regime tests")
    require(extension_tests, (
        "test_duplicate_ticker_is_rejected",
        "test_single_observation_factor_does_not_create_false_coverage",
        "test_duplicate_period_ticker_is_rejected",
        "test_public_ledger_rejects_unapproved_free_form_fields",
        "test_non_adjusted_path_is_left_unresolved",
        "test_mixed_horizons_do_not_pool_correlations_or_inflate_unique_research",
    ), "extension tests")

    remote_workflow = read(REPO_ROOT / ".github" / "workflows" / "cis-tradingagents.yml")
    require(remote_workflow, (
        "permissions:\n  contents: read",
        "provider_profile:",
        "reviewed_sha",
        "Install pinned TradingAgents upstream",
        "PINNED_SHA",
        "actions/upload-artifact@v4",
        "actions/download-artifact@v4",
        "trusted publisher",
        "contents: write",
        "NVIDIA_API_KEY",
        "OPENAI_COMPATIBLE_API_KEY",
    ), "TradingAgents workflow")
    forbid(remote_workflow, (
        "TRADINGAGENTS_API_KEY",
        "git clone --depth 1 https://github.com/TauricResearch/TradingAgents.git",
    ), "TradingAgents workflow")

    validate_workflow = read(REPO_ROOT / ".github" / "workflows" / "cis-validate.yml")
    require(validate_workflow, (
        '"AGENT_ARCHITECTURE.md"',
        '"integrations/lean/**"',
        "Validate CIS architecture and contracts",
        "Compile CIS Core",
        "Compile LEAN Integration",
        "Compile Optional Research Tooling",
        "Run CIS Core unit tests",
        "Run LEAN Integration unit tests",
        "Run Optional Research Tooling unit tests",
    ), "CIS validate workflow")

    status_text = read(REPO_ROOT / "runtime" / "tradingagents" / "upstream-status.json")
    status = json.loads(status_text)
    if int(status.get("check_ttl_days", 0)) != 7:
        raise AssertionError("TradingAgents check_ttl_days must equal 7")
    require(status_text, (
        "observed_sha",
        "reviewed_sha",
        "review_status",
        "last_checked_at",
        "next_check_not_before",
        "use_time_check_with_7_day_ttl_stable_baseline",
    ), "TradingAgents upstream status")

    if (REPO_ROOT / ".github" / "workflows" / "cis-tradingagents-upstream-watch.yml").exists():
        raise AssertionError("scheduled TradingAgents upstream watch must remain removed")

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    for forbidden_bundle in (PLUGIN_ROOT / "skills" / "public-equity-investing", PLUGIN_ROOT / "skills" / "tradingagents"):
        if forbidden_bundle.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {forbidden_bundle.name}")

    for forbidden_lean_bundle in (LEAN / "Lean", LEAN / "engine", LEAN / "upstream"):
        if forbidden_lean_bundle.exists():
            raise AssertionError(f"QuantConnect LEAN source must remain external: {forbidden_lean_bundle.name}")

    print(f"CIS {CIS_VERSION} contract, security and LEAN integration validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError, ValueError) as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
