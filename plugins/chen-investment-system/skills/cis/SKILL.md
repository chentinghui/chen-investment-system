---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。股票/上市公司/ETF分析、估值、买卖、持仓、财报、风险、目标价、买入价、卖出价和跨标的比较默认进入 CIS。日常单股研究由 CIS Core 完成；Quant、QuantConnect LEAN Backtest、Prediction/Evaluation 仅作为按需外围/外部能力，不属于默认分析链。
---

# 陈氏投资系统（CIS）0.4.5

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
CIS Score / Research Grade
  ↓
Market Regime（按交易问题需要）
  ↓
US-equity Price/Session Baseline + Quote Freshness + Tactical R/R Gate（短线按需）
  ↓
Trade / ETF / Portfolio Gate
  ↓
最终中文分析结论
```

日常研究不要求外部 LLM API，也不要求运行原版 TradingAgents Python，更不要求运行 QuantConnect LEAN。

## External Quant Validation + Optional Research Tooling

策略级量化验证使用外部 QuantConnect LEAN：

```text
integrations/lean/
```

- **LEAN**：仅在可执行交易策略、技术规则、仓位规则或期权/ETF/股票策略需要历史验证时按需调用；
- LEAN 是外部量化验证引擎，不属于 CIS Core，不 vendor 源码，不启用默认 live trading；
- LEAN 结果没有最终动作权，必须经过 `references/backtest-validation.md`。

仓库内外围工具统一位于：

```text
extensions/research_tooling/
```

- Quant：仅大股票池/Top N/系统筛选时按需调用；
- Baseline Backtest：仅 `date,ticker,score,forward_return` 横截面因子/Top-N sanity check；
- Prediction / Evaluation：仅用户明确要求记录、复盘或校准时调用；
- External/外围工具故障不得阻塞日常单股分析；
- 外部/外围工具没有最终动作权，也不得自动改写生产评分规则。

## 自动触发规则

以下投资决策问题默认进入 CIS：

- `分析 MU`、`看看 NVDA`、`MU 能买吗`、`QQQ 还能持有吗`；
- 合理买入价、目标价、止盈、止损、估值、上涨空间、风险、财报影响；
- 持仓复盘、加减仓、退出；
- 多股票/ETF比较；
- 大股票池 Top N 任务仍由 CIS 受理，但按需路由 Optional Quant；
- 明确要求“历史回测/验证策略是否有效”仍由 CIS 受理，但策略级验证优先路由外部 QuantConnect LEAN。

纯事实问题如公司全称、代码、交易时间、上市地点，不强制运行完整 CIS。

## Runtime Guard

1. 读取当前 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 当前 `main`，不得凭聊天记忆恢复旧规则。
3. 股票任务读取 `references/tradingagents-methodology.md`，默认由当前 ChatGPT 会话执行多角色研究逻辑。
4. **TradingAgents 7 天 TTL**：读取 `runtime/tradingagents/upstream-status.json`。TTL 未到不访问上游；达到或超过 7 天后，由下一次股票研究执行 `scripts/check_tradingagents_upstream.py` 的同等逻辑轻量检查当前 `main` SHA。新 SHA 标记 `review_required`，未经审查不得进入 CIS 稳定方法论。上游不可访问不阻塞正常研究。
5. 只有用户明确要求运行/测试原版 TradingAgents 时，才启动 `references/tradingagents.md` 的本地/远程路径。**远程 secret-backed 运行只允许执行 `reviewed_sha` 对应的当前上游；若当前 `main` 已变化，先阻断并要求审查。零密钥 Ollama smoke test 可用于检查未审查最新代码的可执行性。**
6. 原版 TradingAgents 的 `execution_status=success` / `runtime_readiness=remote_ready` 只表示程序完成；`research_quality` 未审查时不能直接作为最终结论。
7. 当前市场环境会显著影响交易计划时读取 `references/market-regime.md`；必须选择 `regime_profile`，missing/stale 信号先排除，再按 fresh coverage 判断是否能分类。
8. 专业金融任务按需读取 `references/anthropic-financial-services.md`；只有本次真实可访问时才能声称实际运行。
9. 大股票池筛选或历史校准时，才读取对应 references 并路由 `extensions/research_tooling/`。**策略级规则回测**读取 `references/quantconnect-lean.md` + `references/backtest-validation.md` 并路由 `integrations/lean/cis_lean_adapter.py`；仅横截面因子 sanity check 才使用 baseline `backtest_factor_strategy.py`。
10. 对短线/价位问题必须读取 `references/evidence-confidence.md` 与 `references/four-layer-trading-framework.md`，执行 Price/Session Guard、Quote Freshness Guard 与 Tactical R/R Gate。
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
- `references/quantconnect-lean.md`（仅策略级量化验证/LEAN回测）
- `references/backtest-validation.md`（仅规则/策略验证）
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

不使用定时 GitHub Actions 监控；不允许未经审查的上游变化自动覆盖 CIS。原版远程 Runner 将“执行第三方代码”和“写回仓库”拆成不同 Job：第三方执行 Job 只有 `contents: read`；结果通过 Artifact 交给不持有 LLM Secret 的 trusted publisher 写回。Cloud/secret-backed 运行还必须先确认当前上游 SHA 等于 `reviewed_sha`。

### Anthropic Financial Services

DCF / Comps / Earnings / 三表 / 模型审计 / Competitive / Thesis / Catalyst 等专业子问题按需优先读取上游 `main` 对应 Skill。只有本次真实读取/执行后才能标记已使用，输出仍需回到 CIS Evidence/Risk/Score。

### QuantConnect LEAN

```text
普通单股研究 → 不运行 LEAN
策略级回测 → readiness → lean backtest → result JSON → Backtest Validation
横截面因子 sanity check → baseline evaluator
```

LEAN 独立安装和升级，CIS 不复制上游源码。只有本次真实 `execution_status=success` 且解析到可识别 statistics JSON，才能说“已运行 LEAN 回测”。`runtime_readiness=ready` 只表示 Lean CLI / Docker 基础环境可用，不代表账户、数据或项目已经可运行。

LEAN 回测输出固定视为：

```text
engine_role = external_quant_validation
decision_authority = none
research_quality = unreviewed
```

通过样本外、偏差、费用/滑点、执行真实性与稳健性审查前，不得升级生产规则。当前 CIS 不启用 LEAN live trading / Broker 自动执行。

## Fail-Closed Evidence / Risk + Critical Dimension Gate

评分引擎默认：

```text
audit_status = unverified
risk_status  = unverified
```

机器接口统一枚举：

```text
audit_status = unverified | pass | fail | unresolved
risk_status  = unverified | pass | fail | unresolved
risk_override = none | block
```

Evidence Auditor 不再返回 `conditional`，Risk Manager 不再返回 `caution` 作为机器枚举；需要谨慎/补证时使用 `unresolved` 并写明原因。只有明确 `pass` 才可进入 `decision_grade`。

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience + price_context check + catalyst_event_review check
earnings  → fundamentals + catalyst_macro + risk_resilience
```

对 tactical，`price_context` 和 `catalyst_event_review` 是**完成检查**的布尔门，不要求催化剂一定为正；`checked_no_catalyst` 可在研究文本中作为合法结果，但检查本身必须完成。关键维度或必需检查缺失，即使 coverage >=85%，仍只能 provisional。

**CIS Research Grade 与 Tactical Setup Readiness 必须分开。** `decision_grade` 不等于“现在可以买”；Tactical Setup 也不能用来补齐缺失的长期/通用研究 coverage。

## Tactical Hardening

### Price / Session Guard

短线涉及“当前价”时必须登记：

```text
analysis_timestamp
quote_timestamp
exchange: XNAS | XNYS
market_session: premarket | regular | afterhours | closed
price_type: premarket | live | afterhours | last_close
current_price
quote_max_age_seconds（活跃时段）
quote_session_date（closed / last_close）
```

当前实现是 **US-equity common session baseline**，不是每个交易场所的官方实时日历。`market_session` 由 `scripts/tactical_setup_gate.py` 根据时间戳的美东交易日历/时段基线推导；调用者提供的值只能用于交叉校验，不能覆盖推导结果。周末/主要休市日不得伪装成 `regular`。

活跃时段 quote 必须通过 freshness gate，且 `quote_timestamp` 本身必须落在与分析一致的 session：盘前报价不能包装成 regular `live`，regular 报价也不能包装成 afterhours。`last_close` 只能作为最近收盘参考，且必须引用最近已完成交易日。特殊临时休市仍需 Evidence Layer 额外核验。

### Tactical R/R Gate

短线交易计划至少包含：

```text
Entry Zone
Chase Limit（如适用）
Stop / Invalidation
Stop Type（必填）
Target 1
Target 2（如适用）
Reward / Risk
```

按 Entry Zone 中最差 Target 1 R/R 的 baseline：`<1 reject`、`1–<1.5 weak_setup`、`1.5–<2 acceptable`、`>=2 attractive`。这些阈值是纪律基线，不是已校准最优参数。

`stop_type`：

```text
hard_price | close_confirmation | technical_invalidation
```

非 `hard_price` 必须明确 `stop_confirmation_met=true/false`。`stop_confirmation_met=true` 表示旧 setup 已确认失效，即使价格随后反弹回 Stop 上方/下方也不能“复活”；必须重新定 Entry/Stop/Target。

Setup 生命周期：

```text
Stop 已确认失效       → invalidated_reprice_required
Target 1 已达到/越过  → setup_expired_reprice_required
Stop 穿越但未确认     → blocked_pending_stop_confirmation
超过 Chase Limit      → blocked_do_not_chase
未进入 Entry Zone     → wait_for_entry
```

旧交易计划失效后必须重新定 Entry/Stop/Target，不能继续沿用。

## Evidence Freshness

短线价格、成交量、技术指标和催化剂必须有明确数据截止时间。Price/Volume 应来自当前可验证 session 或明确标记的最近正式收盘；Technical 必须与价格数据截止时间一致；Breaking News/Catalyst 必须检查当前最新公开信息。新鲜度不明时 Evidence Audit 不得 `pass`。

## Market Regime

Regime 只用于环境修正，不直接机械买卖。必须选择：

```text
us_broad_v1  → SPY + S&P500 breadth
us_nasdaq_v1 → QQQ + Nasdaq-100 breadth
```

统一 `sma50_slope_pct` 与 `realized_vol_20d` 计算定义见 `references/market-regime.md`。missing/stale 信号先排除；fresh coverage >=60% 且 fresh signals >=3 才允许输出正式 experimental baseline。未来日期直接拒绝。

## Optional Evaluation 安全边界

Prediction/Evaluation 仍是外围 experimental：

- 公共 Ledger 使用结构化 allowlist，任意 `notes/account/shares/cost_basis` 等非白名单字段直接拒绝；
- 5D/20D/60D 是同一 research 的相关结果，不得当成三个独立样本；相关性按 horizon 分开计算；
- 自动 settlement 当前是 next-session **adjusted-close to adjusted-close** 研究指标，不冒充 next-open 真实成交收益；缺少可审计终值时保持 unresolved。

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
