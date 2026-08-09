# QuantConnect LEAN 外部量化引擎（CIS 0.4.5）

## 定位

`QuantConnect/Lean` 被 CIS 接纳为**外部量化验证/回测引擎**，不作为研究总控、基本面分析器或最终决策器。

```text
CIS 提出可执行规则/策略
        ↓
Backtest Validation Policy
        ↓
CIS LEAN Adapter
        ↓
External QuantConnect LEAN
        ↓
原始结果 JSON + 统一指标
        ↓
CIS 审查偏差、样本外、成本和稳健性
```

源码边界：**不 vendor LEAN，不复制 LEAN 源码到 CIS，不把 LEAN 作为 git submodule。** CIS 仅维护 `integrations/lean/` 适配层。

## 什么时候调用

调用 LEAN：

- 用户明确要求对交易策略、技术规则、仓位规则或期权策略做历史回测；
- 新信号/阈值准备从 `experimental` 升级为默认 CIS 规则；
- 需要验证订单路径、费用、持仓变化、最大回撤、Sharpe、CAGR 等策略级指标；
- 需要比轻量横截面 evaluator 更接近可交易策略的事件驱动验证。

默认不调用 LEAN：

- 普通单股研究；
- 只问公司基本面、估值、新闻或当前技术面；
- 只要求一个即时买卖点，但没有要求历史策略验证；
- LEAN 环境不可用且本次任务不以回测为必要条件。

## 与现有 Backtest Extension 的分工

```text
extensions/research_tooling/backtest_factor_strategy.py
  → 轻量横截面 baseline evaluator
  → score / forward_return / Top-N 研究

QuantConnect LEAN
  → 首选策略级回测引擎
  → 事件驱动、订单、费用、持仓路径和更完整策略统计
```

不要为了“多一个结果”默认同时运行两套引擎。只有 A/B 校验、实现差异审查或结果冲突调查时才并行比较。

## 执行契约

CIS 适配器：

```text
integrations/lean/cis_lean_adapter.py
```

支持：

```text
readiness → 检查 Lean CLI / Docker
backtest  → lean backtest <project> --output <directory>
parse     → 解析已有 LEAN result JSON
```

状态枚举固定为：

```text
execution_status = success | invalid_input | unavailable | error
runtime_readiness = ready | lean_cli_missing | docker_missing | unavailable
```

成功结果至少标记：

```text
schema_version = cis.lean.backtest.v1
engine = QuantConnect LEAN
engine_role = external_quant_validation
decision_authority = none
execution_status = success
research_quality = unreviewed
```

关键归一化指标按可用性输出：

```text
cagr
max_drawdown
sharpe_ratio
sortino_ratio
annual_volatility
net_profit
win_rate
loss_rate
profit_loss_ratio
expectancy
alpha / beta
information_ratio
tracking_error
portfolio_turnover
total_orders / total_trades
```

保留 `statistics_raw`，不能只保留 CIS 摘要数字。

## 真实性门

只有同时满足以下条件，才能说“已运行 LEAN 回测”：

1. 本次真实执行适配器 `backtest` 或解析了明确指定的本次 LEAN 结果；
2. `execution_status=success`；
3. 找到可识别的 LEAN statistics JSON；
4. 记录实际策略项目、数据区间、参数、费用模型、基准和结果文件；
5. 没有把旧结果、README、聊天记忆或历史截图冒充本次运行。

`runtime_readiness=ready` 只表示 Lean CLI / Docker 基础环境存在，不代表账户、数据、项目和策略已经可运行。

## 研究质量门

LEAN 不自动解决：

- look-ahead bias；
- survivorship bias；
- universe drift；
- restatement leakage；
- data snooping / overfitting；
- 不现实的手续费、滑点、成交和流动性假设；
- 样本外不足。

因此 LEAN 成功结果仍必须经过 `backtest-validation.md`。未经审查一律：

```text
research_quality = unreviewed
```

## 故障与降级

LEAN 是 External/Optional 能力：

- 缺 Lean CLI → `execution_status=unavailable`；
- 缺 Docker → `execution_status=unavailable`；
- 账户/数据/项目错误 → 由 Lean CLI 非零退出并记录为 `error`；
- 结果 JSON 不完整 → `result_parse_error`；
- 任何故障都不得阻塞普通 CIS Core 股票研究。

如本次只是横截面因子 sanity check，可退回 `backtest_factor_strategy.py`；但必须明确它是 baseline evaluator，不能冒充完整 LEAN 策略回测。

## 自动交易边界

当前 CIS **不启用 LEAN live trading / Broker 自动执行**。即使 LEAN 支持 live trading，也只有用户未来明确要求、单独完成 Broker 权限/风控/熔断/审计设计后才可另行评估。当前集成只负责回测和结果解析。

## 上游版本检查

LEAN 复用 TradingAgents 已有的**使用时检查 + 7 天 TTL**机制，不新增定时 GitHub Actions：

```text
plugins/chen-investment-system/skills/cis/scripts/check_tradingagents_upstream.py
runtime/tradingagents/upstream-status.json
```

当任务涉及 LEAN 引擎、版本、回测环境或集成验证时，先运行：

```bash
python plugins/chen-investment-system/skills/cis/scripts/check_tradingagents_upstream.py --component lean
```

规则：

- 7 天 TTL 未到：直接使用缓存状态，不访问上游；
- TTL 到期：检查 `quantconnect/lean` Docker Hub 的最新数字 build tag；
- 新 tag 与 `reviewed_tag` 不同：只标记 `review_required`；
- **绝不自动升级** `quantconnect/lean:<tag>`；
- 新版本必须先通过 CIS LEAN integration / strategy smoke / backtest validation，再人工更新 `reviewed_tag` 与 heavy workflow 的 pinned image；
- 上游检查暂时不可用时，允许继续使用已审查的稳定 pinned baseline，但不得声称“已确认最新”。

当前 heavy LEAN workflow 的已审查 baseline 为 `quantconnect/lean:17948`。官方 QuantConnect 文档说明本地 LEAN 回测使用 `quantconnect/lean` Docker image，并可通过 `--image` 指定固定版本；官方 Docker Hub 以 build number 标记可用版本。因此 CIS 以 Docker build tag 作为版本检测对象，而不是直接跟踪 GitHub `main`。
