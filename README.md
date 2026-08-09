# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.4.2**

CIS 是一个中文系统化投资研究控制层。它不自动下单，也不把单一模型、单一 Agent 或单一分数当成最终决策。

## 核心架构

```text
用户
  ↓
CIS Control Layer
  ↓
Quant Factor Ranking（大股票池按需预筛）
  ↓
ChatGPT-native TradingAgents Methodology
  ↓
Anthropic Financial Services（DCF / Comps / Earnings 等按需）
  ↓
Evidence Audit + Risk Review（fail-closed）
  ↓
Critical Dimension Gate
  ↓
CIS 八维评分
  ↓
Market Regime（按需）
  ↓
四层交易 / ETF-QDII / Portfolio Gate
  ↓
最终中文研究姿态 + 证伪条件
  ↓
Prediction Ledger + Performance Loop（按需）
```

## 0.4.2 Hardening

- Evidence Audit / Risk Review 改为 **fail-closed**：没有明确 `pass` 就不能 `decision_grade`。
- 新增 **Critical Dimension Gate**：coverage 足够也不能掩盖关键维度缺失。
- TradingAgents 上游继续使用 **7 天 TTL**，并新增 `check_tradingagents_upstream.py` 作为真实执行器；不使用定时 GitHub Actions。
- Quant Engine 明确为 **Quant Factor Ranking**：横截面必须同一 `as_of`；`max_drawdown_1y` 统一按回撤绝对值处理。
- Backtest 改为按**组合实际换手率**扣交易成本，并支持 train / validation / out-of-sample 分段。
- 新增 **Prediction Ledger**：prediction/outcome 使用 append-only event，禁止事后改写历史预测。
- Performance Loop 增加 horizon、regime 和八维 dimension 校准诊断。
- Market Regime 严格校验 JSON boolean，并同时考虑信用利差绝对水平和变化。
- Original TradingAgents 将“程序执行成功”和“研究质量通过”拆开记录。
- TradingAgents 手动 workflow 必须显式填写新请求，避免误跑仓库中的旧 request.json。
- CI 现在会真正运行评分测试，并编译/测试 TTL、Ledger 和 TradingAgents adapter。

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

### Critical Dimension Gate

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

例如 valuation 完全缺失时，即使其余维度形成 85% coverage，也不能成为 `decision_grade`。

## TradingAgents 上游策略

```text
股票研究
  ↓
last_checked_at 距今 < 7天
  ├─ 是 → 不访问上游，使用已验证稳定方法论
  └─ 否 → 轻量检查当前 main SHA
               ↓
           SHA 未变 → 刷新检查时间
           SHA 变化 → review_required
                         ↓
                    当次继续使用稳定基线
                         ↓
                    审查后再决定是否同步
```

执行器：

```text
plugins/chen-investment-system/skills/cis/scripts/check_tradingagents_upstream.py
```

用户明确要求“检查 TradingAgents 更新”时可以忽略 TTL 立即检查。上游暂时不可访问不会阻塞正常股票研究。

## Quant Factor Ranking

Quant 解决的是“从大量股票中先找谁值得研究”，不是“直接决定买谁”。

- 所有横截面行必须共享同一 `as_of`；
- baseline 因子包括动量、相对强弱、营收/EPS增长、FCF margin、ROE、盈利预期修正、FCF Yield、波动率和最大回撤；
- `max_drawdown_1y` 支持 `-0.35` 或 `0.35`，引擎统一转为绝对回撤后按越小越好排序；
- baseline 权重仍为 **experimental_uncalibrated**。

脚本：

```text
plugins/chen-investment-system/skills/cis/scripts/quant_factor_engine.py
```

## Backtest / Validation

Baseline 回测现在按一边换手率计算成本：

```text
one_way_turnover = 0.5 × Σ|new_weight - old_weight|
transaction_cost = one_way_turnover × configured_cost_rate
```

首次从现金建仓按 100% one-way turnover 处理；持仓不变时换手成本为 0。

支持：

```text
train → validation → out_of_sample
```

脚本：

```text
plugins/chen-investment-system/skills/cis/scripts/backtest_factor_strategy.py
```

## Market Regime

Baseline 可使用：200日趋势、50日线斜率、市场广度、VIX、20日实现波动率、高收益信用利差绝对水平、信用利差3个月变化。

输出：

```text
risk_on | neutral | risk_off | insufficient
```

Regime 不直接产生买卖动作。

## Prediction Ledger / Performance Loop

Ledger：

```text
plugins/chen-investment-system/skills/cis/scripts/prediction_ledger.py
runtime/evaluations/predictions.jsonl
```

采用：

```text
prediction event → 不可修改历史快照 → outcome event → 校准分析
```

Performance evaluator 可按总分、horizon、regime 和八维 dimension 做诊断，但**不得自动修改生产权重**。

## 原版 TradingAgents 显式测试

```text
.github/workflows/cis-tradingagents.yml
plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py
plugins/chen-investment-system/skills/cis/scripts/run_tradingagents_remote.py
```

原版测试每次拉取 TradingAgents 当前 `main`。

状态必须区分：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```

`remote_ready` 只表示程序执行完成。原版 BUY/SELL/HOLD 结果仅是 `external_decision_candidate`，不能绕过 CIS 最终质量门。

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. 趋势：20/50/200 日均线；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈和防守止损。

## ETF / QDII

跨境 ETF/QDII 必须核验产品身份、精确基准、IOPV、历史溢价、申赎/额度、时差和流动性，不能简单套用股票结论。

## 风险声明

CIS 用于研究组织、证据核验、筛选、回测和分析辅助，不构成收益承诺，也不连接 Broker 自动执行交易。模型、数据、因子和历史回测都可能失效，最终投资决定仍需独立判断。
