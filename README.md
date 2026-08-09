# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.4.5**

CIS 是一个中文系统化股票研究控制层。它的核心职责是**分析**：组织证据、多角色研究、风险审查、评分、市场环境和交易计划。CIS 不自动下单，也不要求每次研究都运行量化、Alpha 挖掘、回测或历史绩效模块。

## CIS Core

```text
用户
  ↓
CIS Control Layer
  ↓
ChatGPT-native TradingAgents Methodology
  ↓
Anthropic Financial Services（专业子问题按需）
  ↓
Evidence Audit + Risk Review（fail-closed）
  ↓
Critical Dimension / Context Checks
  ↓
CIS 八维 Quality Score / Research Grade
  ↓
Market Regime（按交易问题需要）
  ↓
US-equity Price/Session Baseline + Quote Freshness + Tactical R/R Gate（短线按需）
  ↓
四层交易 / ETF-QDII / Portfolio Gate
  ↓
最终中文分析结论
```

日常单股分析只运行与当前问题相关的 Core 能力。外围研发工具不可用时，不阻塞 CIS Core。

## Alpha Research Agent

Alpha Discovery / Validation 独立放在：

```text
extensions/alpha_research/
```

第一版将 **WorldQuant BRAIN** 作为外部 Alpha 候选来源：

```text
WorldQuant BRAIN export / 合法 API JSON
        ↓
worldquant/alpha_import.py
        ↓
cis.alpha_candidate.v1
        ↓
worldquant/alpha_validator.py
        ↓
factor_engine / ml_research
        ↓
CIS Evidence / Risk / Portfolio Review
```

核心边界：

- BRAIN 只负责提供 Alpha 候选，不负责 CIS 最终买卖裁决；
- 不保存 BRAIN 密码/API key，不自动提交 Alpha，不连接 Broker 自动交易；
- 所有输出固定 `decision_authority=none`、`research_status=unreviewed`；
- 通过 Sharpe / Turnover / Fitness 等初筛只得到 `candidate_for_cis_validation`；
- 仍需检查经济解释、前视/数据泄漏、样本外、换手/成本/容量、相关性/分散化；
- Factor Engine 提供横截面 Rank IC / IC hit rate / Top-Bottom spread；
- ML Research 只评估外部 prediction 的 train/validation/test，不在 CIS 内自动训练模型。

## 0.4.5 Contract & Security Hardening

0.4.5 基线继续保持接口、边界条件和供应链安全：

- **Agent ↔ Score 契约统一**：Evidence 使用 `audit_status=unverified|pass|unresolved|fail`；Risk 使用 `risk_status=unverified|pass|unresolved|fail`、`risk_override=none|block`。`conditional/caution` 不再作为机器枚举。
- **Quote Observation Session**：active quote 的 `quote_timestamp` 本身必须属于与分析一致的 session，盘前旧报价不能包装成 regular `live`。
- **Persistent Setup Invalidation**：确认型/技术型失效一旦确认，价格随后反弹也不能让旧 setup 自动复活；必须重新定 Entry/Stop/Target。
- **Stop Type fail-closed**：短线正式 setup 必须显式给 `hard_price | close_confirmation | technical_invalidation`，不再静默默认 hard stop。
- **ETF 输入加固**：价格/IOPV 拒绝 JSON boolean；历史溢价 `ready` 至少要求 20 个唯一日期，重复同日数据不能膨胀样本。
- **TradingAgents Remote 权限隔离**：第三方代码只在 `contents: read` Job 运行；写回由独立 trusted publisher 完成，publisher 不持有 LLM Secret，也不执行第三方代码。
- **Secret / Endpoint 绑定**：NVIDIA profile 只允许固定 NVIDIA endpoint + `NVIDIA_API_KEY`；自定义 HTTPS compatible endpoint 只允许 `OPENAI_COMPATIBLE_API_KEY`，不跨 provider fallback。
- **Reviewed SHA Gate**：Cloud/secret-backed 原版 TradingAgents 只有当前 upstream SHA 已被审查时才允许执行；未审查最新 main 只能做零密钥 Ollama smoke test。
- **Evaluation 样本纪律**：5D/20D/60D 不再混成总体相关性；样本门槛优先按 unique `research_id`，避免把多个 horizon 当作独立实验。
- **Public Ledger allowlist**：Prediction/Evaluation 公共记录只允许固定结构化字段，任意 notes/account/shares/cost_basis 等未批准字段直接拒绝。
- **Quant / Backtest 数据质量**：Quant 拒绝重复 ticker 和单点伪横截面；Backtest 拒绝重复 `(date,ticker)` 与不可能的低于 -100% return。
- **Alpha Research 安全边界**：WorldQuant/BRAIN 候选不得携带 credential、brokerage 或 live-order 字段，任何 Alpha 初筛结果都没有最终动作权。

## Optional Research Tooling

以下能力保留，但物理隔离在：

```text
extensions/research_tooling/
```

它们不是日常单股分析链的一部分：

- `quant_factor_engine.py`：大股票池/Top N 候选排序；
- `backtest_factor_strategy.py`：新规则、因子、阈值的历史验证；
- `prediction_ledger.py`：可选研究记录；
- `record_cis_research.py`：可选研究快照；
- `settle_due_predictions.py`：实验性结果结算；
- `evaluate_cis_predictions.py`：历史表现与校准诊断。

路由原则：单股分析不自动调用这些工具；大股票池筛选才按需调用 Quant；验证规则才调用 Backtest；用户明确要求记录、复盘或校准时才调用 Evaluation。Extension 故障不得阻塞 CIS Core。

## TradingAgents 上游策略

日常股票研究默认使用 CIS 已审查的稳定 TradingAgents 方法论。TradingAgents 上游采用 **7 天 TTL** 的使用时检查：TTL 未到不访问上游；到期后的下一次股票研究轻量检查当前 `main` SHA；发现变化只标记 `review_required`，未经审查不会覆盖稳定方法论。

用户明确要求运行原版 TradingAgents 时，远程路径仍以当时 upstream `main` 为目标，但 0.4.5 增加安全门：

```text
Prepare / Analyze Job: contents: read
固定 upstream SHA
按 provider 只注入一项所需 Secret
        ↓ Artifact
Trusted Publisher: contents: write
无 LLM Secret
不执行第三方代码
```

Secret-backed run 要求当前 upstream SHA 等于 `reviewed_sha`；未审查最新 main 只允许零密钥 smoke test。原版结果仍只能作为 `external_decision_candidate`，不能绕过 CIS 最终质量门。

## Anthropic Financial Services

需要 DCF、Comps、Earnings、三表、模型审计、竞争分析、论点或催化剂等专业金融方法时，优先读取 Anthropic `financial-services` 上游 `main` 的目标 Skill。只有本次真实读取/执行后才能声称使用；输出仍必须经过 CIS Evidence/Risk/Score 等规则。

## CIS 八维评分

| 维度 | 权重 |
|---|---:|
| fundamentals | 20 |
| growth | 15 |
| valuation | 15 |
| industry_competitive | 10 |
| technical | 15 |
| catalyst_macro | 10 |
| positioning | 5 |
| risk_resilience | 10 |

```text
coverage < 70%        → insufficient
70% <= coverage < 85% → provisional
coverage >= 85%       → 仍需 Audit/Risk/Critical Dimensions/Context Checks 全部通过才可 decision_grade
```

Critical Dimensions / Context Checks：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience + price_context + catalyst_event_review
earnings  → fundamentals + catalyst_macro + risk_resilience
```

## Tactical Setup Gate

对短线做差价、具体买点或“现在能不能追”的问题，CIS 额外执行：

```text
analysis_timestamp / quote_timestamp
US-equity session baseline + quote observation session
price_type / quote freshness
Entry Zone
Chase Limit
Stop / Stop Type
Target 1 / 2
Reward / Risk
Setup State
```

按 Entry Zone 中最差 Target 1 R/R 的 baseline：

```text
<1.0       reject
1.0-<1.5   weak_setup
1.5-<2.0   acceptable
>=2.0      attractive
```

这些阈值是纪律 baseline，不是已经证明最优的参数。高 CIS Quality Score 也不能覆盖 `blocked_do_not_chase`、`invalidated_reprice_required` 或 `setup_expired_reprice_required`。

## Market Regime

当前 baseline 必须显式选择：

```text
us_broad_v1  → SPY + S&P500 breadth
us_nasdaq_v1 → QQQ + Nasdaq-100 breadth
```

`missing/stale` 信号会从本次分类中排除；只有剩余 fresh coverage >=60% 且 fresh signals >=3 时才允许输出 experimental `risk_on / neutral / risk_off`。Regime 只是环境层，不直接触发买卖。

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. 趋势：20/50/200 日均线；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈与防守止损。跨境 ETF/QDII 还必须核验产品身份、基准、IOPV、历史溢价、申赎/额度、时差和流动性。

## 风险声明

CIS 用于研究组织、证据核验、Alpha 研究、筛选、回测和分析辅助，不构成收益承诺，也不连接 Broker 自动执行交易。模型、数据、因子、Alpha 和历史回测都可能失效，最终投资决定仍需独立判断。
