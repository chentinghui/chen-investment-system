# CIS 0.4.5 系统流程

## 0. Runtime Guard

1. 读取当前 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，核验 `chentinghui/chen-investment-system` 当前 `main`。
3. 读取 `tradingagents-methodology.md` 作为股票默认研究方法。
4. 读取 `runtime/tradingagents/upstream-status.json`。TradingAgents 7 天 TTL 未到时使用稳定基线；到期后的下一次股票研究轻量检查上游 `main` SHA。新 SHA 标记 `review_required`，未经审查不得采用。
5. 原版 TradingAgents 仅在用户明确要求运行/测试时启动；执行成功不等于研究质量通过。Secret-backed 远程运行要求当前 upstream SHA 已审查，第三方执行 Job 不拥有仓库写权限。
6. 专业金融子问题按需路由 Anthropic Financial Services。
7. Quant / Baseline Backtest / Prediction / Evaluation 不属于日常单股 Core，只有对应任务才从 `extensions/research_tooling/` 调用。
8. 当前 CIS 不接入独立外部交易/回测引擎。超出 Python baseline evaluator 的策略执行仿真能力必须明确披露。

## 1. Intake

识别对象、问题、市场、模式、期限、`analysis_date/as_of`、基准和真实持仓资料，并确定 `decision_context`：`generic | long_term | tactical | earnings`。

短线/具体价位任务额外登记：

```text
analysis_timestamp
quote_timestamp
exchange: XNAS | XNYS
market_session（由时间戳的 US-equity session baseline 校验）
price_type
current_price
quote_max_age_seconds（活跃时段）
quote_session_date（closed / last_close）
```

若任务是回测/规则验证，还要登记：

```text
strategy_or_rule
backtest_engine: baseline_python | other_explicit_runtime
backtest_period
benchmark
key_parameters
fee_slippage_assumptions
out_of_sample_period
```

如果所需执行语义无法由当前 runtime 正确表达，停止并披露能力边界。

## 2. Evidence

登记来源等级、发布日期、资料期间、提取日期、事实、限制和冲突。历史任务必须防前视偏差。

短线任务执行 Evidence Freshness Guard：价格/成交/技术必须有明确数据截止时间，Breaking News / Catalyst 必须检查当前最新公开信息；新鲜度不清楚时 Evidence Audit 不得 `pass`。活跃时段 stale quote、分析 session 与 quote observation session 冲突、错误 last-close session 均不能通过 Price Context。

回测任务必须同时登记数据口径、时间覆盖、股票池构造和执行假设。程序运行成功不能替代 point-in-time、survivorship、universe drift、费用/滑点和样本外检查。

## 3. Core Research

由当前 ChatGPT 会话直接执行 `tradingagents-methodology.md`：

```text
Market + Fundamentals + News (+ Sentiment)
  ↓
Bull / Bear 独立反证
  ↓
Research Manager
  ↓
Trader / Risk / Portfolio（按需）
  ↓
methodology_candidate
```

Research Manager 不得创造新事实；Bull/Bear/Risk 必须尽量保持证据和机制独立。

## 4. 专业金融子问题

DCF / Comps / 三表 / 模型审计 / Earnings / Competitive / Thesis / Catalyst 等按需路由 Anthropic Financial Services，并回灌同一证据登记。

## 5. Evidence Audit + Risk Gate

Evidence 与 Risk 都采用 fail-closed：未明确 `pass` 就不能进入 `decision_grade`。

```text
audit_status = unverified | pass | unresolved | fail
risk_status  = unverified | pass | unresolved | fail
risk_override = none | block
```

Agent 层不再使用 `conditional` / `caution` 作为机器枚举。

## 6. Critical Dimension Gate + CIS 八维评分

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience + price_context check + catalyst_event_review check
earnings  → fundamentals + catalyst_macro + risk_resilience
```

`tactical` 的额外检查只要求“检查已完成”，不要求一定存在正面催化剂。

- coverage < 70%：insufficient；
- 70%–<85%：provisional；
- >=85% + Audit pass + Risk pass + Critical Dimensions/Context Checks 完整：才可 decision_grade。

CIS Research Grade 与 Tactical Setup Readiness 分开报告。

## 7. Market Regime（按需）

当前市场环境会改变交易计划时，输出 `risk_on / neutral / risk_off / insufficient`。Regime 不直接机械触发买卖。

必须显式选择 `regime_profile`：`us_broad_v1`（SPY + S&P500 breadth）或 `us_nasdaq_v1`（QQQ + Nasdaq-100 breadth）。每个信号登记独立 `signal_as_of`。missing/stale 信号先排除，再按 fresh coverage 判断是否仍能分类；未来日期直接拒绝。

## 8. 四层交易框架 + Tactical R/R Gate

涉及买卖、持仓、止盈止损或具体价位时执行：趋势 → 价格 → 成交 → 风险。卖出必须同时覆盖盈利止盈与防守止损。

对 `decision_context=tactical` 或明确短线做差价的买入问题，再执行 `scripts/tactical_setup_gate.py`：

```text
US-equity Price/Session Baseline
Quote Freshness + quote observation session
Entry Zone
Chase Limit
Stop / Invalidation + Stop Type（必填）
Target 1 / Target 2
Reward / Risk
Setup Lifecycle
```

Quality Score 高不代表当前价格可追。越过 Chase Limit → `blocked_do_not_chase`；未进入 Entry Zone → `wait_for_entry`；Stop 已确认失效 → `invalidated_reprice_required`；Target 1 已实现/越过 → `setup_expired_reprice_required`；确认型 Stop 尚未确认 → `blocked_pending_stop_confirmation`。

对确认型 Stop，`stop_confirmation_met=true` 是持久状态：即使价格随后反弹，也不能复活旧 setup，必须重新定计划。

## 9. ETF / QDII / Portfolio Gate

跨境 ETF/QDII 执行产品身份、基准、IOPV、溢价、申赎、时差和流动性纪律。历史溢价 `ready` 至少要求 20 个**唯一日期**的有效观察，JSON boolean 不能作为价格/IOPV 数字。组合动作只有在真实持仓、权重、成本、基准、约束和资金需求足够时才给精确比例。

## 10. Synthesis

输出最终中文分析结论、评分 coverage、关键维度/上下文检查状态、为什么不是更高/更低分、价位/风险条件、关键证伪条件和复盘触发点。

短线结论必须区分：

```text
CIS Research Grade / 公司质量
vs
Tactical Setup Readiness / 当前交易计划状态
```

避免把“好公司”直接等同于“现在值得买”。

## 11. Quant / Backtest / Evaluation 路径

只有对应任务才调用；它们不是默认单股研究链。

### 11.1 Quant Screening

```text
extensions/research_tooling/quant_factor_engine.py
```

- 大股票池/Top N 才运行；
- ticker 唯一、同一 as_of；
- 因子需最小横截面观测；
- 只负责候选排序，候选仍要回到 CIS Core 深研。

### 11.2 Baseline Cross-sectional Backtest

当前仓库内回测能力：

```text
extensions/research_tooling/backtest_factor_strategy.py
```

仅用于 `date,ticker,score,forward_return` 的轻量横截面 sanity check。同一 `(date,ticker)` 必须唯一。必须检查样本外、前视/幸存者偏差、成本和参数稳健性。

它不是完整事件驱动策略引擎；若用户的任务需要其未实现的订单/执行语义，必须明确报告能力不足。

### 11.3 Prediction / Evaluation

只有用户明确要求记录/复盘/校准时调用 Prediction / Evaluation 工具；公共 Ledger 使用 allowlist。Evaluation 的 5D/20D/60D 相关性按 horizon 分开，样本门槛优先用 unique `research_id`。Settlement 当前采用 next-session adjusted-close → target-session adjusted-close 研究指标，不能称为真实 next-open 交易 P&L；缺少终值保持 unresolved。

Extension 故障不得阻塞 CIS Core，也不得自动修改生产规则。

## 12. 原版 TradingAgents 测试路径

只有用户明确要求时，才按 `tradingagents.md` 运行本地/远程原版程序。远程执行固定本次 upstream SHA；secret-backed 运行先确认该 SHA 已审查。结果仍只是 `external_decision_candidate`。

必须区分：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```
