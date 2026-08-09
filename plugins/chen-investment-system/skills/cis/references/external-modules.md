# CIS 外部模块适配与降级（0.4.5，Control Plane v2）

外部模块必须拆开判断：

```text
存在/可访问
≠ 程序执行成功
≠ 研究质量通过
≠ 可以发布 CIS 最终动作
```

README、历史运行记录、聊天记忆或模块名称都不能证明本次已运行。

## 1. 外部引擎总原则

CIS 正式接受以下专业外部能力：

```text
OpenBB                  → 数据基础设施
TradingAgents           → 通用多 Agent 股票研究
FinRobot                → 确定性估值/财务建模
Microsoft Qlib          → AI Quant / ML / 因子 / 组合研究
Microsoft RD-Agent      → 自动量化 R&D
QuantConnect LEAN       → 策略级事件驱动回测与执行验证
Anthropic Financial Services → 专业方法增强 / second opinion
```

统一边界：

```text
decision_authority = none
final_decision_authority = CIS Control Layer
```

外部项目不 vendor 到 CIS，不因上游更新自动修改生产规则。

## 2. OpenBB

- 上游：`OpenBB-finance/OpenBB`；
- CIS 定位：**data_fabric**，不是投资决策引擎；
- 用于统一接入行情、基本面、宏观及多 provider 数据；
- 可以向 TradingAgents、FinRobot、Qlib 或 CIS Evidence Layer 提供标准化数据输入。

### 数据纪律

- OpenBB provider 数据不天然高于 primary source；
- 财报重大数字冲突时优先 SEC/issuer filing/regulator source；
- 行情关键冲突时优先交易所或更直接的 market-data source；
- 必须保存 provider、`as_of`/timestamp、currency、unit；
- provider failover 后必须披露口径差异风险。

降级：OpenBB 不可用 → primary source / direct provider / public web。不得声称“OpenBB 已运行”。

## 3. TradingAgents

- 上游：`TauricResearch/TradingAgents`；
- CIS 定位：**general_multi_agent_research**；
- 日常股票研究可使用已审查的 ChatGPT-native TradingAgents Methodology；
- 原版 Python runtime 仅在用户明确运行/测试、A/B 或上游审查时执行；
- 原版 Portfolio Manager 的 BUY/SELL/HOLD 统一记为 `external_decision_candidate`。

### 上游安全

保留 7 天 TTL、`reviewed_sha`、secret-backed 只运行已审查 SHA、第三方执行 Job 无写权限等现有安全边界。

原版 runtime 成功只表示程序完成；最终仍需要 CIS Evidence/Risk/Score。

## 4. FinRobot

- 上游：`AI4Finance-Foundation/FinRobot`；
- CIS 定位：**deterministic_financial_modeling**；
- 正式接受为专业估值/模型引擎。

优先任务：

```text
DCF
Comps
DDM
LBO
WACC
Monte Carlo valuation
Earnings modeling
IC-style equity research output
```

### 规则

- 优先使用经过 CIS Evidence Layer 核验的数据输入；
- 保留模型假设、数值来源和计算 provenance；
- 与其他模型冲突时逐项核对 WACC、增长率、终值、margin、capex、peer set 等；
- 不简单平均目标价；
- FinRobot 的 Judge/Agent 结论仍没有最终 CIS 动作权。

降级：FinRobot 不可用 → Anthropic Financial Services 或透明 CIS 计算。fallback 必须显式标记。

## 5. Microsoft Qlib

- 上游：`microsoft/qlib`；
- CIS 定位：**quant_ml_research**；
- 正式接受为专业 Quant/ML/因子研究层。

适用：

```text
factor research
ML signal/model research
quant screening
portfolio optimization
model/research backtest
```

Qlib 与本地 `extensions/research_tooling/quant_factor_engine.py` 不同：后者只是轻量 fallback/sanity check，不能冒充完整 Qlib。

### 研究纪律

- 数据必须 point-in-time；
- 避免 survivorship、restatement leakage、universe drift；
- 训练/验证/OOS 分离；
- 因子/模型结果只作为 quantitative evidence；
- Qlib 结果不直接修改 CIS Score 权重。

## 6. Microsoft RD-Agent

- 上游：`microsoft/RD-Agent`；
- CIS 定位：**autonomous_quant_rnd**；
- 正式接受，但只在 R&D intent 下按需运行。

适用：

```text
factor discovery
factor-model co-optimization
quant experiment generation
automated R&D loop
```

不适用：一般单股研究、普通买卖判断、简单估值。

### 生产升级链

```text
RD-Agent candidate
→ Qlib independent evaluation
→ LEAN strategy/execution validation
→ CIS Backtest Validation
→ policy review
→ production
```

RD-Agent 的新候选默认：

```text
research_quality = experimental
production_authority = none
```

RD-Agent 不可用时无静默等价替代。

## 7. QuantConnect LEAN

- 上游：`QuantConnect/Lean`；
- CIS 定位：**external_quant_validation**；
- 适配层：`integrations/lean/cis_lean_adapter.py`；
- 用于事件驱动策略、订单、费用、滑点、持仓路径、期权/ETF/股票策略级验证；
- 不负责基本面、新闻、估值或最终动作。

状态：

```text
execution_status = success | error | invalid_input | unavailable
runtime_readiness = ready | lean_cli_missing | docker_missing | unavailable
research_quality = unreviewed
engine_role = external_quant_validation
decision_authority = none
```

显式 LEAN 请求不可用时必须报告 unavailable/error，禁止拿 baseline evaluator 冒充。

LEAN 结果仍需 `backtest-validation.md` 检查 look-ahead、survivorship、费用/滑点、OOS、参数稳健性与执行真实性。

当前 CIS 不启用 LEAN live trading / Broker 自动执行。

## 8. Anthropic Financial Services

Anthropic Financial Services 继续保留为**专业方法上游 / second opinion**，用于模型审计、Earnings、Competitive、Thesis、Catalyst 等。

在 FinRobot 已完成确定性模型后，不无理由再跑一套同质 DCF。deep 模式只有在能提供独立方法或审计价值时才增加 Anthropic。

只有本次真实可访问并读取/执行对应 Skill，才能标记为已使用。

## 9. 数据与模型冲突

### 数据冲突

```text
primary source
→ freshness
→ provider coverage
→ accounting/unit/currency consistency
```

### 估值冲突

比较输入和假设，不平均 target。

### Qlib vs LEAN

- Qlib：研究、因子、ML、组合层；
- LEAN：订单、费用、滑点、持仓路径、event-driven execution；
- 执行真实性问题优先参考 LEAN；
- 研究有效性问题优先审查 Qlib 实验设计；
- 二者最终都回到 CIS Gate。

## 10. Optional Local Research Tooling

仓库本地外围工具继续保留，但角色改为：

- Quant Factor Ranking → Qlib unavailable 时的轻量 fallback；
- Baseline Backtest → 横截面 sanity check；
- Prediction/Evaluation → 记录、复盘与校准诊断。

它们不属于默认单股 Core，也不等价于 Qlib / LEAN。

## 11. 外部模块更新策略

CIS 不追求自动跟随所有 upstream main。对任何上游升级先检查：

```text
repo identity
license
API/CLI contract
dependencies
runtime requirements
output schema
security boundary
representative tests
```

只有审查通过后才能改变稳定路由/适配器。

## 12. 其他可选项目

Vibe-Trading、NautilusTrader、Buffett skill 等可作为未来 optional adapter 或专项视角，但不替代已经正式分工的 OpenBB / TradingAgents / FinRobot / Qlib / RD-Agent / LEAN，也没有最终 CIS 动作权。
