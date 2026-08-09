# CIS 0.4.2 系统流程

## 0. Runtime Guard

1. 读取当前 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，核验 `chentinghui/chen-investment-system` 当前 `main`。
3. 读取 `tradingagents-methodology.md` 作为股票默认研究方法。
4. 读取 `runtime/tradingagents/upstream-status.json`。距离 `last_checked_at` 不足 `check_ttl_days=7` 时直接使用稳定基线；达到或超过 7 天时，由下一次股票研究通过 `scripts/check_tradingagents_upstream.py` 的同等逻辑轻量检查 TradingAgents 当前 `main` SHA。SHA 变化标记 `review_required`，未经审查不得采用新逻辑。
5. 原版 TradingAgents 仅在用户明确要求运行/测试时启动；其 `execution_status=success` 只表示程序完成，不表示研究质量通过。
6. 专业金融子问题按需路由 Anthropic Financial Services。

## 1. Intake

识别对象、问题、市场、模式、期限、`analysis_date/as_of`、股票池/基准和用户真实持仓资料，并确定评分 `decision_context`：`generic | long_term | tactical | earnings`。

## 2. Quant Pre-screen（按需）

只有大股票池、排名、Top N、主题筛选等任务优先运行 Quant Research Engine：

```text
Point-in-time Universe → Factor Ranking → Top N → 深度研究
```

单只股票研究不强制 Quant。`quant_score` 不等于 `cis_score`。横截面排名必须使用同一 `as_of`。

## 3. Evidence

按 `evidence-confidence.md` 登记来源等级、发布日期、资料期间、提取日期、事实、限制和冲突。历史任务必须防前视偏差。

## 4. 默认通用研究核心

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

## 5. 专业金融子问题

DCF / Comps / 三表 / 模型审计 / Earnings / Initiating Coverage / Model Update / Competitive / Thesis / Catalyst 等按需路由 Anthropic Financial Services，并回灌同一证据登记。

## 6. Evidence Audit + Risk Gate

Evidence 与 Risk 都采用 fail-closed：未明确 `pass` 就不能进入 `decision_grade`。

依次检查：

1. 数据截止时间；
2. 数据源/市场覆盖；
3. 会计或指标口径；
4. 时间跨度；
5. 预测假设；
6. 估值方法；
7. 技术/情绪短期信号与长期基本面冲突；
8. 事实与判断混淆。

关键冲突不能靠多数票或平均目标价消除。

## 7. Critical Dimension Gate + CIS 八维评分

先检查任务关键维度，再按 `scoring-engine.md` 汇总八维分数。

当前关键维度：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

- coverage < 70%：insufficient；
- 70%–<85%：provisional；
- >=85% + Audit pass + Risk pass + Critical Dimensions 完整：才可 decision_grade。

## 8. Market Regime（按需）

当市场环境会影响交易计划时，读取 `market-regime.md`，输出 `risk_on / neutral / risk_off / insufficient`。

Regime 只能影响宏观/风险证据、安全边际和交易节奏，不能直接产生买卖动作。

## 9. 四层交易框架

涉及买入、持有、加减仓、止盈、止损、退出或具体价位时执行：

1. 趋势：20/50/200 日均线；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时覆盖盈利止盈与防守止损。

## 10. ETF / QDII Gate

跨境 ETF/QDII 优先执行产品身份、基准、IOPV、历史溢价、申赎/额度、时差和流动性纪律，不默认套用股票研究结论。

## 11. Portfolio Gate

只有持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位或再平衡动作。CIS 不自动下单。

## 12. Synthesis

最终输出研究姿态、评分 coverage、关键维度状态、为什么不是更高/更低分、关键证伪条件、下一复盘触发点。

## 13. Prediction Ledger + Backtest / Calibration

需要长期复盘的研究使用 `scripts/prediction_ledger.py` 记录 append-only prediction event；到期后追加 outcome event，禁止回写历史预测。

新增因子、阈值和生产规则按 `backtest-validation.md` 做偏差检查、按换手率扣成本，并分 train / validation / out-of-sample 验证。

`evaluate_cis_predictions.py` 按总分、horizon、regime 和八维 dimension 做校准诊断。脚本可以生成报告，但禁止自动修改生产权重。

## 14. 原版 TradingAgents 测试路径

只有用户明确要求时，才按 `tradingagents.md` 运行本地/远程原版程序。远程每次拉取上游当前 `main`，结果仍只是 `external_decision_candidate`。

必须区分：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```

程序执行成功不能绕过 CIS 最终质量门。
