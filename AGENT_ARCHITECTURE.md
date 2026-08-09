# 陈氏投资系统：CIS 0.4.5 Control Plane v2 架构

CIS 的定位不是重新实现所有金融工具，而是做**投资研究总控、质量控制与最终裁决层**。

设计原则：

> Specialist engines do specialist work. CIS controls routing, evidence, risk, scoring and final action.

## 总体架构

```text
用户
 ↓
陈氏投资分析师 / CIS Control Layer
 ↓
Intent + Asset + Mode + as_of
 ↓
Deterministic Route Planner
 ↓
┌───────────────────────────────────────────────────────────┐
│                 External Specialist Engines               │
├────────────┬──────────────┬────────────┬──────────────────┤
│ OpenBB     │TradingAgents │ FinRobot   │ Microsoft Qlib   │
│ 数据基础设施│ 通用多Agent研究 │确定性财务模型│ Quant / ML      │
├────────────┼──────────────┼────────────┼──────────────────┤
│ RD-Agent   │ QuantConnect LEAN         │ Anthropic FS      │
│ 自动Quant R&D│ 策略/执行真实性验证       │ 专业方法增强       │
└────────────┴───────────────────────────┴──────────────────┘
 ↓
Evidence Audit
 ↓
Risk Review
 ↓
Critical Dimensions
 ↓
CIS 八维 Score / Research Grade
 ↓
Market Regime（按需）
 ↓
Tactical / Four-layer / ETF-QDII / Portfolio Gate（按需）
 ↓
最终中文结论
```

**只有 CIS Control Layer 有最终动作权。** 外部项目全部 `decision_authority = none`。

## 专业分工

| 项目 | CIS 中的职责 | 不负责 |
|---|---|---|
| OpenBB | 行情、基本面、宏观、多 provider 数据整合 | 最终买卖判断 |
| TradingAgents | 基本面/技术/新闻/情绪、多空辩论、Trader/Risk/Portfolio 视角 | 覆盖 CIS 质量门 |
| FinRobot | DCF、Comps、DDM、LBO、WACC、Monte Carlo、Earnings 等确定性建模 | 直接发布 CIS target/action |
| Microsoft Qlib | 因子、ML、量化筛选、组合优化、Quant research | 事件驱动实盘路径最终验证 |
| Microsoft RD-Agent | 自动发现/实现新因子、新模型与实验 | 日常单股问答、自动升级生产规则 |
| QuantConnect LEAN | 事件驱动策略回测、订单、费用、滑点、持仓路径 | 基本面/新闻/估值与最终裁决 |
| Anthropic Financial Services | 模型审计、Earnings、Competitive、Thesis、Catalyst 等专业方法增强 | 无理由重复 FinRobot 已完成的同质模型 |

## 最少充分路由

CIS 不默认把所有引擎全跑。

```text
general_research → OpenBB + TradingAgents
valuation         → OpenBB + TradingAgents + FinRobot
screening/quant   → OpenBB + Qlib
factor_discovery  → RD-Agent + Qlib + LEAN
strategy_validation → LEAN
tactical_trade    → OpenBB + TradingAgents + CIS Tactical Gates
ETF/QDII          → data/research + CIS ETF Gate
portfolio         → data + Qlib（按需）+ CIS Portfolio Gate
```

`fast / standard / deep` 只改变研究深度，不允许删除用户显式要求的专业验证器。

## Quant R&D Pipeline

```text
Hypothesis
 ↓
RD-Agent
发现 / 实现候选
 ↓
Qlib
独立 Quant/ML 研究与样本外评估
 ↓
LEAN
event-driven order / fee / slippage / portfolio-path validation
 ↓
CIS Backtest Validation
 ↓
Policy Review
 ↓
Production Rule
```

这个链条明确区分：

- **RD-Agent = 发明候选**；
- **Qlib = 研究候选**；
- **LEAN = 验证可执行策略路径**；
- **CIS = 决定是否进入生产规则**。

任何外部项目的名气或 Star 数都不能让候选跳过验证链。

## 股票研究 Pipeline

```text
Primary Sources / OpenBB
 ↓
TradingAgents
 ↓
FinRobot（估值/模型需要时）
 ↓
Anthropic（deep method audit，按需）
 ↓
Evidence + Risk + Critical Dimensions
 ↓
CIS Score
 ↓
交易/ETF/组合门
 ↓
CIS Final
```

估值冲突不平均目标价，而是逐项比较 WACC、growth、terminal value、margin、capex、dilution、peer set 与会计口径。

## Data Authority

OpenBB 是 data fabric，不是 primary-source override。

关键数据冲突顺序：

```text
primary source
→ freshness / as_of
→ provider coverage
→ accounting / unit / currency consistency
```

## External Runtime Truthfulness

对所有外部引擎必须区分：

```text
availability
execution_status
data_as_of
research_quality
evidence_audit_status
accepted_by_cis
```

仓库里写了某项目、项目可安装、甚至旧任务曾成功，都不等于本次已运行。

## TradingAgents Runtime Safety

日常研究允许使用稳定、已审查的 ChatGPT-native TradingAgents Methodology。原版 Python runtime 仅明确运行/测试时启动。

保留：

- 7 天 TTL 上游检查；
- `reviewed_sha` Gate；
- 第三方代码只读执行；
- Trusted Publisher 独立写回；
- Secret 与 provider endpoint 绑定。

原版 Portfolio Manager 输出仍是 `external_decision_candidate`。

## QuantConnect LEAN Boundary

```text
engine = QuantConnect LEAN
engine_role = external_quant_validation
decision_authority = none
execution_status = success | invalid_input | unavailable | error
research_quality = unreviewed
```

只有真实执行并解析到 statistics JSON 才能说 LEAN 已运行。显式 LEAN 请求失败时，不允许拿 lightweight baseline 冒充。

当前 CIS 不启用 LEAN live trading / Broker 自动执行。

## CIS 自有质量门

机器契约：

```text
audit_status = unverified | pass | unresolved | fail
risk_status  = unverified | pass | unresolved | fail
risk_override = none | block
```

CIS 自有规则始终保留：

- Evidence / source / freshness / point-in-time；
- 八维评分和 coverage；
- 四层交易框架；
- Price / Session / Quote Freshness；
- Tactical R/R 和 setup lifecycle；
- ETF/QDII premium discipline；
- Portfolio data gate；
- 最终中文结论与证伪条件。

## Optional Local Tooling

`extensions/research_tooling/` 降级为外围 fallback/sanity：

- Quant Factor Ranking → 不等价于 Qlib；
- Baseline Backtest → 不等价于 LEAN；
- Prediction/Evaluation → 仅记录、复盘和校准诊断。

External/Extension 故障不得伪装成成功，也不得自动修改生产规则。

## 关键文件

- 唯一入口：`plugins/chen-investment-system/skills/cis/SKILL.md`
- 总控 Agent：`plugins/chen-investment-system/agents/chen-chief-investment-analyst.md`
- 系统流程：`plugins/chen-investment-system/skills/cis/references/system-workflow.md`
- 模块路由：`plugins/chen-investment-system/skills/cis/references/module-routing.md`
- 引擎注册：`plugins/chen-investment-system/skills/cis/references/external-engine-registry.json`
- 编排协议：`plugins/chen-investment-system/skills/cis/references/agent-orchestration.md`
- 确定性路由器：`plugins/chen-investment-system/skills/cis/scripts/route_cis.py`
- LEAN 适配器：`integrations/lean/cis_lean_adapter.py`
- 回测验证：`plugins/chen-investment-system/skills/cis/references/backtest-validation.md`
- 评分：`plugins/chen-investment-system/skills/cis/references/scoring-engine.md`
- Optional Extensions：`extensions/research_tooling/`
