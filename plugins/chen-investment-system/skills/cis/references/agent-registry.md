# CIS 0.4.5 Agent / Engine 登记表

CIS 默认由当前 ChatGPT 会话执行 TradingAgents 多角色方法论；筛选、回测和绩效工具是独立外围研发能力，不属于默认单股分析链。

## 默认研究角色（Core）

| 角色 | 主要职责 | 默认条件 |
|---|---|---|
| Market / Technical | 趋势、动量、波动、关键价位 | 股票研究 |
| Fundamentals | 财务、业务质量、KPI | 股票研究 |
| News / Catalyst | 公司/行业/宏观事件 | 股票研究 |
| Sentiment / Positioning | 机构/资金流/拥挤度 | 数据可用且会改变结论 |
| Bull Researcher | 最强看多路径与证据 | standard/deep |
| Bear Researcher | 独立反证与下行机制 | standard/deep |
| Research Manager | 裁决冲突，不创造新事实 | standard/deep |
| Trader Perspective | 条件化入场/等待/止盈/防守 | 涉及交易 |
| Risk Perspective | 尾部风险、论点失效、流动性/集中度 | standard/deep/holding_review |
| Portfolio Perspective | 组合影响 | 真实组合数据完整 |

## CIS Core 系统角色

| 模块/Agent | 主要职责 | 状态 |
|---|---|---|
| 陈氏投资分析师 | Runtime Guard、路由、最终中文结论 | **始终启用** |
| Evidence Audit | 来源、时效、前视偏差、冲突；`audit_status=pass|unresolved|fail` | **fail-closed** |
| Risk Review | 尾部风险、论点失效、集中度/流动性；`risk_status=pass|unresolved|fail` | **fail-closed** |
| Critical Dimension Gate | 按 decision_context 检查关键维度 | **独立质量门** |
| Tactical Context Checks | Price Context + Catalyst/Event Review 完成检查 | **短线质量门** |
| CIS Scoring | 八维 coverage + weighted score | 生产启发式、待校准 |
| Market Regime Layer | 趋势/广度/波动/信用环境分类 | 按需 |
| TradingAgents TTL Checker | 每7天到期后按需检查上游 SHA | installed |
| Price / Session Guard | US-equity common session baseline + quote freshness | tactical installed |
| Tactical R/R Gate | Entry / Stop / Target / R/R + persistent invalidation | tactical baseline |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | installed |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | 按需 |

## Optional Research Tooling

位于 `extensions/research_tooling/`：

| 模块 | 主要职责 | 状态 |
|---|---|---|
| Quant Factor Ranking | 大股票池 point-in-time 排序 | experimental |
| Backtest Validator | 换手成本、偏差检查、train/validation/OOS | experimental |
| Prediction / Evaluation | 可选研究记录、结果与校准诊断 | experimental_optional |

这些模块不属于默认单股分析链，也没有最终动作权。

## 外部运行角色

`Original TradingAgents Runtime` 仅显式测试。其状态必须拆开记录：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```

`remote_ready` / `installed_ready` 只能表示程序完成，不能表示结论已被 CIS 接受。远程 Runner 的第三方执行 Job 只有 `contents: read`；仓库写回由独立 trusted publisher 完成。Secret-backed 运行只允许已审查 upstream SHA。

## 权限边界

- Analyst / Bull / Bear / Research Manager / Trader / Risk / Portfolio Perspective 都没有最终动作权；
- Quant、Backtest、Evaluation、Anthropic Financial Services 都没有最终动作权；
- 原版 TradingAgents 的 `external_decision_candidate` 没有最终动作权；
- 最终结论只能由 CIS Control Layer 在适用质量门后生成。
