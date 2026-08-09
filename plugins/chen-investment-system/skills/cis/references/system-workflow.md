# CIS 0.4.5 系统流程（Control Plane v2）

## 0. Runtime Guard + Route Guard

1. 读取当前 `SKILL.md`、`references/external-engine-registry.json` 与必读 references。
2. 若可访问 GitHub，核验 `chentinghui/chen-investment-system` 当前 `main`；不得凭聊天记忆恢复旧规则。
3. 将用户请求标准化为：

```text
asset_type
intent
mode = fast | standard | deep
analysis_date/as_of
horizon
decision_context
portfolio_context（按需）
```

4. 使用 `scripts/route_cis.py` 生成**最少充分路由**。路由器只决定应该由谁负责，不证明外部 runtime 本次真的可用或已经执行。
5. 外部模块必须分别判断：`available / executed / evidence_quality / accepted_by_cis`，禁止把“项目存在”写成“本次已运行”。
6. TradingAgents 保留 7 天 TTL 与 `reviewed_sha` 安全策略；原版 runtime 只有明确运行/测试时才执行。
7. 所有外部结果最后必须回到 CIS Evidence / Risk / Critical / Score / asset-specific gates。

## 1. Intake

识别对象、问题、市场、资产类型、intent、模式、期限、`analysis_date/as_of`、基准和真实持仓资料。

支持的核心 intent：

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

短线/具体价位任务额外登记：

```text
analysis_timestamp
quote_timestamp
exchange: XNAS | XNYS
market_session（由 US-equity common session baseline 校验）
price_type
current_price
quote_max_age_seconds
quote_session_date
```

策略验证额外登记：

```text
strategy_or_rule
backtest_period
benchmark
key_parameters
fee_slippage_assumptions
out_of_sample_period
```

## 2. Data / Evidence Acquisition

默认数据优先级：

```text
primary source
→ OpenBB / direct provider
→ other public sources
```

OpenBB 的职责是数据聚合与标准化，不拥有最终事实覆盖权。重大冲突必须回到 SEC、公司公告、交易所、监管披露或其他 primary source。

每个关键证据登记：来源、provider、发布日期、资料期间、提取时间、`as_of`、currency/unit、事实、限制与冲突。历史任务必须防 look-ahead、restatement leakage、survivorship 和 universe drift。

## 3. General Research — TradingAgents

普通股票/上市公司研究默认由 TradingAgents 方法论承担：

```text
Market + Fundamentals + News (+ Sentiment)
  ↓
Bull / Bear 独立反证
  ↓
Research Manager
  ↓
Trader / Risk / Portfolio（按需）
  ↓
research_candidate
```

日常研究可以使用已审查的 ChatGPT-native TradingAgents Methodology，不要求每次启动原版 Python runtime。

Research Manager 不得创造新事实；Bull/Bear/Risk 必须尽量保持证据与机制独立。原版 runtime 的 BUY/SELL/HOLD 只是 `external_decision_candidate`。

## 4. Specialist Modeling — FinRobot / Anthropic

### 4.1 FinRobot

需要确定性金融模型时优先路由 FinRobot：

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

原则：**数字由确定性计算产生，LLM 负责解释与综合。** 关键假设和数值 provenance 必须保留。

若模型之间冲突，比较 WACC、growth、terminal value、margin、capex、dilution、peer set、会计口径，不机械平均目标价。

### 4.2 Anthropic Financial Services

作为专业方法增强或 deep second opinion，用于模型审计、Earnings、Competitive、Thesis、Catalyst 等。只有本次环境真实可访问相关 Skill 时才能声称已使用。

FinRobot 已经完成同质确定性模型时，不无理由再让 Anthropic/LLM 重算同一模型。

## 5. Quant Research — Microsoft Qlib

Qlib 是 CIS 的专业 AI Quant / ML 研究层：

```text
factor research
ML signal/model
quant screening
portfolio optimization
research backtest/model evaluation
```

Qlib 研究必须保持 point-in-time 数据、train/validation/OOS 分离、成本意识和稳健性检查。

`extensions/research_tooling/quant_factor_engine.py` 只是 Qlib 不可用时的有限 fallback / sanity check，不得声称等价于 Qlib。

## 6. Autonomous Quant R&D — Microsoft RD-Agent

只有 `factor_discovery` 或明确的新因子/新模型研发任务才调用 RD-Agent。

固定升级链：

```text
RD-Agent proposes / implements
        ↓
Qlib independent research evaluation
        ↓
QuantConnect LEAN execution-realistic validation
        ↓
CIS Backtest Validation
        ↓
manual / policy review
        ↓
production rule
```

RD-Agent 输出默认是 `experimental_research_candidate`，任何新因子、新阈值、新模型都不能自动写入生产 CIS Score 或交易规则。

## 7. Strategy Validation — QuantConnect LEAN

需要验证可执行策略、技术规则、仓位规则、期权/ETF/股票策略，或必须观察订单/费用/滑点/持仓路径时，使用：

```text
references/quantconnect-lean.md
references/backtest-validation.md
        ↓
integrations/lean/cis_lean_adapter.py
        ↓
External QuantConnect LEAN
```

只有本次 `execution_status=success` 且解析到可识别 statistics JSON，才能称为“已运行 LEAN”。

固定输出语义：

```text
engine_role = external_quant_validation
decision_authority = none
research_quality = unreviewed
```

用户明确要求 LEAN 时，如果 LEAN unavailable/error，必须如实报告，不能用 baseline evaluator 冒充。

LEAN 成功也必须继续审查样本外、look-ahead、survivorship、费用/滑点、参数稳健性和执行真实性。当前 CIS 不启用 LEAN live trading / Broker 自动执行。

## 8. Conflict Reconciliation

总控不使用多数票。

### 事实冲突

```text
primary source
→ freshness/as_of
→ provider coverage
→ accounting/unit/currency consistency
```

### 估值冲突

逐项拆解输入与假设，禁止简单平均 target price。

### Quant vs Fundamentals

先区分预测期限、目标变量和核心假设。短期量化信号与长期基本面可以同时成立，最终在各自时间尺度表达。

### Qlib vs LEAN

- 因子/ML研究有效性 → 审查 Qlib 实验设计；
- 订单、费用、滑点、持仓路径 → LEAN 执行验证优先；
- 二者都不能绕过 CIS Evidence/Risk Gate。

关键冲突无法解决时必须保留冲突并降低 confidence/readiness。

## 9. Evidence Audit + Risk Gate

Evidence 与 Risk 都 fail closed：未明确 `pass` 就不能进入 `decision_grade`。

```text
audit_status = unverified | pass | fail | unresolved
risk_status  = unverified | pass | fail | unresolved
risk_override = none | block
```

Agent 层不使用 `conditional` / `caution` 作为机器枚举。

## 10. Critical Dimension Gate + CIS 八维评分

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience + price_context check + catalyst_event_review check
earnings  → fundamentals + catalyst_macro + risk_resilience
```

- coverage < 70% → insufficient；
- 70%–<85% → provisional；
- >=85% + Audit pass + Risk pass + 关键维度完整 → 才可 decision_grade。

CIS Research Grade 与 Tactical Setup Readiness 必须分开。

## 11. Market Regime（按需）

当前市场环境会改变交易计划时，输出 `risk_on / neutral / risk_off / insufficient`。Regime 只修正安全边际、节奏和仓位倾向，不直接机械触发买卖。

必须显式选择 `regime_profile`：

```text
us_broad_v1  → SPY + S&P500 breadth
us_nasdaq_v1 → QQQ + Nasdaq-100 breadth
```

missing/stale 信号先排除；未来日期直接拒绝。

## 12. Tactical Trading Gate

涉及买卖、止盈止损、追不追、明确买入价/目标价时执行：趋势 → 价格 → 成交 → 风险。

短线任务运行 `scripts/tactical_setup_gate.py`：

```text
US-equity Price/Session Baseline
Quote Freshness + quote observation session
Entry Zone
Chase Limit
Stop / Invalidation + Stop Type
Target 1 / Target 2
Reward / Risk
Setup Lifecycle
```

当前实现基于 **US-equity common session baseline**。必须登记 `quote_timestamp`。

对确认型 Stop，`stop_confirmation_met=true` 表示旧 setup 已持久失效，即使价格随后反弹，也不能复活旧计划。

可能状态包括：

```text
blocked_do_not_chase
wait_for_entry
invalidated_reprice_required
setup_expired_reprice_required
blocked_pending_stop_confirmation
```

## 13. ETF / QDII / Portfolio Gate

### ETF / QDII

外部项目不能覆盖 CIS 自有产品纪律：产品身份、基准、NAV/IOPV、溢价、申赎、时差、流动性。

### Portfolio

只有真实持仓、权重、成本、基准、约束和资金需求完整时，才给精确仓位或再平衡比例。Qlib portfolio optimization 只是研究输入。

## 14. Optional Research Tooling

位于：

```text
extensions/research_tooling/
```

定位：

- local Quant → Qlib 不可用时的有限 fallback / CI sanity；
- Baseline Backtest → `date,ticker,score,forward_return` 横截面 sanity check；
- Prediction / Evaluation → 用户明确要求记录、复盘或校准时使用。

公共 Prediction Ledger 使用结构化 `allowlist`。5D/20D/60D 是同一 research 的相关结果，**不得当成三个独立样本**；相关性按 horizon 分开。

Optional Research Tooling 不自动修改生产规则，也不能冒充 Qlib 或 LEAN。

## 15. TradingAgents Runtime Safety

保留 `check_tradingagents_upstream.py` 的 7 天 TTL。

```text
TTL 未到 → 使用稳定已审查基线
TTL 到期 → 下一次股票研究轻量检查 main SHA
SHA 变化 → review_required
```

Secret-backed remote run 只允许当前 upstream SHA 等于 `reviewed_sha`。第三方代码执行 Job 不拥有仓库写权限。

## 16. Fail-Closed Fallback

```text
OpenBB unavailable       → primary/direct/public source
TradingAgents runtime    → reviewed ChatGPT-native methodology
FinRobot unavailable     → Anthropic 或透明 CIS calculation
Qlib unavailable         → local Quant limited fallback
RD-Agent unavailable     → 明确 R&D stage 未运行
LEAN unavailable         → 显式 LEAN 请求报告 unavailable/error
Anthropic unavailable    → 跳过增强
```

任何 fallback 都必须说明实际使用了什么；不能虚构“已运行某外部项目”。

## 17. Synthesis

最终输出至少说明：

- 本次 intent / horizon / `as_of`；
- 实际调用/未调用的关键模块及原因；
- 关键证据和冲突；
- Evidence/Risk/Critical Gate 状态；
- CIS Research Grade / Score / coverage；
- 若涉及交易：Tactical Setup Readiness、Entry/Stop/Target/RR；
- 若涉及 ETF/组合：对应 Gate 状态；
- 为什么不是更高/更低分；
- 证伪条件和复盘触发点。

最终发布权始终属于 CIS Control Layer。
