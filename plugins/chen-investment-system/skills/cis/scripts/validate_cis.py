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
ALPHA = REPO_ROOT / "extensions" / "alpha_research"


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
        "backtest": read(REFS / "backtest-validation.md"),
        "performance": read(REFS / "performance-loop.md"),
        "evaluation cases": read(REFS / "evaluation-cases.md"),
        "root README": read(REPO_ROOT / "README.md"),
        "root architecture": read(REPO_ROOT / "AGENT_ARCHITECTURE.md"),
        "agents README": read(PLUGIN_ROOT / "agents" / "README.md"),
        "extension README": read(EXT / "README.md"),
        "alpha README": read(ALPHA / "README.md"),
    }
    require_version(skill, "CIS skill")
    for label, text in docs.items():
        require_version(text, label)

    plugin_json = json.loads(read(PLUGIN_ROOT / ".codex-plugin" / "plugin.json"))
    if plugin_json.get("version") != CIS_VERSION:
        raise AssertionError(f"plugin metadata version must equal {CIS_VERSION}")

    require(skill, (
        "CIS Core",
        "Optional Research Tooling",
        "Alpha Research Agent",
        "WorldQuant BRAIN",
        "extensions/research_tooling/",
        "extensions/alpha_research/",
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
        "Alpha Research Agent",
        "worldquant/alpha_import.py",
        "candidate_for_cis_validation",
    ), "module routing")
    require(docs["module registry"], (
        "WorldQuant BRAIN Alpha Source",
        "CIS Alpha Research Agent",
        "external_research_source",
        "decision_authority = none",
    ), "module registry")
    require(docs["root architecture"], (
        "CIS Alpha Research Agent",
        "extensions/alpha_research/",
        "cis.alpha_candidate.v1",
        "decision_authority = none",
    ), "root architecture")
    require(docs["alpha README"], (
        "WorldQuant BRAIN",
        "cis.alpha_candidate.v1",
        "candidate_for_cis_validation",
        "decision_authority=none",
        "out-of-sample validation",
    ), "alpha README")
    require(docs["performance"], (
        "5 / 20 / 60 trading days",
        "unique `research_id`",
        "pooled correlation",
        "allowlist",
        "next_session_close_to_close_adjusted_price_return",
    ), "performance loop")

    no_lean_text = "\n".join((
        skill,
        docs["root README"],
        docs["root architecture"],
        docs["module registry"],
        docs["module routing"],
        docs["external modules"],
        docs["system workflow"],
    ))
    forbid(no_lean_text, ("QuantConnect LEAN", "integrations/lean", "quantconnect-lean.md"), "no-LEAN architecture")
    for forbidden_path in (
        REPO_ROOT / "integrations" / "lean",
        REPO_ROOT / ".github" / "workflows" / "cis-lean-qqq-engine-test.yml",
        REFS / "quantconnect-lean.md",
    ):
        if forbidden_path.exists():
            raise AssertionError(f"removed LEAN integration must stay absent: {forbidden_path}")

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

    alpha_import = read(ALPHA / "worldquant" / "alpha_import.py")
    alpha_schema = read(ALPHA / "worldquant" / "alpha_schema.json")
    alpha_validator = read(ALPHA / "worldquant" / "alpha_validator.py")
    cross_section = read(ALPHA / "factor_engine" / "cross_section.py")
    factor_test = read(ALPHA / "factor_engine" / "factor_test.py")
    model_test = read(ALPHA / "ml_research" / "model_test.py")
    alpha_tests = read(ALPHA / "test_alpha_research.py")

    require(alpha_import, (
        'SCHEMA_VERSION = "cis.alpha_candidate.v1"',
        'SOURCE = "worldquant_brain"',
        '"decision_authority": "none"',
        '"offline_or_api_json"',
        "normalize_worldquant_alpha",
    ), "WorldQuant alpha importer")
    require(alpha_schema, (
        '"cis.alpha_candidate.v1"',
        '"worldquant_brain"',
        '"decision_authority"',
        '"none"',
    ), "WorldQuant alpha schema")
    require(alpha_validator, (
        "FORBIDDEN_KEY_FRAGMENTS",
        "candidate_for_cis_validation",
        "out_of_sample_validation",
        '"decision_authority": "none"',
    ), "WorldQuant alpha validator")
    require(cross_section, (
        "duplicate date/ticker observation",
        "mean_rank_ic",
        "rank_ic_hit_rate",
        "mean_top_bottom_spread",
    ), "alpha cross-section diagnostics")
    require(factor_test, (
        "cis.alpha_factor_test.v1",
        "cis_alpha_factor_test",
        '"decision_authority": "none"',
    ), "alpha factor test")
    require(model_test, (
        "test split is required for out-of-sample model validation",
        "model_training_performed",
        '"decision_authority": "none"',
        "oos_status",
    ), "alpha model test")
    require(alpha_tests, (
        "test_normalizes_export_and_percent_metrics",
        "test_good_screen_is_candidate_not_trade_authority",
        "test_duplicate_date_ticker_is_rejected",
        "test_requires_test_split_by_default",
        "test_reports_present_oos_after_three_test_periods",
    ), "alpha research tests")

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
        '"extensions/alpha_research/**"',
        "Validate CIS architecture and contracts",
        "Compile CIS Core",
        "Compile Optional Research Tooling",
        "Compile Alpha Research Agent",
        "Run CIS Core unit tests",
        "Run Optional Research Tooling unit tests",
        "Run Alpha Research unit tests",
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
    if "lean" in status:
        raise AssertionError("TradingAgents upstream status must not retain LEAN state")

    if (REPO_ROOT / ".github" / "workflows" / "cis-tradingagents-upstream-watch.yml").exists():
        raise AssertionError("scheduled TradingAgents upstream watch must remain removed")

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    for forbidden_bundle in (PLUGIN_ROOT / "skills" / "public-equity-investing", PLUGIN_ROOT / "skills" / "tradingagents"):
        if forbidden_bundle.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {forbidden_bundle.name}")

    print(f"CIS {CIS_VERSION} contract and security validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError, ValueError) as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
