# CIS 0.4.5 模块路由（Control Plane v2）

## 总原则

CIS 是唯一用户入口和最终质量控制层。总控采用 **minimum sufficient routing（最少充分路由）**：只调用能增加独立信息价值的专业模块，不为了“看起来复杂”而把所有项目都跑一遍。

确定性路由器：

```text
scripts/route_cis.py
```

外部能力登记表：

```text
references/external-engine-registry.json
```

## 1. Intent 标准化

自然语言任务先映射到以下 intent：

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

同时登记：

```text
asset_type = equity | etf | crypto | portfolio | other
mode = fast | standard | deep
as_of
explicit_lean
needs_backtest
needs_new_factor_rnd
needs_portfolio_optimization
```

未知 intent 或非法机器字段必须 fail closed，不允许“猜一个最接近的动作然后继续”。

## 2. 默认专业路由

| 用户任务 | 默认专业引擎 | 可选增强 | CIS 必经质量门 |
|---|---|---|---|
| 纯事实/数据 | OpenBB / primary source | direct provider/web | source/as_of check |
| 一般股票研究 | OpenBB + TradingAgents | deep: Anthropic method | Evidence + Risk + Critical + Score |
| 基本面+技术+新闻综合 | OpenBB + TradingAgents | — | Evidence + Risk + Score |
| 多空观点 | TradingAgents Bull/Bear/Manager | — | conflict reconciliation |
| DCF / Comps / 估值 | OpenBB + TradingAgents + **FinRobot** | deep: Anthropic audit | valuation reconciliation + Evidence |
| 财报前后 | OpenBB + TradingAgents + **FinRobot** | deep: Anthropic Earnings | catalyst + valuation + Risk |
| 大股票池筛选 | OpenBB + **Qlib** | local Quant fallback | 候选回到 CIS Core 深研 |
| Quant / ML / 因子研究 | **Qlib** | OpenBB data | bias/evidence review |
| 新因子/模型自动研发 | **RD-Agent → Qlib → LEAN** | — | Backtest Validation + policy review |
| 可执行策略是否有效 | **LEAN** | Qlib（若策略源于ML/因子） | Backtest Validation |
| 短线买入/做差价 | OpenBB + TradingAgents | Regime | Price/Session + R/R + Four-layer |
| 持仓复盘 | OpenBB + TradingAgents | FinRobot/Anthropic（按问题） | Risk + Portfolio Gate |
| ETF / QDII | OpenBB / product sources | LEAN（仅策略验证） | ETF/QDII Gate |
| 组合优化 | OpenBB + Qlib | — | Portfolio Gate |
| 历史复盘/校准 | Prediction/Evaluation Extension | LEAN/Qlib视任务 | horizon separation |
| 原版 TradingAgents A/B | Original runtime | — | external candidate only |

## 3. Fast / Standard / Deep

### fast

目标：快速但不破坏质量门。

- general/tactical/holding：OpenBB + TradingAgents；
- valuation/earnings：OpenBB + FinRobot；
- screening：OpenBB + Qlib；
- 用户显式指定的 LEAN/Qlib/RD-Agent 不因 fast 被删除。

### standard

按 intent 使用默认专业路由，不无理由双跑同职责引擎。

### deep

允许增加独立 second opinion，但只在能提供不同方法/证据时使用。例如估值任务可在 FinRobot 之后增加 Anthropic Financial Services 做模型方法审计；不得只是把同一个 DCF 换个 LLM 再算一次。

## 4. OpenBB 路由

OpenBB 是 CIS 的**数据基础设施层**，主要服务：

- current/historical market data；
- fundamentals；
- macro；
- 多 provider 数据接入；
- 下游 Qlib / TradingAgents / FinRobot 的统一数据准备。

规则：

- OpenBB provider 输出不天然高于 SEC、交易所、公司公告等 primary source；
- 关键数据冲突时优先核验 primary source；
- 记录 provider、timestamp/as_of、货币与单位；
- provider fallback 必须披露，不能把不同口径数据无提示拼接。

## 5. TradingAgents 路由

TradingAgents 负责**通用投资研究方法论**：基本面、技术、新闻、情绪、Bull/Bear、Research Manager、Trader/Risk/Portfolio 视角。

- 日常可使用已审查 ChatGPT-native methodology；
- 原版 Python runtime 只有明确运行/测试时才执行；
- 原版 Portfolio Manager 的 BUY/SELL/HOLD = `external_decision_candidate`；
- 不替代 CIS Evidence/Risk/Score/ETF/Portfolio/Tactical gates。

## 6. FinRobot 路由

FinRobot 是 CIS 的**专业确定性金融建模引擎**，优先用于：

```text
DCF
Comps
DDM
LBO
WACC
Monte Carlo valuation
Earnings modeling
IC-style report
```

总控职责：

- 尽量使用已核验数据输入；
- 保存关键假设与数值 provenance；
- FinRobot 输出与其他估值冲突时，逐项比较假设；
- 不平均目标价，不因“模型数量多”提高 confidence。

FinRobot 不可用时，可使用 Anthropic Financial Services 或透明 CIS 计算，但必须明确是 fallback，不能声称已运行 FinRobot。

## 7. Qlib 路由

Qlib 负责 CIS 的**专业 AI Quant/ML 研究层**：

- 因子研究；
- ML signal/model；
- portfolio optimization；
- quant screening；
- research backtest/model evaluation。

本地 `extensions/research_tooling/quant_factor_engine.py` 只作为：

- 轻量筛选 fallback；
- CI/sanity check；
- Qlib runtime 不可用时的有限降级。

不得将本地 extension 宣称为 Qlib 等价替代。

## 8. RD-Agent 路由

RD-Agent 仅用于**研发型任务**：

```text
factor discovery
factor-model co-optimization
quant experiment generation
automated R&D loop
```

普通单股研究、一般买卖判断、简单 DCF 不调用 RD-Agent。

新候选升级链固定为：

```text
RD-Agent candidate
→ Qlib independent quant evaluation
→ LEAN strategy/execution validation
→ CIS Backtest Validation
→ manual/policy review
→ production
```

任何一步未通过，都不能自动进入生产 CIS 评分权重或交易规则。

## 9. QuantConnect LEAN 路由

LEAN 是 CIS 的**策略级事件驱动验证引擎**，适配层：

```text
integrations/lean/cis_lean_adapter.py
```

适用：

- 明确的可执行策略；
- 技术规则；
- 仓位规则；
- options/ETF/stock strategy；
- 需要订单、费用、滑点、持仓路径时。

不适用：

- 普通单股基本面研究；
- 纯新闻解释；
- 纯 DCF；
- 没有明确规则的“这股票未来会不会涨”。

如果用户明确要求 LEAN：不可用时必须报告 unavailable/error，**不得用 baseline evaluator 冒充**。

LEAN 结果默认：

```text
engine_role = external_quant_validation
decision_authority = none
research_quality = unreviewed
```

## 10. Quant研发与策略验证的职责分工

```text
RD-Agent = 发明候选
Qlib     = 研究候选
LEAN     = 验证可执行策略路径
CIS      = 决定是否接受为系统规则
```

因此 Qlib 和 LEAN 不是互相替代：

- Qlib 强在 data/model/factor/ML research；
- LEAN 强在 event-driven order/fee/slippage/portfolio-path validation。

## 11. Tactical Price / R/R 路由

只要用户要求短期差价、明确买入价、追不追、止损或目标价，就运行：

```text
scripts/tactical_setup_gate.py
```

至少登记：

```text
analysis_timestamp
quote_timestamp
exchange
price_type
current_price
Entry Zone
Stop + stop_type
Target 1
```

并执行现有：Price/Session、Quote Freshness、Setup Lifecycle、R/R baseline、Four-layer Trading Gate。

质量分与短线 setup readiness 必须分开。

## 12. ETF / Portfolio 路由

### ETF/QDII

无论外部数据/回测多强，CIS 自有 ETF/QDII Gate 始终保留：产品身份、NAV/IOPV、溢价、申赎、时差、流动性。

### Portfolio

只有真实组合数据完整时才能给精确仓位/再平衡建议。Qlib 的 portfolio optimization 是研究输入，不覆盖用户现金需求、税务、集中度与 CIS 风险约束。

## 13. 冲突仲裁优先级

### 事实冲突

```text
primary source
→ freshness / as_of
→ provider coverage
→ accounting / unit / currency consistency
```

### 估值冲突

拆解 WACC、增长率、终值、可比公司、利润率、资本开支、稀释等假设；禁止简单平均。

### Quant vs Fundamentals

先区分时间尺度、目标变量与假设。短期量化信号弱不能自动推翻长期基本面；长期基本面好也不能覆盖当前极差的执行赔率。

### Qlib vs LEAN

- 研究有效性问题：优先看 Qlib 的实验设计与样本外证据；
- 订单/费用/滑点/持仓路径问题：LEAN 的执行验证优先级更高；
- 两者都不能绕过 CIS Evidence/Risk。

## 14. 防重叠

- OpenBB 不做最终判断；
- TradingAgents 不重复 FinRobot 的确定性财务模型；
- FinRobot 不重复 Qlib 的 ML Quant；
- Qlib 不替代 LEAN 的 event-driven execution validation；
- RD-Agent 不进入日常单股链；
- Anthropic 默认不与 FinRobot 无理由双跑；
- local Quant/Backtest 仅 fallback/sanity；
- 外部结果最后统一回灌 CIS。

## 15. 最终顺序

```text
Intake / as_of
→ Data / primary-source verification
→ General research
→ Specialist modeling
→ Quant/R&D（按需）
→ Strategy validation（按需）
→ Evidence Audit
→ Risk Review
→ Critical Dimensions
→ CIS Score
→ Regime / Tactical / ETF / Portfolio Gates（按需）
→ 最终中文结论
```
