# CIS 外部模块适配与降级（0.4.2）

外部模块的“存在/可访问”“程序执行成功”“研究质量通过”必须分开判断。README、历史运行记录、聊天记忆或模块名称都不能证明本次已运行，更不能证明结果可靠。

## TradingAgents 上游

- 上游：`TauricResearch/TradingAgents`。
- CIS 日常股票研究默认**不运行其 Python 程序**，而是使用 `tradingagents-methodology.md` 的 ChatGPT-native 稳定方法论。
- 原版 Python 只用于用户明确要求的运行/测试、A/B 验证或上游功能审查。
- 远程显式测试每次重新 clone 上游当前 `main`。
- 日常上游检查使用 `runtime/tradingagents/upstream-status.json` 的 **7 天 TTL**。
- TTL 的确定性执行器是 `scripts/check_tradingagents_upstream.py`：距离 `last_checked_at` 不足 7 天时不访问上游；达到或超过 7 天后才检查当前 `main` SHA，并可刷新状态文件。
- SHA 变化时标记 `review_required`，当次仍使用 CIS 已验证稳定基线。
- 上游暂时不可访问不阻塞正常研究；披露 `upstream_check=unavailable`。
- 用户明确要求“检查 TradingAgents 更新”时可忽略 TTL 立即检查。
- **不使用定时 GitHub Actions 监控 TradingAgents 上游。**
- 上游变化不得自动覆盖 CIS 方法论。

### 原版运行状态分层

程序执行状态与研究质量分开：

```text
execution_status = success | error | invalid_input | unavailable
runtime_readiness = installed_ready | installed_limited | remote_ready | remote_limited | upstream_only | blocked

evidence_audit_status = not_run | pass | unresolved | fail
research_quality = unreviewed | accepted | rejected
```

`remote_ready` / `installed_ready` **只表示程序运行完成**，不表示事实正确、证据可靠或最终结论被 CIS 接受。

原版 Portfolio Manager / BUY-SELL-HOLD 统一记为 `external_decision_candidate`，无最终动作权。

## Anthropic Financial Services

Anthropic `financial-services` 是 CIS 首选专业金融 Skill 上游，用于：

- DCF / Comps；
- 三表、数据清洗、模型审计；
- Earnings Preview / Analysis；
- Initiating Coverage / Model Update；
- Competitive Analysis / Sector Overview；
- Thesis Tracker / Catalyst Calendar / Idea Generation。

只有本次真实读取/执行对应 Skill 且关键输入完整时，才能标记为已使用。输出必须回灌 CIS Evidence Gate。

## Buffett / 其他可选方法

任何外部投资方法都只能作为可选视角或证据增强，不得覆盖 CIS 的 Evidence、Risk、Score、Critical Dimension、Regime、四层交易、ETF/QDII和组合门。

## 数据连接器

- 代码/Skill 可用不等于数据已授权或实时。
- 行情、财报、新闻、宏观、机构持仓、资金流必须记录实际来源和 `as_of`。
- 历史研究必须使用 point-in-time 数据，禁止 look-ahead leakage。
- 数据不可用时可降级到公开资料/用户资料，但必须说明覆盖限制。

## Quant / Backtest 注意

Quant、Backtest、Regime、Prediction Ledger 和 Performance Loop 是 CIS 自有确定性/规则模块，不依赖外部 LLM，但输入数据仍必须满足 point-in-time、股票池和偏差纪律。
