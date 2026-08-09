# CIS Agent Layer — 0.4.5

本目录保存 CIS 自有 Agent 角色契约。日常股票研究的默认方法是 **ChatGPT-native TradingAgents Methodology**；这些文件用于定义 CIS 专属控制、证据、风险、fallback 与冲突复核职责，不代表每次分析都要把所有 Agent 独立运行一遍。

## 角色

- `chen-chief-investment-analyst.md`：CIS 控制层总控，唯一拥有最终 CIS 研究姿态。
- `evidence-auditor.md`：独立证据质量门；机器状态统一 `pass | unresolved | fail`。
- `risk-manager.md`：CIS 风险门与证伪条件；机器状态统一 `risk_status=pass|unresolved|fail`、`risk_override=none|block`。
- `technical-market-analyst.md`：执行 CIS 四层交易框架与技术/价格/成交证据复核。
- `portfolio-manager.md`：使用用户真实组合数据执行 CIS 组合门，不照搬外部 Portfolio Manager 仓位建议。
- `fundamental-financial-analyst.md`：基本面 fallback / 冲突复核。
- `growth-competitive-analyst.md`：成长竞争 fallback / 冲突复核。
- `valuation-analyst.md`：Anthropic 专业估值不可用时的有限 fallback / 输入复核。
- `macro-catalyst-strategist.md`：宏观与催化剂 fallback / 冲突复核。
- `positioning-flow-analyst.md`：资金流和拥挤度补充证据。

## 运行原则

- 默认股票研究由当前 ChatGPT 会话按照 `skills/cis/references/tradingagents-methodology.md` 执行，不要求原版 TradingAgents Python。
- 同职责研究已经完成时，不无理由重复调用 fallback Agent；只有冲突复核、数据缺口或 CIS 专属 Gate 需要时才启用。
- DCF、Comps、三表、Earnings、模型审计等专业方法优先使用 Anthropic Financial Services。
- 原版 TradingAgents 仅显式测试；外部 Portfolio Manager 输出只记为 `external_decision_candidate`。
- 最终顺序由 CIS 控制：证据审计 → 风险门 → Critical Dimensions / Context Checks → 八维评分 → Regime（按需）→ Tactical/四层/ETF/组合门 → 最终中文研究姿态。
- Quant、Backtest、Prediction/Evaluation 位于 `extensions/research_tooling/`，不属于默认 Agent 链。
