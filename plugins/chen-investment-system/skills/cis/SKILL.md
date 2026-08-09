---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。投资语境下的股票/上市公司/ETF分析、估值、买卖、持仓、财报、风险、目标价、买入价、卖出价和跨标的比较默认进入 CIS。股票研究默认由当前 ChatGPT 会话直接执行 TradingAgents 多角色方法论；全市场/大股票池筛选按需先走 Quant Factor Ranking；原版 TradingAgents Python 仅在用户明确要求运行/测试时调用；专业财务、估值和财报方法按需使用 Anthropic Financial Services；最终由 CIS 执行证据门、风险门、关键维度门、八维评分、Market Regime、四层交易、ETF/QDII纪律、组合门和中文结论。
---

# 陈氏投资系统（CIS）0.4.2

CIS 是唯一用户入口和最终质量控制层。

**默认架构：ChatGPT → CIS Control Layer →（Quant 预筛按需）→ ChatGPT-native TradingAgents Methodology → 专业金融 Skills（按需）→ Evidence/Risk → Critical Dimensions → CIS Score → Market Regime → Trade/ETF/Portfolio Gate → 最终中文结论 → Prediction Ledger（按需）。**

日常研究不要求外部 LLM API，也不要求运行 TradingAgents Python。CIS 不自动下单。

## 自动触发规则

以下投资决策问题默认进入 CIS：

- `分析 MU`、`看看 NVDA`、`MU 能买吗`、`QQQ 还能持有吗`；
- 合理买入价、目标价、止盈、止损、估值、上涨空间、风险、财报影响；
- 持仓复盘、加减仓、退出；
- 多股票/ETF 比较；
- “今天最值得研究的美股”“从一批股票中筛选 Top N”等大股票池任务。

纯事实型问题如公司全称、代码、交易时间、上市地点，不强制运行完整 CIS。

## Runtime Guard

当 CIS 启动时：

1. 读取本 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 当前 `main`，不得凭聊天记忆恢复旧规则。
3. 股票任务读取 `references/tradingagents-methodology.md`，默认由 ChatGPT 直接执行多角色研究逻辑。
4. **TradingAgents 7 天 TTL**：读取 `runtime/tradingagents/upstream-status.json`。若距离 `last_checked_at` 不足 `check_ttl_days=7`，本次不访问 TradingAgents 上游；达到或超过 7 天时，由下一次股票研究执行 `scripts/check_tradingagents_upstream.py` 的同等逻辑轻量检查当前 `main` SHA。SHA 变化标记 `review_required`，未经审查的新逻辑不得进入 CIS。上游不可访问不阻塞正常研究。
5. 只有用户明确要求“运行原版 TradingAgents / 跑官方程序 / 系统测试”时，才启动 `references/tradingagents.md` 的本地/远程运行路径。
6. 原版 TradingAgents 的 `execution_status=success` / `runtime_readiness=remote_ready` 只表示程序执行完成；默认 `evidence_audit_status=not_run`、`research_quality=unreviewed`，不能直接作为最终研究结论。
7. 大股票池筛选读取 `references/quant-engine.md`；横截面必须同一 `as_of`。若涉及规则验证，再读 `references/backtest-validation.md`。
8. 当前市场环境会显著影响交易计划时读取 `references/market-regime.md`。
9. 需要历史校准/复盘时读取 `references/performance-loop.md`，使用 append-only Prediction Ledger。
10. 专业金融任务按需读取 `references/anthropic-financial-services.md`；只有本次真实可访问时才能声称实际运行。
11. 所有研究结果必须回到 CIS 最终质量门。

## 必读资料

每次运行先读：

1. `references/system-workflow.md`
2. `references/module-registry.md`
3. `references/module-routing.md`
4. `references/external-modules.md`
5. `references/tradingagents-methodology.md`
6. `references/anthropic-financial-services.md`
7. `references/agent-registry.md`
8. `references/agent-orchestration.md`
9. `references/scoring-engine.md`

按需读取：

- `references/tradingagents.md`（仅原版运行/测试/上游审查）
- `references/quant-engine.md`
- `references/backtest-validation.md`
- `references/market-regime.md`
- `references/performance-loop.md`
- `references/evidence-confidence.md`
- `references/investor-profile.md`
- `references/research-lifecycle.md`
- `references/output-modes.md`
- `references/four-layer-trading-framework.md`
- `references/cross-border-etf-premium.md`
- `references/io-contract.md`
- `references/agent-contract.md`

## 默认研究核心：ChatGPT-native TradingAgents Methodology

```text
Market / Technical
+ Fundamentals
+ News / Catalyst
+ Sentiment / Positioning（按需）
        ↓
Bull / Bear 独立反证
        ↓
Research Manager 综合
        ↓
Trader / Risk / Portfolio（按任务需要）
        ↓
methodology_candidate
```

`methodology_candidate` 不是原版 TradingAgents 的 `external_decision_candidate`，也不是 CIS 最终动作。

### 多角色独立性规则

- Analyst 必须引用可核验事实，不把模型观点当证据。
- Bull 优先寻找支持上涨路径的独立证据。
- Bear 必须主动寻找与 Bull 不同来源/机制的反证，不得只改写 Bull。
- Risk 必须寻找尾部风险、论点失效和流动性/集中度风险。
- Research Manager 不得创造新事实，只能裁决已登记证据和冲突。

## Quant Factor Ranking Engine

用于“大股票池 → 候选”任务：

```text
Point-in-time 股票池
  ↓
同一 as_of 因子数据
  ↓
quant_score + factor_coverage
  ↓
Top N 候选
  ↓
ChatGPT-native TradingAgents Methodology 深研
```

`quant_score` 与 `cis_score` 严格分开。Quant baseline 权重目前标记 `experimental_uncalibrated`。`max_drawdown_1y` 支持有符号回撤或正的回撤绝对值，引擎统一取绝对值后按越小越好排序。

## Backtest / Validation

新增规则、因子、阈值或评分权重，不得仅凭直觉成为默认规则。必须检查：

- look-ahead / survivorship / universe drift / restatement leakage；
- CAGR、Sharpe、最大回撤、胜率、超额收益；
- **按实际组合换手率计算交易成本**；
- train / validation / out-of-sample；
- 样本足够时 walk-forward 稳定性。

## Fail-Closed Evidence / Risk + Critical Dimension Gate

评分引擎默认：

```text
audit_status = unverified
risk_status  = unverified
```

只有明确 `pass` 才可进入 `decision_grade`。

Coverage 之外还必须检查关键维度：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

关键维度缺失，即使 coverage >=85%，仍只能 provisional。

## Market Regime

Regime 只用于环境修正，不直接买卖。Baseline 可使用趋势、广度、VIX、实现波动、信用利差绝对水平和信用变化；严格校验 JSON boolean 和数值范围。

输出：`risk_on | neutral | risk_off | insufficient`。

## Prediction Ledger / Performance Loop

长期可复盘研究使用：

```text
scripts/prediction_ledger.py
runtime/evaluations/predictions.jsonl
```

Prediction 和 Outcome 采用 append-only event，禁止结果已知后回写历史预测。Performance 评估按总分、horizon、regime 和八维 dimension 做诊断，禁止自动覆盖生产权重。

## 原版 TradingAgents：显式测试模式

- 本地：`scripts/run_tradingagents.py`。
- 远程：`.github/workflows/cis-tradingagents.yml`。
- 远程每次运行重新 clone `TauricResearch/TradingAgents` 当前 `main`。
- 手动 `workflow_dispatch` 必须显式填写 request_id/ticker/analysis_date 等参数，不再默默复用旧 request.json。
- 结果状态拆为 `execution_status`、`runtime_readiness`、`evidence_audit_status`、`research_quality`。
- `external_decision_candidate` 永远没有最终动作权。

## TradingAgents 上游更新策略

```text
7天 TTL 未到 → 不访问上游
TTL 到期 → 下一次股票研究轻量检查 main SHA
SHA 未变 → 刷新 last_checked_at
SHA 变化 → review_required → 当次继续稳定基线
```

不使用定时 GitHub Actions 监控，不允许上游代码自动覆盖 CIS 方法论。

## 专业金融方法

DCF / Comps / 三表 / 模型审计 / Earnings / Initiating Coverage / Model Update / Competitive Analysis / Thesis / Catalyst 等子问题按需使用 Anthropic Financial Services 对应 Skill，并回到 CIS 证据登记。

## 标准输入

```text
research_type: company | stock | ETF | portfolio | industry | macro | earnings | screening | backtest
subject: 标的或股票池
research_question: 本次问题
mode: quick | standard | deep | holding_review
analysis_date/as_of: 数据截止时间
horizon: 短期 | 1-3年 | 3-10年
decision_context: generic | long_term | tactical | earnings
portfolio_context: 持仓、权重、成本、基准、约束、资金需求
```

默认 `standard`；真实持仓增减/退出使用 `holding_review`。

## 执行顺序

1. Intake：对象、问题、模式、期限、`as_of`、decision_context。
2. Runtime Guard：读取 GitHub 当前 CIS；按 7 天 TTL 决定是否检查 TradingAgents 上游。
3. Quant Pre-screen：仅大股票池/排名任务按需执行。
4. Evidence：采集并登记事实、计算、假设、来源和限制。
5. Core Research：ChatGPT 直接执行 TradingAgents Methodology。
6. Professional Skills：按需 Anthropic。
7. Audit/Risk：两者均必须明确 pass 才能放行决策级。
8. Critical Dimensions：按任务检查关键维度。
9. Score：按 `scoring-engine.md`。
10. Regime：当前市场环境会影响交易计划时执行。
11. Trade Framework：涉及买卖/价位时执行趋势 → 价格 → 成交 → 风险。
12. ETF/Portfolio Gate：按任务执行。
13. Synthesis：最终中文研究姿态、证伪条件、复盘触发点。
14. Prediction Ledger：需要长期校准时记录不可变研究快照。

## 八维评分

权重只以 `references/scoring-engine.md` 为准：

- fundamentals 20
- growth 15
- valuation 15
- industry_competitive 10
- technical 15
- catalyst_macro 10
- positioning 5
- risk_resilience 10

`coverage < 70%` 不输出单一总分；`70% <= coverage < 85%` 为 provisional；`coverage >= 85%` 也必须通过 Audit/Risk/Critical Dimensions 才可 decision_grade。

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. 趋势：20/50/200 日均线和趋势状态；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈和防守止损。

## ETF / QDII

跨境 ETF/QDII 必须执行产品身份、精确基准、IOPV、历史溢价、申赎/额度、时差和流动性纪律，不默认套用股票多 Agent 结论。

## 组合门

只有真实持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位/再平衡比例。当前 CIS 不连接 Broker 自动执行交易。

## 最终输出最低要求

- CIS 规则版本；
- 本次使用 ChatGPT-native methodology / Quant / Regime / 原版 TradingAgents 的实际状态；
- TradingAgents `upstream_check` 状态（适用时）；
- 数据截止时间；
- Anthropic 专业 Skill 是否实际运行；
- Evidence/Risk/Critical Dimension Gate 状态；
- CIS 评分 coverage；
- 为什么不是更高/更低分；
- 关键证伪条件和复盘触发点。
