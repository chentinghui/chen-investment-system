# CIS 0.4.5 模块路由

## 总原则

CIS 是唯一用户入口和最终质量控制层，但**不是所有工具都属于 Core**。

- 单股票/上市公司研究：默认只走 CIS Core；
- 短线/具体买点：Core 内追加 US-equity Price/Session + Quote Freshness + Tactical R/R Gate；
- 大股票池筛选：按需调用 `extensions/research_tooling/quant_factor_engine.py`；
- 专业估值/财报/模型：按需调用 Anthropic Financial Services；
- 当前市场环境显著影响交易计划：加 Market Regime；
- 横截面因子/Top-N 历史验证：按需调用 `backtest_factor_strategy.py`；
- 需要当前 evaluator 未实现的完整事件驱动/复杂执行回测：明确报告能力不足，不静默替代；
- 用户明确要求历史记录/复盘/校准：按需调用 Prediction/Evaluation Extension；
- 原版 TradingAgents Python：仅用户明确要求运行/测试时调用。

## 默认路由

| 用户意图 | 默认核心 | 可选增强 | CIS 最终校验 |
|---|---|---|---|
| 一般股票研究 | ChatGPT-native TradingAgents Methodology | Anthropic（按需） | Evidence + Risk + Critical Dimensions + Score |
| 基本面+技术+新闻综合 | ChatGPT-native Methodology | — | Evidence + Score |
| 多空观点 | Bull/Bear 独立反证 | Research Manager | 冲突保留与裁决 |
| 价值区间/DCF/Comps | ChatGPT-native 上下文 | Anthropic DCF/Comps | valuation + Evidence |
| 财报前后 | ChatGPT-native News/Fundamentals | Anthropic Earnings | catalyst/valuation 更新 |
| 短线买入/做差价 | ChatGPT-native Methodology + Session/Freshness + Tactical R/R | Regime（按需） | Tactical Context Checks + 四层交易 |
| 买入/卖出/持有 | ChatGPT-native Methodology | Regime（按需） | Critical Dimensions + 四层交易 + Portfolio Gate |
| 大股票池 Top N | CIS 受理 | **Quant Extension** | 候选再回到 CIS Core 深研 |
| 横截面因子/Top-N sanity check | CIS 受理 | **Baseline Backtest Extension** | Backtest Validation；不冒充完整策略回测 |
| 当前市场环境 | Market Regime | 宏观证据 | 不直接触发买卖 |
| ETF / QDII | CIS ETF 模块 | 可验证产品数据 | ETF/QDII专属纪律 |
| 组合再平衡 | 单标的研究 + Regime | Portfolio Gate | 真实组合数据门 |
| 历史复盘/评分校准 | CIS 受理 | **Prediction/Evaluation Extension** | horizon 分离 + 独立样本纪律 |
| 运行原版 TradingAgents | 原版 local/remote | A/B 验证 | external_decision_candidate 仅作输入 |

## Backtest 路由

当前 CIS 只内置：

```text
extensions/research_tooling/backtest_factor_strategy.py
```

规则：

- 仅用于 `date,ticker,score,forward_return` 横截面验证；
- 同一 period 的 ticker 必须唯一；
- 必须检查 point-in-time、survivorship、成本和样本外；
- 不把 baseline evaluator 宣称为事件驱动、订单级或机构级交易引擎；
- 当前没有独立外部交易/回测引擎；超出能力范围必须明确披露。

## Critical Dimension / Context Check 路由

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience + price_context + catalyst_event_review
earnings  → fundamentals + catalyst_macro + risk_resilience
```

其中 tactical 的 `price_context` 与 `catalyst_event_review` 是“检查是否完成”的布尔门；没有正面催化剂可以是合法研究结论，但未检查不能进入 `decision_grade`。

质量门机器枚举统一为：

```text
audit_status = unverified | pass | fail | unresolved
risk_status  = unverified | pass | fail | unresolved
risk_override = none | block
```

关键维度或必需上下文检查缺失时，即使 coverage >= 85%，仍只能 `provisional`。同时，`decision_grade` 只代表 CIS Research Grade；Tactical Setup Readiness 必须另行报告，不能互相覆盖。

## Tactical Price / R/R 路由

只要用户要求短期差价、明确买入价、追不追、止损或目标价，就运行：

```text
scripts/tactical_setup_gate.py
```

输入至少包含：

```text
analysis_timestamp
quote_timestamp
exchange: XNAS | XNYS
market_session（可提供，但必须与代码推导一致）
price_type
current_price
quote_max_age_seconds（活跃时段）
quote_session_date（closed/last_close）
Entry Zone
Stop + stop_type（stop_type 必填）
Target 1
```

Chase Limit 和 Target 2 按任务需要。非 `hard_price` Stop 必须显式提供 `stop_confirmation_met`。

路由语义：

- 活跃时段 stale quote → Price Context fail；
- active quote 的 `quote_timestamp` 不属于当前 analysis session → fail；
- 周末/休市日不能伪装成 `regular`；
- 旧 last close 不是最近已完成 session，或 quote timestamp 日期不匹配 → fail；
- `stop_confirmation_met=true` → 原 setup 持久失效，不因价格反弹复活；
- Stop 当前已失效 → `invalidated_reprice_required`；
- Target 1 已达到/越过 → `setup_expired_reprice_required`；
- 确认型 Stop 已穿越但未确认 → `blocked_pending_stop_confirmation`；
- 超过 Chase Limit → `blocked_do_not_chase`；
- 尚未进入 Entry Zone → `wait_for_entry`。

Quality Score 与 Tactical Setup 必须分开报告。

## Optional Research Tooling

统一位于：

```text
extensions/research_tooling/
```

- Quant：股票池排名/筛选/Top N；横截面必须同一 `as_of`、ticker 唯一；
- Baseline Backtest：轻量横截面验证；
- Prediction/Evaluation：只有用户明确要求记录、复盘或校准时运行；默认观察周期为 5/20/60 交易日；公开 Ledger 只接受 allowlist 字段；
- Evaluation 的相关性按 horizon 分开，5D/20D/60D 不得混成一个总体相关性；样本门槛优先按 unique `research_id`；
- 单股分析不得因为这些文件存在而自动运行；
- Extension 故障不得阻塞 CIS Core。

## Market Regime 路由

Regime 只修正环境、安全边际和交易节奏，不直接覆盖公司基本面，也不产生机械买卖信号。

必须选择：

```text
us_broad_v1  → SPY + S&P500 breadth
us_nasdaq_v1 → QQQ + Nasdaq-100 breadth
```

每个参与分类的信号提供独立 `signal_as_of`。missing/stale 信号先从本次分类排除，再用剩余 fresh signals 重新计算 coverage；fresh coverage 不足才输出 `insufficient`。未来日期仍直接拒绝。

## TradingAgents 上游检查

- 读取 `upstream-status.json`；
- 7 天 TTL 未到：不访问上游；
- TTL 到期：下一次股票研究执行 `check_tradingagents_upstream.py` 的同等逻辑，只检查 SHA；
- 新 SHA → `review_required`，本次仍用稳定基线；
- 不使用定时 GitHub Actions 监控。

## TradingAgents 原版运行安全路由

原版 Remote Runner 分成 Prepare → Analyze → Trusted Publisher：

- Prepare/Analyze 只有 `contents: read`；
- Analyze 执行固定 upstream SHA；
- Cloud/secret-backed run 要求当前 upstream SHA 等于 `reviewed_sha`；
- NVIDIA profile 只能使用固定 NVIDIA endpoint + `NVIDIA_API_KEY`；
- custom compatible profile 只使用 HTTPS endpoint + `OPENAI_COMPATIBLE_API_KEY`；
- Trusted Publisher 拥有 `contents: write`，但不持有 LLM Secret，也不执行第三方 TradingAgents 代码。

只有真实 `.propagate()` 成功且结果请求身份匹配，才能说程序已执行。即便 `execution_status=success` / `runtime_readiness=remote_ready`，研究质量仍需 CIS Evidence/Risk/Score 复核。

## 防重叠规则

- ChatGPT-native Analyst 已覆盖的职责不重复跑同职责 fallback Agent；
- Tactical Gate 只负责价格语义、session/freshness、setup 生命周期和赔率几何；
- Quant 只筛选，不重复做最终公司研究；
- Anthropic 只负责专业子问题，不拥有最终动作权；
- Market Regime 不重复技术分析，只提供环境层；
- Baseline Backtest/Evaluation 只验证和复盘，不自动修改生产规则；
- 最终顺序固定为：证据 → 多角色研究 → 专业增强 → Evidence/Risk → Critical Dimensions/Context Checks → CIS Score → Regime（按需）→ Tactical/Four-layer/ETF/组合门 → 最终中文结论。
