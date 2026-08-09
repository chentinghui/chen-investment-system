# CIS 0.4.3 系统流程

## 0. Runtime Guard

1. 读取当前 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，核验 `chentinghui/chen-investment-system` 当前 `main`。
3. 读取 `tradingagents-methodology.md` 作为股票默认研究方法。
4. 读取 `runtime/tradingagents/upstream-status.json`。TradingAgents 7 天 TTL 未到时使用稳定基线；到期后的下一次股票研究轻量检查上游 `main` SHA。新 SHA 标记 `review_required`，未经审查不得采用。
5. 原版 TradingAgents 仅在用户明确要求运行/测试时启动；执行成功不等于研究质量通过。
6. 专业金融子问题按需路由 Anthropic Financial Services。
7. Quant / Backtest / Prediction / Evaluation 不属于日常单股 Core，只有对应任务才从 `extensions/research_tooling/` 调用。

## 1. Intake

识别对象、问题、市场、模式、期限、`analysis_date/as_of`、基准和真实持仓资料，并确定 `decision_context`：`generic | long_term | tactical | earnings`。

短线/具体价位任务额外登记：

```text
analysis_timestamp
quote_timestamp
market_session
price_type
current_price
```

## 2. Evidence

登记来源等级、发布日期、资料期间、提取日期、事实、限制和冲突。历史任务必须防前视偏差。

短线任务执行 Evidence Freshness Guard：价格/成交/技术必须有明确数据截止时间，Breaking News / Catalyst 必须检查当前最新公开信息；新鲜度不清楚时 Evidence Audit 不得 `pass`。

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

## 7. Market Regime（按需）

当前市场环境会改变交易计划时，输出 `risk_on / neutral / risk_off / insufficient`。Regime 不直接机械触发买卖。

每个已使用 Regime 信号必须登记独立 `signal_as_of`。缺失日期、未来日期或超过 baseline 新鲜度容忍范围时，Regime 降级为 `insufficient` 或拒绝输入。

## 8. 四层交易框架 + Tactical R/R Gate

涉及买卖、持仓、止盈止损或具体价位时执行：趋势 → 价格 → 成交 → 风险。卖出必须同时覆盖盈利止盈与防守止损。

对 `decision_context=tactical` 或明确短线做差价的买入问题，再执行 `scripts/tactical_setup_gate.py`：

```text
Price/Session Guard
Entry Zone
Chase Limit
Stop / Invalidation
Target 1 / Target 2
Reward / Risk
```

Quality Score 高不代表当前价格可追。越过 Chase Limit 时输出 `blocked_do_not_chase`；未进入 Entry Zone 时输出 `wait_for_entry`。

## 9. ETF / QDII / Portfolio Gate

跨境 ETF/QDII 执行产品身份、基准、IOPV、溢价、申赎、时差和流动性纪律。组合动作只有在真实持仓、权重、成本、基准、约束和资金需求足够时才给精确比例。

## 10. Synthesis

输出最终中文分析结论、评分 coverage、关键维度/上下文检查状态、为什么不是更高/更低分、价位/风险条件、关键证伪条件和复盘触发点。

短线结论必须区分：

```text
公司质量/研究姿态
vs
当前 Tactical Setup 状态
```

避免把“好公司”直接等同于“现在值得买”。

## 11. Optional Research Tooling

只有对应任务才调用：

```text
extensions/research_tooling/
```

- 大股票池/Top N → `quant_factor_engine.py`；
- 新规则/因子/阈值验证 → `backtest_factor_strategy.py`；
- 用户明确要求记录/复盘/校准 → Prediction / Evaluation 工具。

这些外围工具不属于默认单股分析链，故障不得阻塞 CIS Core，也不得自动修改生产规则。可选 Prediction/Evaluation 的默认观察周期调整为短线导向的 5/20/60 交易日；仍保持 experimental，不作为 CIS Core 的必要条件。

## 12. 原版 TradingAgents 测试路径

只有用户明确要求时，才按 `tradingagents.md` 运行本地/远程原版程序。远程每次拉取上游当前 `main`，结果仍只是 `external_decision_candidate`。

必须区分：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```
