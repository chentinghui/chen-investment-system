from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
SKILL = ROOT / "SKILL.md"
REFS = ROOT / "references"
STOCK_ASSISTANT = SKILLS_ROOT / "stock-research-assistant" / "SKILL.md"


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
    tradingagents = read(REFS / "tradingagents.md")
    anthropic = read(REFS / "anthropic-financial-services.md")
    orchestration = read(REFS / "agent-orchestration.md")
    agent_registry = read(REFS / "agent-registry.md")
    output_modes = read(REFS / "output-modes.md")
    contract = read(REFS / "io-contract.md")
    evidence = read(REFS / "evidence-confidence.md")
    profile = read(REFS / "investor-profile.md")
    lifecycle = read(REFS / "research-lifecycle.md")
    premium = read(REFS / "cross-border-etf-premium.md")
    evaluations = read(REFS / "evaluation-cases.md")
    premium_analyzer = read(ROOT / "scripts" / "analyze_etf_premium.py")
    premium_tests = read(ROOT / "scripts" / "test_analyze_etf_premium.py")
    ta_adapter = read(ROOT / "scripts" / "run_tradingagents.py")
    assistant = read(STOCK_ASSISTANT)

    require(
        skill,
        [
            "0.3.0",
            "TradingAgents",
            "Anthropic Financial Services",
            "唯一用户入口",
            "自动触发规则",
            "分析 MU",
            "纯事实型问题",
            "只要答案会影响投资研究或交易决策，默认进入 CIS",
            "Runtime Guard",
            "external_decision_candidate",
            "scoring-engine.md",
            "four-layer-trading-framework.md",
            "cross-border-etf-premium.md",
        ],
        "CIS skill",
    )
    require(
        workflow,
        [
            "CIS 0.3",
            "TradingAgents",
            "Anthropic Financial Services",
            "Fallback adapters",
            "CIS 八维统一评分",
            "四层结构",
            "ETF / QDII",
            "跟踪与复盘",
        ],
        "workflow",
    )
    require(
        registry,
        [
            "TradingAgents Core",
            "upstream_default",
            "external_decision_candidate",
            "Anthropic Financial Services",
            "Trading Framework",
            "ETF / QDII",
        ],
        "registry",
    )
    require(
        routing,
        [
            "TradingAgents",
            "Anthropic",
            "运行前检查",
            "Fallback 路由",
            "四层交易框架",
            "不得声称已运行",
        ],
        "routing",
    )
    require(
        external,
        [
            "TradingAgents（默认通用研究核心）",
            "v0.3.1",
            "Apache License 2.0",
            "external_decision_candidate",
            "代码持续更新不代表行情/新闻实时",
            "Anthropic Financial Services",
        ],
        "external module policy",
    )
    require(
        tradingagents,
        [
            "默认通用股票研究/决策核心",
            "Portfolio Manager",
            "external_decision_candidate",
            "installed_ready",
            "upstream_only",
            "look-ahead",
            "run_tradingagents.py",
        ],
        "TradingAgents adapter policy",
    )
    require(
        anthropic,
        ["dcf-model", "comps-analysis", "earnings-analysis", "thesis-tracker"],
        "Anthropic policy",
    )
    require(
        orchestration,
        ["TradingAgents", "Anthropic", "避免重复分析", "external_decision_candidate", "最终综合顺序"],
        "orchestration",
    )
    require(
        agent_registry,
        ["fallback adapters", "TradingAgents Analyst Team", "证据审计员", "CIS 专属规则适配器"],
        "agent registry",
    )
    require(
        output_modes,
        ["Quick", "Standard", "Deep", "Holding Review", "资料截止时间"],
        "output modes",
    )
    require(
        contract,
        ["runtime_readiness", "thesis_falsifiers", "evidence:", "thesis:", "valuation:"],
        "I/O contract",
    )
    require(evidence, ["A 级", "B 级", "C 级", "D 级", "综合置信度"], "evidence policy")
    require(profile, ["status: 未设置", "maximum_single_position", "drawdown_tolerance"], "profile")
    require(lifecycle, ["research_id", "thesis_falsifiers", "change_since_prior"], "lifecycle")
    require(
        premium,
        ["产品身份门", "entry_premium", "结构性溢价", "风险提示公告", "通用阈值"],
        "cross-border ETF premium policy",
    )
    require(
        evaluations,
        [
            "分析 MU",
            "MU现在能买吗",
            "MU全称是什么",
            "TradingAgents 包未安装",
            "external_decision_candidate",
            "look-ahead leakage",
            "Anthropic DCF",
            "159509",
            "英伟达186美元",
        ],
        "evaluation cases",
    )
    require(
        premium_analyzer,
        ["def analyze", "current_premium_pct", "entry_premium_pct", "premium_regime"],
        "ETF premium analyzer",
    )
    require(
        premium_tests,
        ["159509", "insufficient_history", "rejects_non_positive_values"],
        "ETF premium tests",
    )
    require(
        ta_adapter,
        [
            "TradingAgentsGraph",
            "propagate",
            "external_decision_candidate",
            "probe-only",
            "upstream_only",
        ],
        "TradingAgents runtime adapter",
    )
    require(
        assistant,
        ["旧版中文入口兼容层", "调用 `$cis`", "TradingAgents", "Anthropic Financial Services"],
        "legacy stock assistant",
    )

    for relative in re.findall(r"`(references/[^`]+\\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    forbidden_bundles = [
        SKILLS_ROOT / "buffett",
        SKILLS_ROOT / "public-equity-investing",
        SKILLS_ROOT / "tradingagents",
    ]
    for path in forbidden_bundles:
        if path.exists():
            raise AssertionError(f"third-party source must not be bundled directly: {path.name}")

    print("CIS 0.3 plugin validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
