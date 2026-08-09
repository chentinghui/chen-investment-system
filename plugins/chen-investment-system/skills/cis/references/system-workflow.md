# CIS 0.4.2 系统流程

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

## 2. Evidence

登记来源等级、发布日期、资料期间、提取日期、事实、限制和冲突。历史任务必须防前视偏差。

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
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

- coverage < 70%：insufficient；
- 70%–<85%：provisional；
- >=85% + Audit pass + Risk pass + Critical Dimensions 完整：才可 decision_grade。

## 7. Market Regime（按需）

当前市场环境会改变交易计划时，输出 `risk_on / neutral / risk_off / insufficient`。Regime 不直接机械触发买卖。

## 8. 四层交易框架

涉及买卖、持仓、止盈止损或具体价位时执行：趋势 → 价格 → 成交 → 风险。卖出必须同时覆盖盈利止盈与防守止损。

## 9. ETF / QDII / Portfolio Gate

跨境 ETF/QDII 执行产品身份、基准、IOPV、溢价、申赎、时差和流动性纪律。组合动作只有在真实持仓、权重、成本、基准、约束和资金需求足够时才给精确比例。

## 10. Synthesis

输出最终中文分析结论、评分 coverage、关键维度状态、为什么不是更高/更低分、价位/风险条件、关键证伪条件和复盘触发点。

## 11. Optional Research Tooling

只有对应任务才调用：

```text
extensions/research_tooling/
```

- 大股票池/Top N → `quant_factor_engine.py`；
- 新规则/因子/阈值验证 → `backtest_factor_strategy.py`；
- 用户明确要求记录/复盘/校准 → Prediction / Evaluation 工具。

这些外围工具不属于默认单股分析链，故障不得阻塞 CIS Core，也不得自动修改生产规则。

## 12. 原版 TradingAgents 测试路径

只有用户明确要求时，才按 `tradingagents.md` 运行本地/远程原版程序。远程每次拉取上游当前 `main`，结果仍只是 `external_decision_candidate`。

必须区分：

```text
execution_status
runtime_readiness
evidence_audit_status
research_quality
```
