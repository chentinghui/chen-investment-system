# CIS Agent Layer — 0.3

本目录保存 CIS 自有 Agent 角色契约，但从 0.3.0 起它们**不再是默认股票研究团队**。

默认股票研究核心由 TradingAgents 提供；本目录角色主要承担：

1. **fallback adapters**：TradingAgents 本次不可执行时兜底；
2. **conflict validators**：TradingAgents、Anthropic 或其他证据发生关键冲突时复核；
3. **CIS-specific adapters**：执行 CIS 自有证据、四层交易、组合数据门等特殊纪律。

## 角色

- `chen-chief-investment-analyst.md`：CIS 控制层总控，唯一拥有最终 CIS 研究姿态。
- `evidence-auditor.md`：独立证据质量门，保持核心角色。
- `risk-manager.md`：CIS 风险门与证伪条件，不等同于 TradingAgents Risk Team。
- `technical-market-analyst.md`：重点执行 CIS 四层交易框架，而不是重复外部通用技术分析。
- `portfolio-manager.md`：使用用户真实组合数据执行 CIS 组合门，不照搬外部 Portfolio Manager 仓位建议。
- `fundamental-financial-analyst.md`：基本面 fallback / 冲突复核。
- `growth-competitive-analyst.md`：成长竞争 fallback / 冲突复核。
- `valuation-analyst.md`：Anthropic 专业估值不可用时的有限 fallback / 输入复核。
- `macro-catalyst-strategist.md`：宏观传导 fallback / 冲突复核。
- `positioning-flow-analyst.md`：资金流和拥挤度补充证据。

## 运行原则

- TradingAgents 实际成功运行后，不重复调用同职责 CIS fallback Agent，除非会验证关键冲突。
- DCF、Comps、三表、Earnings、模型审计等专业方法优先使用 Anthropic Financial Services。
- 外部 Portfolio Manager 输出只记为 `external_decision_candidate`。
- 最终顺序仍由 CIS 控制：证据审计 → 风险门 → 八维评分 → 四层/ETF/组合门 → 最终中文研究姿态。
- 外部核心不可用时才按最小团队原则启用本目录 fallback adapters。
