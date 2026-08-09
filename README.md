# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.4.2**

CIS 是一个中文系统化股票研究控制层。它的核心职责是**分析**：组织证据、多角色研究、风险审查、评分、市场环境和交易计划。CIS 不自动下单，也不要求每次研究都运行量化、回测或历史绩效模块。

## CIS Core

```text
用户
  ↓
CIS Control Layer
  ↓
ChatGPT-native TradingAgents Methodology
  ↓
Anthropic Financial Services（专业子问题按需）
  ↓
Evidence Audit + Risk Review（fail-closed）
  ↓
Critical Dimension Gate
  ↓
CIS 八维评分
  ↓
Market Regime（按交易问题需要）
  ↓
四层交易 / ETF-QDII / Portfolio Gate
  ↓
最终中文分析结论
```

日常单股分析只运行与当前问题相关的 Core 能力。CIS Core 的失败条件不会因为外围研发工具不可用而扩大。

## Optional Research Tooling

以下能力保留，但物理隔离在：

```text
extensions/research_tooling/
```

它们不是日常单股分析链的一部分：

- `quant_factor_engine.py`：大股票池/Top N 候选排序；
- `backtest_factor_strategy.py`：新规则、因子、阈值的历史验证；
- `prediction_ledger.py`：可选研究记录；
- `record_cis_research.py`：可选研究快照；
- `settle_due_predictions.py`：实验性结果结算；
- `evaluate_cis_predictions.py`：历史表现与校准诊断。

路由原则：单股分析不自动调用这些工具；大股票池筛选才按需调用 Quant；验证规则才调用 Backtest；用户明确要求记录、复盘或校准时才调用 Evaluation。Extension 故障不得阻塞 CIS Core。

## TradingAgents 上游策略

日常股票研究默认使用 CIS 已审查的稳定 TradingAgents 方法论。TradingAgents 上游采用 **7 天 TTL** 的使用时检查：TTL 未到不访问上游；到期后的下一次股票研究轻量检查当前 `main` SHA；发现变化只标记 `review_required`，未经审查不会覆盖稳定方法论。

用户明确要求运行原版 TradingAgents 时，显式测试路径仍会重新 clone 上游当前 `main`。原版结果只能作为 `external_decision_candidate`，不能绕过 CIS 最终质量门。

## Anthropic Financial Services

需要 DCF、Comps、Earnings、三表、模型审计、竞争分析、论点或催化剂等专业金融方法时，优先读取 Anthropic `financial-services` 上游 `main` 的目标 Skill。只有本次真实读取/执行后才能声称使用；输出仍必须经过 CIS Evidence/Risk/Score 等规则。

## 0.4.2 Hardening

- Evidence Audit / Risk Review 为 **fail-closed**：没有明确 `pass` 就不能 `decision_grade`；
- Critical Dimension Gate 防止 coverage 掩盖关键维度缺失；
- TradingAgents 7 天 TTL 有确定性执行器；
- Market Regime 严格校验输入；
- Original TradingAgents 将执行成功与研究质量拆开；
- CI 分别验证 **CIS Core** 与 **Optional Research Tooling**。

## CIS 八维评分

| 维度 | 权重 |
|---|---:|
| fundamentals | 20 |
| growth | 15 |
| valuation | 15 |
| industry_competitive | 10 |
| technical | 15 |
| catalyst_macro | 10 |
| positioning | 5 |
| risk_resilience | 10 |

```text
coverage < 70%        → insufficient
70% <= coverage < 85% → provisional
coverage >= 85%       → 仍需 Audit/Risk/Critical Dimensions 全部通过才可 decision_grade
```

Critical Dimensions：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. 趋势：20/50/200 日均线；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈与防守止损。跨境 ETF/QDII 还必须核验产品身份、基准、IOPV、历史溢价、申赎/额度、时差和流动性。

## 风险声明

CIS 用于研究组织、证据核验、筛选、回测和分析辅助，不构成收益承诺，也不连接 Broker 自动执行交易。模型、数据、因子和历史回测都可能失效，最终投资决定仍需独立判断。
