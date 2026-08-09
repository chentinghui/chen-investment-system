# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.4.5 — Control Plane v2**

CIS 是一个中文投资研究**总控与最终质量控制层**。它不试图重新实现所有成熟金融项目，而是把不同任务路由给最合适的专业外部引擎，再由 CIS 自有证据门、风险门、评分、交易纪律、ETF/QDII纪律和组合门统一裁决。

CIS 不自动下单。

## 核心原则

> **最专业的项目做最专业的事情；CIS 负责路由、证据、冲突、风险、评分与最终动作。**

```text
User
 ↓
CIS Control Layer
 ↓
Intent / Asset / Mode / as_of
 ↓
Deterministic Route Planner
 ↓
┌──────────┬──────────────┬──────────┬──────────────┐
│ OpenBB   │ TradingAgents│ FinRobot │ Microsoft Qlib│
│ 数据层    │ 通用多Agent研究│ 财务模型   │ Quant / ML     │
├──────────┼──────────────┼──────────┼──────────────┤
│ RD-Agent │ QuantConnect LEAN      │ Anthropic FS  │
│ 自动R&D   │ 策略/执行真实性验证      │ 方法增强        │
└──────────┴─────────────────────────┴───────────────┘
 ↓
Evidence Audit
 ↓
Risk Review
 ↓
Critical Dimensions
 ↓
CIS 0–100 Score / Research Grade
 ↓
Market Regime / Tactical / ETF / Portfolio Gates（按需）
 ↓
最终中文分析结论
```

**外部项目全部没有最终动作权；只有 CIS Control Layer 可以发布最终 CIS 结论。**

## 外部专业项目分工

| 项目 | CIS 中的主职责 |
|---|---|
| **OpenBB** | 行情、基本面、宏观、多 provider 数据基础设施 |
| **TradingAgents** | 基本面、技术、新闻、情绪、多空辩论、Trader/Risk/Portfolio 视角 |
| **FinRobot** | DCF、Comps、DDM、LBO、WACC、Monte Carlo、Earnings 等确定性财务模型 |
| **Microsoft Qlib** | 因子、ML、量化筛选、组合优化、Quant research |
| **Microsoft RD-Agent** | 自动发现/实现新因子、新模型、Quant R&D |
| **QuantConnect LEAN** | 事件驱动策略回测、订单、费用、滑点、持仓路径验证 |
| **Anthropic Financial Services** | 模型审计、Earnings、Competitive、Thesis、Catalyst 等专业方法增强 |

## Minimum Sufficient Routing

CIS 不会为了复杂而把所有模块每次全部运行。

```text
一般股票研究     → OpenBB + TradingAgents
估值/财务模型    → OpenBB + TradingAgents + FinRobot
大股票池/Quant   → OpenBB + Qlib
新因子/新模型    → RD-Agent → Qlib → LEAN
策略级历史验证   → LEAN
短线/买卖价位    → OpenBB + TradingAgents + CIS Tactical Gates
ETF/QDII         → data/research + CIS ETF Gate
组合优化         → data + Qlib（按需）+ CIS Portfolio Gate
```

`fast / standard / deep` 控制研究深度；用户明确要求的专业引擎不会因为 fast 模式被静默取消。

## Deterministic Control Plane

外部引擎机器登记表：

```text
plugins/chen-investment-system/skills/cis/references/external-engine-registry.json
```

确定性路由器：

```text
plugins/chen-investment-system/skills/cis/scripts/route_cis.py
```

支持 intent：

```text
fact_lookup
general_research
valuation
earnings
screening
quant_research
factor_discovery
strategy_validation
tactical_trade
holding_review
portfolio_review
etf_review
```

路由器只回答“应该由谁负责”，不伪装成外部 runtime 已执行。

## Quant R&D Pipeline

```text
RD-Agent
发现 / 实现候选
 ↓
Qlib
Quant / ML 独立评估
 ↓
QuantConnect LEAN
事件驱动 / 费用 / 滑点 / 订单 / 持仓路径验证
 ↓
CIS Backtest Validation
 ↓
Policy Review
 ↓
Production Rule
```

角色固定：

```text
RD-Agent = 发明候选
Qlib     = 研究候选
LEAN     = 验证可执行路径
CIS      = 决定是否生产化
```

任何新因子、模型或阈值默认是 experimental，不能自动修改 CIS 生产评分权重。

## General Equity Research Pipeline

```text
Primary Sources / OpenBB
 ↓
TradingAgents
 ↓
FinRobot（需要专业估值/财务模型时）
 ↓
Anthropic（deep second opinion，按需）
 ↓
Evidence + Risk + Critical Dimensions
 ↓
CIS Score
 ↓
Tactical / ETF / Portfolio Gate
 ↓
CIS Final
```

估值冲突不使用简单平均目标价，而是比较 WACC、growth、terminal value、margin、capex、dilution、peer set 与会计口径。

## OpenBB Boundary

OpenBB 是 data fabric，不是 primary-source override。

关键事实冲突按：

```text
primary source
→ freshness / as_of
→ provider coverage
→ accounting / unit / currency consistency
```

## TradingAgents Boundary

日常股票研究可以使用 CIS 已审查的 ChatGPT-native TradingAgents Methodology。原版 Python runtime 仅在明确运行/测试或 A/B 时调用。

原版 Portfolio Manager 输出：

```text
external_decision_candidate
```

不能绕过 CIS Evidence/Risk/Score/Tactical/ETF/Portfolio Gates。

保留 7 天 TTL、`reviewed_sha`、第三方只读执行、Trusted Publisher 独立写回等供应链安全规则。

## FinRobot Boundary

FinRobot 是专业确定性财务建模引擎。CIS 优先保留 code-calculated 数字、输入假设与 provenance，而不是让多个 LLM 无理由重复心算同一模型。

FinRobot 不可用时可以降级到 Anthropic Financial Services 或透明 CIS calculation，但必须标记 fallback，不能声称“已运行 FinRobot”。

## Qlib Boundary

Qlib 是专业 Quant/ML 研究引擎。研究必须考虑 point-in-time、train/validation/OOS、survivorship、restatement leakage、universe drift 与稳健性。

本地：

```text
extensions/research_tooling/quant_factor_engine.py
```

只保留为有限 fallback / sanity check，不等价于 Qlib。

## QuantConnect LEAN — External Quant Validation

策略级验证适配层：

```text
integrations/lean/cis_lean_adapter.py
```

LEAN 输出固定语义：

```text
engine_role = external_quant_validation
decision_authority = none
research_quality = unreviewed
```

只有本次真实 `execution_status=success` 且解析到可识别 statistics JSON，才能说“已运行 LEAN”。

显式 LEAN 请求如果 unavailable/error，不能用 lightweight baseline backtest 冒充。

当前 CIS 不启用 LEAN live trading / Broker 自动执行。

## CIS Fail-Closed Quality Gates

```text
audit_status = unverified | pass | unresolved | fail
risk_status  = unverified | pass | unresolved | fail
risk_override = none | block
```

只有明确通过，才允许升级到 decision-grade。

八维评分：

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
coverage >= 85%       → 仍需 Evidence/Risk/Critical Gates 通过才可 decision_grade
```

## Tactical Setup Gate

涉及短线、买点、追不追、止损、目标价时，CIS 继续执行：

```text
analysis_timestamp / quote_timestamp
US-equity Price/Session
Quote Freshness
Entry Zone
Chase Limit
Stop / Stop Type
Target 1 / 2
Reward / Risk
Setup Lifecycle
```

高 CIS Research Grade 不等于当前价值得追。

## ETF / QDII Discipline

跨境 ETF/QDII 始终保留 CIS 自有产品门：

- 产品身份与基准；
- NAV / IOPV；
- 实时与历史溢价；
- 申赎/额度；
- 海内外交易时差；
- 流动性。

专业外部项目不能覆盖这层纪律。

## Optional Research Tooling

位于：

```text
extensions/research_tooling/
```

- local Quant：有限 fallback / CI sanity；
- Baseline Backtest：横截面 `score → forward_return` sanity；
- Prediction/Evaluation：用户明确要求记录、复盘、校准时运行。

它们不等价于 Qlib/LEAN，也不能自动修改生产规则。

## 关键文件

```text
plugins/chen-investment-system/skills/cis/SKILL.md
plugins/chen-investment-system/agents/chen-chief-investment-analyst.md
plugins/chen-investment-system/skills/cis/references/system-workflow.md
plugins/chen-investment-system/skills/cis/references/module-routing.md
plugins/chen-investment-system/skills/cis/references/module-registry.md
plugins/chen-investment-system/skills/cis/references/external-engine-registry.json
plugins/chen-investment-system/skills/cis/references/agent-orchestration.md
plugins/chen-investment-system/skills/cis/scripts/route_cis.py
integrations/lean/cis_lean_adapter.py
extensions/research_tooling/
```

## 风险声明

CIS 用于研究组织、证据核验、量化研究、回测和投资分析辅助，不构成收益承诺。模型、数据、因子和历史回测都可能失效；最终投资决定仍需基于可承受风险独立判断。
