---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。股票/上市公司/ETF分析、估值、买卖、持仓、财报、风险、目标价、买入价、卖出价和跨标的比较默认进入 CIS。日常单股研究由 CIS Core 完成；Quant、Backtest、Prediction/Evaluation 仅作为按需外围工具，不属于默认分析链。
---

# 陈氏投资系统（CIS）0.4.3

CIS 是唯一用户入口和最终质量控制层。**CIS Core 的职责是分析，不负责默认记录、自动结算或绩效数据库。** CIS 不自动下单。

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
Price/Session Guard + Tactical R/R Gate（短线按需）
  ↓
Trade / ETF / Portfolio Gate
  ↓
最终中文分析结论
```

日常研究不要求外部 LLM API，也不要求运行原版 TradingAgents Python。

## Optional Research Tooling

外围工具统一位于：

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
7. 当前市场环境会显著影响交易计划时读取 `references/market-regime.md`；Regime 使用的每个信号必须登记独立 `signal_as_of`，新鲜度未通过则输出 `insufficient`。
8. 专业金融任务按需读取 `references/anthropic-financial-services.md`；只有本次真实可访问时才能声称实际运行。
9. 大股票池筛选、规则回测或历史校准时，才读取对应 references 并路由 `extensions/research_tooling/`。
10. 对短线/价位问题必须读取 `references/evidence-confidence.md` 与 `references/four-layer-trading-framework.md`，执行 Price/Session Guard 与 Tactical R/R Gate。
11. 所有外部/外围结果必须回到 CIS 最终质量门。

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
tactical  → technical + risk_resilience + price_context check + catalyst_event_review check
earnings  → fundamentals + catalyst_macro + risk_resilience
```

对 tactical，`price_context` 和 `catalyst_event_review` 是**完成检查**的布尔门，不要求催化剂一定为正；`checked_no_catalyst` 可在研究文本中作为合法结果，但检查本身必须完成。关键维度或必需检查缺失，即使 coverage >=85%，仍只能 provisional。

## Tactical Hardening

### Price / Session Guard

短线涉及“当前价”时必须登记：

```text
analysis_timestamp
quote_timestamp
market_session: premarket | regular | afterhours | closed
price_type: premarket | live | afterhours | last_close
current_price
```

`last_close` 只能作为最近收盘参考，不能冒充实时价格。确定性校验器：`scripts/tactical_setup_gate.py`。

### Tactical R/R Gate

短线交易计划至少包含：

```text
Entry Zone
Chase Limit（如适用）
Stop / Invalidation
Target 1
Target 2（如适用）
Reward / Risk
```

按 Entry Zone 中最差 Target 1 R/R 的 baseline：`<1 reject`、`1–<1.5 weak_setup`、`1.5–<2 acceptable`、`>=2 attractive`。越过 Chase Limit → `blocked_do_not_chase`。这些阈值是纪律基线，不是已校准最优参数。

## Evidence Freshness

短线价格、成交量、技术指标和催化剂必须有明确数据截止时间。Price/Volume 应来自当前可验证 session 或明确标记的最近正式收盘；Technical 必须与价格数据截止时间一致；Breaking News/Catalyst 必须检查当前最新公开信息。新鲜度不明时 Evidence Audit 不得 `pass`。

## Market Regime

Regime 只用于环境修正，不直接机械买卖。输出：

```text
risk_on | neutral | risk_off | insufficient
```

每个已使用信号必须有独立 `signal_as_of`；缺失、未来日期或超出 baseline 新鲜度容忍范围时，Regime 必须降级为 `insufficient` 或拒绝输入。

## 标准输入

```text
research_type: company | stock | ETF | portfolio | industry | macro | earnings | screening | backtest
subject: 标的或股票池
research_question: 本次问题
mode: quick | standard | deep | holding_review
analysis_date/as_of: 数据截止时间
analysis_timestamp: 短线/价位任务使用带时区时间戳
horizon: 短期 | 1-3年 | 3-10年
decision_context: generic | long_term | tactical | earnings
portfolio_context: 持仓、权重、成本、基准、约束、资金需求
```

默认 `standard`；真实持仓增减/退出使用 `holding_review`。

## 执行顺序

1. Intake：对象、问题、模式、期限、`as_of`、decision_context。
2. Runtime Guard：核验当前 CIS；按 7 天 TTL 决定是否检查 TradingAgents 上游。
3. Evidence：采集并登记事实、计算、假设、来源、新鲜度和限制。
4. Core Research：执行 ChatGPT-native TradingAgents Methodology。
5. Professional Skills：按需 Anthropic。
6. Audit/Risk：两者均必须明确 pass 才能放行决策级。
7. Critical Dimensions / Context Checks：按任务检查关键维度；tactical 还需 Price Context 与 Catalyst/Event Review 完成。
8. Score：按 `scoring-engine.md`。
9. Regime：当前环境会改变交易计划时执行。
10. Trade Framework：涉及买卖/价位时执行趋势 → 价格 → 成交 → 风险；短线再执行 Tactical R/R Gate。
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

`coverage < 70%` 不输出单一总分；`70% <= coverage < 85%` 为 provisional；`coverage >= 85%` 也必须通过 Audit/Risk/Critical Dimensions/Context Checks 才可 decision_grade。
