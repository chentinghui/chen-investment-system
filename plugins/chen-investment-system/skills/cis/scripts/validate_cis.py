from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
SKILL = ROOT / "SKILL.md"
REFS = ROOT / "references"
REPO_ROOT = ROOT.parents[3]
REMOTE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "cis-tradingagents.yml"
DELETED_UPSTREAM_WATCH = REPO_ROOT / ".github" / "workflows" / "cis-tradingagents-upstream-watch.yml"
UPSTREAM_STATUS = REPO_ROOT / "runtime" / "tradingagents" / "upstream-status.json"
PLUGIN_JSON = ROOT.parents[1] / ".codex-plugin" / "plugin.json"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{label} missing: {', '.join(missing)}")


def main() -> int:
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
    upstream_status = read(UPSTREAM_STATUS)
    plugin_json = read(PLUGIN_JSON)
    quant_script = read(ROOT / "scripts" / "quant_factor_engine.py")
    backtest_script = read(ROOT / "scripts" / "backtest_factor_strategy.py")
    regime_script = read(ROOT / "scripts" / "classify_market_regime.py")
    performance_script = read(ROOT / "scripts" / "evaluate_cis_predictions.py")

    if DELETED_UPSTREAM_WATCH.exists():
        raise AssertionError("scheduled TradingAgents upstream watch must be removed")

    require(skill, [
        "0.4.1", "ChatGPT-native TradingAgents Methodology", "Quant Research Engine",
        "Backtest / Validation", "Market Regime", "Performance Loop",
        "原版 TradingAgents：显式测试模式", "upstream-status.json", "7 天 TTL",
        "不再使用定时 GitHub Actions", "Evidence", "scoring-engine.md",
        "four-layer-trading-framework.md", "cross-border-etf-premium.md", "CIS 不自动下单",
    ], "CIS skill")
    require(workflow, ["CIS 0.4.1", "7", "Quant Pre-screen", "Market Regime", "Backtest / Calibration", "原版 TradingAgents 测试路径"], "workflow")
    require(registry, ["ChatGPT-native TradingAgents Methodology", "Quant Research Engine", "Backtest / Validation", "Market Regime Layer", "Performance Loop", "explicit_test_only"], "module registry")
    require(routing, ["ChatGPT-native TradingAgents Methodology", "Quant Engine", "Backtest / Validation", "Market Regime", "Performance Loop", "原版 TradingAgents"], "module routing")
    require(external, ["日常股票研究默认", "7 天 TTL", "review_required", "不再使用定时 GitHub Actions", "external_decision_candidate", "Anthropic Financial Services"], "external modules")
    require(methodology, ["多角色独立性协议", "Source separation", "No fact creation by manager", "Risk independence", "Quant Engine", "7天 TTL"], "TradingAgents methodology")
    require(tradingagents, ["显式测试", "remote_ready", "external_decision_candidate", "openai_compatible", "7 天 TTL"], "original TradingAgents runtime")
    require(anthropic, ["dcf-model", "comps-analysis", "earnings-analysis", "thesis-tracker"], "Anthropic policy")
    require(orchestration, ["多角色独立性", "Quant", "Market Regime", "Performance", "最终综合顺序"], "orchestration")
    require(agent_registry, ["Quant Research Engine", "Backtest Validator", "Market Regime Layer", "Performance Loop", "Research Manager"], "agent registry")
    require(scoring, ["fundamentals", "growth", "valuation", "coverage >= 85%", "最终动作不能只由分数决定"], "scoring")
    require(quant, ["quant_score", "cis_score", "experimental_uncalibrated", "point-in-time", "factor_coverage"], "quant policy")
    require(backtest, ["Look-ahead bias", "Survivorship bias", "walk-forward", "Sharpe Ratio", "Transaction costs"], "backtest policy")
    require(regime, ["risk_on", "neutral", "risk_off", "insufficient", "experimental"], "market regime")
    require(performance, ["realized_return", "benchmark_return", "out_of_sample", "禁止", "自动覆盖"], "performance loop")
    require(remote_workflow, ["TauricResearch/TradingAgents", "run_tradingagents_remote.py", "NVIDIA_API_KEY"], "original TradingAgents workflow")
    require(upstream_status, ["observed_sha", "reviewed_sha", "review_status", "last_checked_at", '"check_ttl_days": 7', "next_check_not_before", "use_time_check_with_7_day_ttl_stable_baseline"], "upstream status")
    require(plugin_json, ['"version": "0.4.1"', "quant-research", "market-regime", "7 天 TTL"], "plugin metadata")
    require(quant_script, ["DEFAULT_FACTORS", "average_percentile_ranks", "factor_coverage", "experimental_uncalibrated"], "quant script")
    require(backtest_script, ["max_drawdown", "annualized_metrics", "forward_return", "transaction_cost_bps_per_rebalance"], "backtest script")
    require(regime_script, ["risk_on", "risk_off", "breadth_above_sma200_pct", "experimental_baseline"], "regime script")
    require(performance_script, ["score_bucket", "realized_return", "score_return_correlation", "calibration_report"], "performance script")

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    forbidden_bundles = [SKILLS_ROOT / "public-equity-investing", SKILLS_ROOT / "tradingagents"]
    for path in forbidden_bundles:
        if path.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {path.name}")

    print("CIS 0.4.1 plugin validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
