# CIS 0.4.5 Agent / Engine 登记表（Control Plane v2）

CIS 采用“**一个总控 + 多个专业外部引擎 + CIS 自有质量门**”结构。总控只调用最少数量、职责不重叠且能增加独立信息价值的模块。

## 1. CIS Control Layer

| 模块/Agent | 主要职责 | 状态 | 最终动作权 |
|---|---|---|---|
| 陈氏投资分析师 | Intake、意图标准化、路由、冲突仲裁、最终中文结论 | **始终启用** | **唯一有** |
| Deterministic Route Planner | `intent/asset/mode` → 专业引擎执行计划 | installed | 无 |
| External Engine Registry | 外部项目职责、fallback、权限、输出类别 | installed | 无 |
| Evidence Audit | 来源、时效、前视偏差、冲突 | fail-closed | 阻止升级 |
| Risk Review | 尾部风险、论点失效、集中度/流动性 | fail-closed | 阻止升级 |
| Critical Dimension Gate | 按 decision_context 检查关键维度 | installed | 阻止升级 |
| CIS Scoring | 八维 coverage + weighted score | production heuristic | 无单独动作权 |
| Market Regime | 风险环境修正 | 按需 | 无 |
| Price / Session Guard | session / quote freshness | tactical | 阻止交易 setup |
| Tactical R/R Gate | Entry / Stop / Target / R/R / lifecycle | tactical | 阻止交易 setup |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | installed | 阻止产品动作 |
| Portfolio Gate | 权重、成本、集中度、约束、资金需求 | 按需 | 阻止组合动作 |

## 2. 默认研究角色 — TradingAgents Methodology

| 角色 | 主要职责 | 默认条件 |
|---|---|---|
| Market / Technical | 趋势、动量、波动、关键价位 | 股票研究 |
| Fundamentals | 财务、业务质量、KPI | 股票研究 |
| News / Catalyst | 公司/行业/宏观事件 | 股票研究 |
| Sentiment / Positioning | 机构、资金流、拥挤度 | 数据可用且会改变结论 |
| Bull Researcher | 最强看多路径与支持证据 | standard/deep |
| Bear Researcher | 独立反证与下行机制 | standard/deep |
| Research Manager | 裁决冲突，不创造新事实 | standard/deep |
| Trader Perspective | 条件化入场/等待/止盈/防守 | 涉及交易 |
| Risk Perspective | 尾部风险、论点失效、流动性/集中度 | standard/deep/holding |
| Portfolio Perspective | 组合影响 | 真实组合资料完整 |

这些角色没有最终动作权。原版 TradingAgents Portfolio Manager 输出统一为 `external_decision_candidate`。

## 3. Accepted External Specialist Engines

| Engine | Role | 输出类别 | 默认用途 | 最终动作权 |
|---|---|---|---|---|
| **OpenBB** | data_fabric | `evidence_input` | 行情、基本面、宏观、多 provider 数据 | 无 |
| **TradingAgents** | general_multi_agent_research | `research_candidate` | 一般股票研究、多空、交易假设 | 无 |
| **FinRobot** | deterministic_financial_modeling | `specialist_model_evidence` | DCF/Comps/DDM/LBO/WACC/Monte Carlo/Earnings | 无 |
| **Microsoft Qlib** | quant_ml_research | `quant_research_evidence` | 因子、ML、筛选、组合优化 | 无 |
| **Microsoft RD-Agent** | autonomous_quant_rnd | `experimental_research_candidate` | 新因子/新模型研发 | 无 |
| **QuantConnect LEAN** | event_driven_strategy_validation | `external_quant_validation` | 策略、订单、费用、滑点、持仓路径回测 | 无 |
| Anthropic Financial Services | professional_financial_methodology | `specialist_method_evidence` | 模型审计、Earnings、Competitive、Thesis、Catalyst | 无 |

机器登记表：

```text
references/external-engine-registry.json
```

## 4. Quant R&D 团队关系

```text
RD-Agent = Research & Development
     ↓
Qlib     = Quant research / independent evaluation
     ↓
LEAN     = Event-driven execution validation
     ↓
CIS      = Backtest Validation / policy decision
```

- RD-Agent 发现/实现候选；
- Qlib 判断因子/模型是否有研究价值；
- LEAN 检查策略在更接近真实订单/费用/持仓路径下是否成立；
- CIS 决定是否允许升级为生产规则。

## 5. Optional Local Research Tooling

位于 `extensions/research_tooling/`：

| 模块 | 主要职责 | 状态 | 与外部专业引擎关系 |
|---|---|---|---|
| Quant Factor Ranking | 轻量 point-in-time 排序 | experimental fallback | 不等价于 Qlib |
| Baseline Backtest | 横截面 `score→forward_return` sanity | experimental baseline | 不等价于 LEAN |
| Prediction / Evaluation | 研究记录、复盘、校准诊断 | experimental optional | 不自动改生产规则 |

## 6. 权限矩阵

```text
CIS Control Layer   = final publish authority
Evidence/Risk Gates = veto/hold authority
OpenBB               = data input authority
TradingAgents        = research candidate authority
FinRobot             = deterministic model evidence authority
Qlib                 = quant research evidence authority
RD-Agent              = experimental R&D candidate authority
LEAN                  = strategy validation evidence authority
Anthropic             = specialist method evidence authority
```

任何外部 Agent/Engine 的 BUY、SELL、HOLD、score、target、position recommendation 均不能直接发布为 CIS 最终动作。

## 7. 防重叠规则

- OpenBB 不做投资裁决；
- TradingAgents 不重复 FinRobot 的确定性模型；
- FinRobot 不重复 Qlib 的 ML Quant；
- Qlib 不替代 LEAN 的 event-driven execution validation；
- RD-Agent 不进入普通单股问答；
- Anthropic 只在方法/审计价值独立时作为增强；
- local Quant/Backtest 只做 fallback/sanity；
- 所有结果最终统一回到 CIS Evidence/Risk/Score/Gates。

## 8. 运行状态必须分层

对于任何外部引擎，总控必须区分：

```text
availability
execution_status
data_as_of
research_quality
evidence_audit_status
accepted_by_cis
```

`installed`、`remote_ready`、`execution_status=success` 都不能自动推导 `research_quality=accepted`。
