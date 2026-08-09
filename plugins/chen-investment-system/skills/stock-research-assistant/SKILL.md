---
name: stock-research-assistant
description: 旧版中文入口兼容层。仅当用户明确说“股票研究助手”时使用，并立即把完整任务转交陈氏投资系统（CIS）；本 Skill 不独立调用 TradingAgents、Anthropic 或发布投资结论。
---

# 股票研究助手

这是陈氏投资系统的旧版中文别名，只负责转交，不拥有独立分析流程。

## 工作流程

1. 保留用户原始研究对象、问题、期限、截止日期和资料。
2. 调用 `$cis`（陈氏投资系统）。
3. 由 CIS 执行 Runtime Guard，核验当前版本。
4. 股票/上市公司由 CIS 检查并优先路由 TradingAgents；需要 DCF、Comps、财报等专业方法时再按需路由 Anthropic Financial Services。
5. 最终仍由 CIS 执行证据门、八维评分、四层/ETF/组合门并输出中文结论。

## 禁止事项

- 不在本 Skill 中直接调用 TradingAgents。
- 不在本 Skill 中直接调用 Anthropic Financial Services。
- 不在本 Skill 中直接调用 `$buffett`。
- 不在本 Skill 中给出独立评分、仓位或买卖结论。

## 输出要求

仅确认任务已按陈氏投资系统处理；最终输出完全遵循 CIS 当前 `main` 的模式、证据、评分、风险门和复盘契约。
