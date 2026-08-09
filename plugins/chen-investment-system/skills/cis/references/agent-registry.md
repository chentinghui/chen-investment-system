# CIS 0.4.2 Agent / Engine 登记表

CIS 默认不运行外部多 Agent 程序，而是由当前 ChatGPT 会话执行 TradingAgents 多角色方法论；Quant、Regime、Backtest、Prediction Ledger、Performance Loop 作为独立系统层。

## 默认研究角色

| 角色 | 主要职责 | 默认条件 | 身份 |
|---|---|---|---|
| Market / Technical | 趋势、动量、波动、关键价位 | 股票研究 | methodology role |
| Fundamentals | 财务、业务质量、KPI | 股票研究 | methodology role |
| News / Catalyst | 公司/行业/宏观事件 | 股票研究 | methodology role |
| Sentiment / Positioning | 机构/资金流/拥挤度 | 数据可用且会改变结论 | optional methodology role |
| Bull Researcher | 最强看多路径与证据 | standard/deep | methodology role |
| Bear Researcher | 独立反证与下行机制 | standard/deep | methodology role |
| Research Manager | 裁决冲突，不创造新事实 | standard/deep | methodology role |
| Trader Perspective | 条件化入场/等待/止盈/防守 | 涉及交易 | methodology role |
| Risk Perspective | 尾部风险、论点失效、流动性/集中度 | standard/deep/holding_review | methodology role |
| Portfolio Perspective | 组合影响 | 真实组合数据完整 | methodology role |

## CIS 系统角色

| 模块/Agent | 主要职责 | 状态 |
|---|---|---|
| 陈氏投资分析师 | Runtime Guard、路由、最终中文结论 | **始终启用** |
| Evidence Audit | 来源、时效、前视偏差、冲突 | **fail-closed 独立质量门** |
| Risk Review | 尾部风险、论点失效、集中度/流动性 | **fail-closed 独立质量门** |
| Critical Dimension Gate | 按 decision_context 检查关键维度 | **独立质量门** |
| CIS Scoring | 八维 coverage + weighted score | 生产启发式、待校准 |
| Quant Research Engine | 大股票池 point-in-time 横截面因子排序 | experimental |
| Backtest Validator | 换手成本、偏差检查、train/validation/OOS | experimental |
| Market Regime Layer | 趋势/广度/波动/信用环境分类 | experimental |
| TradingAgents TTL Checker | 每7天到期后按需检查一次上游 SHA | installed |
| Prediction Ledger | append-only prediction/outcome 记录 | installed |
| Performance Loop | 按 horizon/regime/dimension 做校准诊断 | installed policy |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | installed |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | installed |

## 外部运行角色

`Original TradingAgents Runtime` 仅显式测试。其状态必须拆开记录：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```

`remote_ready` / `installed_ready` 只能表示程序完成，不能表示结论已被 CIS 接受。

## 权限边界

- Analyst / Bull / Bear / Research Manager / Trader / Risk / Portfolio Perspective 都没有最终动作权。
- Quant、Regime、Backtest、Performance 都没有最终动作权。
- Anthropic Financial Services 没有最终动作权。
- 原版 TradingAgents 的 `external_decision_candidate` 没有最终动作权。
- 最终结论只能由 CIS Control Layer 在所有适用质量门后生成。
