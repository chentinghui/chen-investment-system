# CIS 0.4.5 模块登记表（Control Plane v2）

CIS 采用 **Core Control + External Specialist Engines + Optional Local Tooling** 三层结构。核心原则是：**CIS 自己只做控制、质量门、评分与最终裁决；成熟外部项目负责各自最专业的工作。**

## 1. CIS Core

| 模块 | 作用 | 默认状态 | 所属层 | 最终动作权 |
|---|---|---|---|---|
| CIS Control Layer | Intake、任务标准化、路由、冲突仲裁、最终中文结论 | `installed` | **Core** | **有，唯一** |
| Deterministic Route Planner | 根据 intent/asset/mode 生成最少充分路由 | `installed` | **Core Control** | 无 |
| External Engine Registry | 外部项目能力、职责、fallback、权限登记 | `installed` | **Core Control** | 无 |
| Evidence Audit | 来源、时效、新鲜度、前视偏差、冲突 | `fail_closed_gate` | **Core** | 质量门 |
| Risk Review | 尾部风险、论点失效、集中度/流动性 | `fail_closed_gate` | **Core** | 质量门 |
| Critical Dimension Gate | 按任务确保关键维度存在 | `installed` | **Core** | 质量门 |
| Tactical Context Checks | Price Context + Catalyst/Event Review | `installed` | **Core, tactical** | 质量门 |
| CIS Scoring | 八维加权 + coverage；Research Grade 与 Trade Readiness 分离 | `production_heuristic_pending_calibration` | **Core** | 无单独动作权 |
| Market Regime Layer | risk_on / neutral / risk_off 环境层 | `experimental` | **Core, 按需** | 无 |
| Price / Session Guard | US-equity session + quote freshness | `installed` | **Core, tactical** | 质量门 |
| Tactical R/R Gate | Entry / Stop / Target / Chase / Setup lifecycle | `installed_baseline` | **Core, tactical** | 质量门 |
| Trading Framework | 趋势→价格→成交→风险 | `installed` | **Core** | 质量门 |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | `installed` | **Core** | 质量门 |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | `installed` | **Core, 按需** | 质量门 |

确定性路由文件：

```text
references/external-engine-registry.json
scripts/route_cis.py
```

## 2. Accepted External Specialist Engines

| 外部项目 | CIS 定位 | 默认触发 | 状态 | 最终动作权 |
|---|---|---|---|---|
| **OpenBB** | 数据基础设施 / provider 聚合 | 行情、基本面、宏观、多源数据 | `accepted_external_lazy` | 无 |
| **TradingAgents** | 通用多 Agent 投资研究 | 一般股票研究、多空辩论、交易假设 | `accepted_default_methodology` | 无 |
| **FinRobot** | 确定性财务模型 / 估值 | DCF、Comps、DDM、LBO、WACC、Monte Carlo、Earnings/IC | `accepted_external_lazy` | 无 |
| **Microsoft Qlib** | AI Quant / 因子 / ML / 组合优化 | screening、factor/model research、quant research | `accepted_external_lazy` | 无 |
| **Microsoft RD-Agent** | 自动量化研发 | 新因子发现、因子-模型联合优化、实验生成 | `accepted_external_lazy` | 无 |
| **QuantConnect LEAN** | 事件驱动策略级验证 | 策略回测、费用/滑点/订单/持仓路径 | `accepted_external_lazy` | 无 |
| Anthropic Financial Services | 专业方法 / second opinion | deep、模型审计、Earnings/Competitive/Thesis | `accepted_optional_method_upstream` | 无 |

### 外部引擎的权限语义

```text
OpenBB       = data authority only
TradingAgents= research candidate only
FinRobot     = model evidence only
Qlib         = quant research evidence only
RD-Agent     = experimental R&D candidate only
LEAN         = strategy validation evidence only
Anthropic    = specialist method evidence only
CIS          = final decision authority
```

所有外部项目的 BUY/SELL/HOLD、target price、score、portfolio action 都只能作为候选输入。

## 3. 专业职责边界

### OpenBB

负责“拿数据”，不负责“替 CIS 做最终判断”。数据发生重大冲突时仍回到 primary source / issuer filing / exchange / regulator source。

### TradingAgents

负责基本面、技术、新闻、情绪、多空反证、Research Manager/Trader/Risk/Portfolio 等通用多角色研究。原版 runtime 的 Portfolio Manager 结论记为 `external_decision_candidate`。

### FinRobot

负责需要确定性金融计算和透明假设的专业问题。CIS 不再优先让 LLM 自己重复心算完整 DCF/Comps。

### Qlib

负责 AI/ML Quant 研究、因子研究、组合优化、量化筛选和模型研究。仓库本地 `quant_factor_engine.py` 只保留为轻量 fallback / sanity check。

### RD-Agent

负责**研究研发**而不是日常投资问答。它可以提出并实现新因子/模型，但不能把实验结果直接升级到生产 CIS。

### LEAN

负责事件驱动策略级历史验证、订单模型、费用、滑点、持仓路径和策略统计。它不替代基本面、估值、新闻或 CIS 风险门。

## 4. 外部项目组合关系

最重要的量化研发链：

```text
RD-Agent
   ↓ 发现/实现候选因子与模型
Qlib
   ↓ Quant/ML 独立研究与评估
LEAN
   ↓ 事件驱动 / execution-realistic 验证
CIS Backtest Validation
   ↓
CIS policy review
```

最重要的股票研究链：

```text
OpenBB / primary sources
        ↓
TradingAgents
        ↓
FinRobot（需要专业估值/模型时）
        ↓
Evidence + Risk + CIS Score
        ↓
CIS final
```

## 5. Optional Local Research Tooling

位于 `extensions/research_tooling/`：

| 模块 | 主要职责 | 状态 |
|---|---|---|
| Quant Factor Ranking | 轻量大股票池 point-in-time 排序 | `experimental_fallback` |
| Baseline Backtest Evaluator | `score → forward_return` 横截面 sanity check | `experimental_baseline` |
| Prediction / Evaluation | 研究记录、结果与校准诊断 | `experimental_optional` |

这些工具的定位从“主要 Quant 能力”下调为：**外部 Qlib/LEAN 不可用时的有限 fallback，或用于轻量 CI/sanity check。**

不得声称：

- local quant extension 等价于 Qlib；
- baseline evaluator 等价于 LEAN；
- Prediction/Evaluation 可以自动优化生产评分。

## 6. 路由边界

- 一般单股研究 → OpenBB（数据可用时） + TradingAgents + CIS Gates；
- 估值/财务模型 → 加 FinRobot；deep 模式可加 Anthropic second opinion；
- 大股票池/Quant/ML → Qlib；Qlib 不可用才考虑 local Quant fallback；
- 新因子/模型研发 → RD-Agent → Qlib → LEAN → CIS Validation；
- 可执行策略/技术规则/仓位规则 → LEAN；
- ETF/QDII → CIS ETF Gate 始终保留；
- 短线价位 → CIS Tactical Gate 始终保留；
- 组合优化 → 组合数据完整后才允许 Qlib/Portfolio Gate；
- 外部模块故障不得伪装成成功，也不得绕过 Evidence/Risk。

## 7. 状态说明

- `accepted_default_methodology`：日常默认研究方法；
- `accepted_external_lazy`：正式接受，但只有任务需要且 runtime 实际可用时才调用；
- `accepted_optional_method_upstream`：方法增强，不作为默认双跑系统；
- `fail_closed_gate`：只有明确 pass 才可升级；
- `production_heuristic_pending_calibration`：已生产使用，但权重/阈值仍需未来样本校准；
- `experimental_fallback`：仅 fallback/sanity，不冒充专业上游；
- `experimental_baseline`：轻量 baseline，不冒充完整策略引擎；
- `experimental_optional`：实验性且不在默认链。

## 8. 维护原则

CIS 不 vendor 这些大型上游源码，不通过复制代码“拥有”它们。优先维护：

```text
routing contract
adapter contract
source/as_of contract
result contract
quality gates
version/review state
```

上游升级不得自动改变 CIS 生产规则或最终动作。
