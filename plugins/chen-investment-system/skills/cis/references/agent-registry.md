# CIS 0.3 Agent / Engine 登记表

CIS 0.3.0 不再把自写通用专家 Agent 作为默认股票研究团队。默认通用研究团队由 TradingAgents 提供；CIS 自写 Agent 保留为 fallback adapters、质量验证和特殊规则执行者。

## 默认外部研究核心

| 引擎/角色 | 主要职责 | 默认调用条件 | CIS中的身份 |
|---|---|---|---|
| TradingAgents Analyst Team | Fundamentals / Technical / News / Sentiment | 股票/上市公司 standard/deep/holding_review | 默认通用研究核心 |
| TradingAgents Bull/Bear | 多空辩论、反证 | 需要形成研究结论 | 默认研究冲突引擎 |
| TradingAgents Research Manager | 汇总研究分歧 | TradingAgents 全链路 | 外部研究综合 |
| TradingAgents Trader | 候选交易方案 | 具体交易研究 | 候选方案生成器 |
| TradingAgents Risk Team | 候选方案风险讨论 | 具体交易研究 | 外部风险输入 |
| TradingAgents Portfolio Manager | 批准/拒绝其候选方案 | TradingAgents 全链路 | `external_decision_candidate`，非CIS最终动作 |

## CIS 自有角色

| Agent | 主要职责 | 默认调用条件 | 状态 |
|---|---|---|---|
| 陈氏投资分析师 | Runtime Guard、路由、证据综合、CIS评分、最终中文结论 | 所有 CIS 任务 | **始终启用** |
| 证据审计员 | 来源、时效、前视偏差、冲突质量门 | standard/deep/holding_review；关键 quick | **始终独立** |
| 基本面与财务分析师 | TradingAgents不可用时补基本面；或验证关键财务冲突 | fallback / conflict check | fallback adapter |
| 成长与竞争分析师 | 跑道、行业、竞争的兜底或交叉核验 | fallback / conflict check | fallback adapter |
| 估值分析师 | Anthropic专业估值不可用时做透明简化估值；或复核输入 | fallback / validation | fallback adapter |
| 技术与市场结构分析师 | 执行 CIS 四层交易框架，不重复 TradingAgents 通用技术分析 | 涉及买卖/价位时 | CIS 专属规则适配器 |
| 宏观与催化剂策略师 | 传导链兜底和关键事件核验 | fallback / macro conflict | fallback adapter |
| 定位与资金流分析师 | 机构/资金流/拥挤度补充证据 | 数据可用且会改变结论 | support adapter |
| 风险经理 | CIS 特有下行机制、证伪条件和风险覆盖；不重复外部Risk Team | standard/deep/holding_review | CIS质量门 |
| 组合与仓位经理 | 使用用户真实组合数据执行组合门 | 组合数据完整 | CIS专属规则适配器 |

## 专业方法

DCF、Comps、三表、财报前后、模型审计、竞争分析、首次覆盖、论点/催化剂优先使用 Anthropic Financial Services；对应 CIS 自写 Agent 不重复执行，除非上游不可用或需要验证关键冲突。

## 调度原则

- Quick 股票任务：CIS + TradingAgents（可用时）；证据关键缺口才加审计/适配器。
- Standard：CIS + TradingAgents + 证据审计；按需 Anthropic；CIS 风险门最终检查。
- Deep：CIS + TradingAgents + Anthropic 专业 Skills + 证据审计；仅在冲突处启用 fallback adapters。
- Holding Review：上述链路 + CIS 四层交易框架 + 组合数据门。
- ETF/QDII：CIS 专属 ETF 路由优先，不强制 TradingAgents。

不得为了“看起来全面”重复运行 TradingAgents 与同职责 CIS fallback Agent。
