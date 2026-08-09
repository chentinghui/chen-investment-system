---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。股票/上市公司/ETF分析、估值、买卖、持仓、财报、风险、目标价、买入价、卖出价和跨标的比较默认进入 CIS。日常单股研究由 CIS Core 完成；Quant、Backtest、Prediction/Evaluation 仅作为按需外围工具，不属于默认分析链。
---

# 陈氏投资系统（CIS）0.4.2

CIS 是唯一用户入口和最终质量控制层。**CIS Core 的职责是分析，不负责默认记录、自动结算或绩效数据库。**

## 默认核心架构

```text
ChatGPT
  ↓
CIS Control Layer
  ↓
ChatGPT-native TradingAgents Methodology
  ↓
Anthropic Financial Services（专业子问题按需）
  ↓
Evidence Audit + Risk Review
  ↓
Critical Dimension Gate
  ↓
CIS Score
  ↓
Market Regime（按交易问题需要）
  ↓
Trade / ETF / Portfolio Gate
  ↓
最终中文分析结论
```

日常研究不要求外部 LLM API，也不要求运行原版 TradingAgents Python。CIS 不自动下单。

## Optional Research Tooling

以下能力保留在仓库外围，不属于 CIS Core：

```text
extensions/research_tooling/
```

- Quant：仅大股票池/Top N/系统筛选时按需调用；
- Backtest：仅验证新规则、因子、阈值或权重时调用；
- Prediction / Evaluation：仅用户明确要求记录、复盘或校准时调用；
- 外围工具故障不得阻塞日常单股分析；
- 外围工具没有最终动作权，也不得自动改写生产评分规则。

## 自动触发规则

以下投资决策问题默认进入 CIS：

- `分析 MU`、`看看 NVDA`、`MU 能买吗`、`QQQ 还能持有吗`；
- 合理买入价、目标价、止盈、止损、估值、上涨空间、风险、财报影响；
- 持仓复盘、加减仓、退出；
- 多股票/ETF比较；
- 大股票池 Top N 任务仍由 CIS 受理，但按需路由 Optional Quant。

纯事实问题如公司全称、代码、交易时间、上市地点，不强制运行完整 CIS。

## Runtime Guard

1. 读取当前 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 当前 `main`，不得凭聊天记忆恢复旧规则。
3. 股票任务读取 `references/tradingagents-methodology.md`，默认由当前 ChatGPT 会话执行多角色研究逻辑。
4. **TradingAgents 7 天 TTL**：读取 `runtime/tradingagents/upstream-status.json`。TTL 未到不访问上游；达到或超过 7 天后，由下一次股票研究执行 `scripts/check_tradingagents_upstream.py` 的同等逻辑轻量检查当前 `main` SHA。新 SHA 标记 `review_required`，未经审查不得进入 CIS。上游不可访问不阻塞正常研究。
5. 只有用户明确要求运行/测试原版 TradingAgents 时，才启动 `references/tradingagents.md` 的本地/远程路径。
6. 原版 TradingAgents 的 `execution_status=success` / `runtime_readiness=remote_ready` 只表示程序完成；`research_quality` 未审查时不能直接作为最终结论。
7. 当前市场环境会显著影响交易计划时读取 `references/market-regime.md`。
8. 专业金融任务按需读取 `references/anthropic-financial-services.md`；只有本次真实可访问时才能声称实际运行。
9. 大股票池筛选、规则回测或历史校准时，才读取对应 references 并路由 `extensions/research_tooling/`。
10. 所有外部/外围结果必须回到 CIS 最终质量门。

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
- `references/quant-engine.md`（仅筛选任务）
- `references/backtest-validation.md`（仅规则验证）
- `references/performance-loop.md`（仅记录/复盘/校准）
- `references/market-regime.md`
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

### 多角色独立性

- Analyst 必须引用可核验事实，不把模型观点当证据。
- Bull 建立最强上涨路径与支持证据。
- Bear 主动寻找不同来源/机制的反证，不得只改写 Bull。
- Risk 检查尾部风险、论点失效和流动性/集中度风险。
- Research Manager 不创造新事实，只裁决已登记证据和冲突。

## 外部项目更新策略

### TradingAgents

```text
7天 TTL 未到 → 不访问上游
TTL 到期 → 下一次股票研究轻量检查 main SHA
SHA 未变 → 刷新检查时间
SHA 变化 → review_required → 继续使用稳定基线
```

不使用定时 GitHub Actions 监控；不允许未经审查的上游变化自动覆盖 CIS。用户明确要求运行原版 TradingAgents 时，显式测试路径仍重新 clone 上游当前 `main`。

### Anthropic Financial Services

DCF / Comps / Earnings / 三表 / 模型审计 / Competitive / Thesis / Catalyst 等专业子问题按需优先读取上游 `main` 对应 Skill。只有本次真实读取/执行后才能标记已使用，输出仍需回到 CIS Evidence/Risk/Score。

## Fail-Closed Evidence / Risk + Critical Dimension Gate

评分引擎默认：

```text
audit_status = unverified
risk_status  = unverified
```

只有明确 `pass` 才可进入 `decision_grade`。

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

关键维度缺失，即使 coverage >=85%，仍只能 provisional。

## Market Regime

Regime 只用于环境修正，不直接机械买卖。输出：

```text
risk_on | neutral | risk_off | insufficient
```

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
2. Runtime Guard：核验当前 CIS；按 7 天 TTL 决定是否检查 TradingAgents 上游。
3. Evidence：采集并登记事实、计算、假设、来源和限制。
4. Core Research：执行 ChatGPT-native TradingAgents Methodology。
5. Professional Skills：按需 Anthropic。
6. Audit/Risk：两者均必须明确 pass 才能放行决策级。
7. Critical Dimensions：按任务检查关键维度。
8. Score：按 `scoring-engine.md`。
9. Regime：当前环境会改变交易计划时执行。
10. Trade Framework：涉及买卖/价位时执行趋势 → 价格 → 成交 → 风险。
11. ETF/Portfolio Gate：按任务执行。
12. Synthesis：最终中文研究姿态、价位/风险条件、证伪条件和复盘触发点。
13. **Optional Extension**：只有筛选、规则验证、记录/复盘/校准任务才额外调用外围工具。

## 八维评分

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

跨境 ETF/QDII 必须执行产品身份、精确基准、IOPV、历史溢价、申赎/额度、时差和流动性纪律。

## 组合门

只有真实持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位/再平衡比例。CIS 不连接 Broker 自动执行交易。

## 最终输出最低要求

- CIS 规则版本；
- 本次实际使用的 Core/Extension/外部模块状态；
- TradingAgents `upstream_check` 状态（适用时）；
- 数据截止时间；
- Anthropic 专业 Skill 是否实际运行；
- Evidence/Risk/Critical Dimension Gate 状态；
- CIS 评分 coverage；
- 为什么不是更高/更低分；
- 关键证伪条件和复盘触发点。
