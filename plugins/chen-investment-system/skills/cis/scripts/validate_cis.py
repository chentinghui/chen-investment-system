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
    output_modes = read(REFS / "output-modes.md")
    contract = read(REFS / "io-contract.md")
    evidence = read(REFS / "evidence-confidence.md")
    profile = read(REFS / "investor-profile.md")
    lifecycle = read(REFS / "research-lifecycle.md")
    premium = read(REFS / "cross-border-etf-premium.md")
    evaluations = read(REFS / "evaluation-cases.md")
    premium_analyzer = read(ROOT / "scripts" / "analyze_etf_premium.py")
    premium_tests = read(ROOT / "scripts" / "test_analyze_etf_premium.py")
    assistant = read(STOCK_ASSISTANT)

    require(
        skill,
        [
            "唯一用户入口",
            "quick",
            "standard",
            "deep",
            "holding_review",
            "ready",
            "limited",
            "blocked",
            "cross-border-etf-premium.md",
        ],
        "CIS skill",
    )
    require(
        workflow,
        ["任务受理", "个人规则", "模块预检", "证据登记", "风险门", "跟踪与复盘"],
        "workflow",
    )
    require(
        registry,
        ["默认能力状态", "本次就绪度", "external_optional", "ETF", "Portfolio", "AI Industry"],
        "registry",
    )
    require(
        routing,
        ["运行前检查", "CIS 是唯一总控", "ETF/index diligence", "portfolio-risk-management"],
        "routing",
    )
    require(
        external,
        ["上游未提供明确 LICENSE", "capability_status: unavailable", "未运行 Buffett 模块"],
        "external module policy",
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
        [
            "产品身份门",
            "entry_premium",
            "结构性溢价",
            "风险提示公告",
            "不得设置",
            "通用阈值",
        ],
        "cross-border ETF premium policy",
    )
    require(
        evaluations,
        ["贵州茅台", "ETF", "股票研究助手", "Buffett 与 DCF", "159509", "完全重复", "精确卖出清单"],
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
        assistant,
        ["旧版中文入口兼容层", "调用 `$cis`", "不在本 Skill 中直接调用"],
        "legacy stock assistant",
    )

    for relative in re.findall(r"`(references/[^`]+\.md)`", skill):
        if not (ROOT / relative).is_file():
            raise AssertionError(f"broken SKILL.md reference: {relative}")

    forbidden_bundles = [
        SKILLS_ROOT / "buffett",
        SKILLS_ROOT / "public-equity-investing",
    ]
    for path in forbidden_bundles:
        if path.exists():
            raise AssertionError(f"third-party source must not be bundled: {path.name}")

    print("CIS plugin validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"CIS plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
