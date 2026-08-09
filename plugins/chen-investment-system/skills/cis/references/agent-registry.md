# CIS 0.4 Agent / Engine 登记表

CIS 0.4.0 默认不运行外部多 Agent 程序，而是由当前 ChatGPT 会话执行 TradingAgents 多角色方法论；Quant、Regime、Backtest、Performance Loop 作为独立系统层。

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
| 陈氏投资分析师 | Runtime Guard、路由、Evidence、Score、最终中文结论 | **始终启用** |
| Evidence Audit | 来源、时效、前视偏差、冲突 | **独立质量门** |
| Quant Research Engine | 股票池因子筛选与排序 | experimental |
| Backtest Validator | 历史验证、偏差、成本、样本外 | experimental |
| Market Regime Layer | 风险环境分类与安全边际修正 | experimental |
| Performance Loop | 预测结果复盘与校准报告 | installed policy |
| 技术与市场结构适配器 | CIS 四层交易框架 | CIS-specific |
| 风险经理 | CIS 下行机制、证伪条件和风险覆盖 | CIS-specific |
| 组合与仓位经理 | 真实组合数据门 | CIS-specific |
| 基本面/成长/宏观/估值自写 Agent | 仅关键冲突或默认方法无法完成时 | fallback / validation |

## 外部专业/测试模块

| 模块 | 用途 | 默认条件 |
|---|---|---|
| Anthropic Financial Services | DCF/Comps/三表/Earnings/模型/竞争/论点 | 专业子问题按需 |
| Original TradingAgents Runtime | 官方 Python A/B 验证/系统测试 | 用户明确要求 |

## 调度原则

- Quick：最相关 1–2 个 methodology Analyst + 简化反证。
- Standard：Market + Fundamentals + News（Sentiment按需）+ Bull/Bear + Research Manager + CIS质量门。
- Deep：四 Analyst + 完整 Bull/Bear/Risk + 专业金融 Skills（按需）。
- Holding Review：上述链路 + 四层交易框架 + 组合门。
- Screening：Quant → Top N → methodology 深研。
- Backtest：只验证规则，不产生交易动作。
- ETF/QDII：CIS 专属产品路由优先。

不得为了“看起来全面”重复运行同职责角色，也不得让同一个模型的多角色形式掩盖共同证据来源造成的相关性错误。
