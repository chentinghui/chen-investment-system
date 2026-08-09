# CIS 0.4 模块登记表

CIS 0.4.0 将研究、筛选、验证、市场环境和反馈闭环分层，避免一个模型/一个分数承担全部职责。

| 模块 | 作用 | 默认状态 | 本次就绪条件 | 最终动作权 |
|---|---|---|---|---|
| CIS Control Layer | 受理、Runtime Guard、证据门、八维评分、最终中文结论 | `installed` | 总是可用 | **有** |
| ChatGPT-native TradingAgents Methodology | 基本面、技术、新闻、情绪、多空反证、Research/Risk/Trader视角 | `default_methodology` | 当前会话可访问必要证据 | 无 |
| Quant Research Engine | 股票池因子筛选、横截面排序 | `experimental` | 同一 as_of 的可比 point-in-time 因子数据 | 无 |
| Backtest / Validation | 因子/规则/阈值历史验证与偏差检查 | `experimental` | point-in-time 历史数据和基准 | 无 |
| Market Regime Layer | risk_on / neutral / risk_off 环境分类 | `experimental` | 趋势/广度/波动/信用等覆盖足够 | 无 |
| Performance Loop | 预测→实际结果→校准报告 | `installed_policy` | 有历史预测和到期结果 | 无 |
| Anthropic Financial Services | DCF、Comps、三表、财报、模型、竞争、论点/催化剂 | `upstream_preferred` | 对应 Skill 本次真实可访问且输入完整 | 无 |
| Original TradingAgents Runtime | 官方 Python 多 Agent 运行 | `explicit_test_only` | 用户明确要求 + runtime/model/data ready | 无 |
| Evidence Audit | 来源、时效、前视偏差、事实/判断、冲突 | `installed` | 有可审计证据 | 质量门 |
| Trading Framework | 趋势→价格→成交→风险；止盈+止损 | `installed` | 涉及具体买卖/持仓 | 质量门 |
| ETF / QDII | 产品身份、基准、IOPV、历史溢价、申赎、时差 | `installed` | 产品和溢价数据足够 | 质量门 |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | `installed` | 用户真实组合数据完整 | 质量门 |

## 研究能力映射

| 能力 | 默认负责人 | 增强/验证 |
|---|---|---|
| 股票池候选生成 | Quant Engine（按需） | Backtest |
| 通用基本面 | ChatGPT-native Fundamentals | Anthropic Financial Analysis |
| 技术/市场结构 | ChatGPT-native Market | CIS 四层交易最终校验 |
| 新闻/宏观 | ChatGPT-native News | Market Regime / Anthropic sector |
| 情绪/定位 | ChatGPT-native Sentiment（按需） | 可验证资金流/机构数据 |
| 多空反证 | Bull/Bear 独立证据协议 | Research Manager |
| 专业估值/财报 | Anthropic Financial Services | CIS Evidence Gate |
| 市场环境 | Market Regime | 条件化回测 |
| 最终评分 | CIS Scoring | Performance Loop 校准 |
| 最终动作/研究姿态 | CIS | 无替代 |

## 状态说明

- `default_methodology`：日常默认由当前 ChatGPT 会话执行的方法论。
- `experimental`：已有规则/代码骨架，但尚未经过充分样本外验证，不能称为已证明有效。
- `explicit_test_only`：只有用户明确要求原版运行/系统测试时使用。
- `upstream_preferred`：专业方法首选上游；必须逐次确认可访问性。

代码版本更新、模型可用和市场数据实时性是三件不同的事，必须分别记录。
