# CIS Research Tooling Extension（0.4.5）

本目录是 **CIS Core 的可选外围研究工具**，不属于日常单股分析运行链。

CIS Core 的职责仅包括：

- ChatGPT-native TradingAgents 多角色股票研究；
- Evidence Audit / Risk Review / Critical Dimension / Context Checks；
- CIS 八维评分；
- Market Regime（按交易问题需要）；
- Price/Session Guard + Tactical R/R Gate（短线按需）；
- 四层交易框架、ETF/QDII、Portfolio Gate；
- 最终中文分析结论。

本扩展只在明确需要时使用：

- `quant_factor_engine.py`：大股票池候选排序；
- `backtest_factor_strategy.py`：新规则/因子/阈值历史验证；
- `prediction_ledger.py`：可选预测记录；
- `record_cis_research.py`：可选研究快照；
- `settle_due_predictions.py`：实验性结果结算；
- `evaluate_cis_predictions.py`：历史表现/校准诊断。

## 边界

1. 分析一只股票时，CIS Core **不得因为这些文件存在而自动运行它们**。
2. Quant 仅在股票池筛选/Top N 任务按需启用。
3. Backtest 仅在验证规则有效性时启用。
4. Prediction/Evaluation 仅在用户明确要求记录、复盘或校准时启用。
5. Extension 故障不得阻塞 CIS Core 的正常股票分析。
6. Extension 不拥有 CIS 最终动作权，也不得自动修改生产评分权重。
7. TradingAgents 7 天 TTL 与 Anthropic Financial Services 上游读取策略仍由 CIS Core/对应外部模块规范管理，不属于本扩展。

## 0.4.5 Data / Evaluation Hardening

### Quant

- 横截面必须同一 `as_of`；
- ticker 必须唯一且非空；
- custom factor weight 必须为有限正数；
- factor 至少达到 `min_factor_observations` 才形成 percentile，并计入 coverage；只有单点数据时不会产生伪排名。

### Backtest

- 同一 period 的 `(date,ticker)` 必须唯一；
- `cost_bps` 必须有限且非负；
- forward / benchmark return 不能低于 -100%；
- 仍要求 point-in-time、survivorship-aware 输入。

### Prediction / Recorder

公开 Ledger 使用**结构化 allowlist**。任何未批准字段，包括 `notes/account/shares/cost_basis/position_size` 等，都直接拒绝。不要把原始聊天或个人组合记录放进公共评估数据。

默认观察周期：

```text
5 / 20 / 60 trading days
```

### Settlement

当前 settlement 是研究指标，不是实际交易模拟：

```text
entry_price_basis = next_benchmark_session_adjusted_close
return_semantics = next_session_close_to_close_adjusted_price_return
path_metric_basis = adjusted_close_only
```

Yahoo Adjusted Close 缺失时不再 fallback 到 raw close。缺少目标 session 价格、存在无法审计的价格口径或 terminal event 无法处理时保持 `unresolved`。

当前尚未实现退市、破产、现金/股票并购等完整 terminal-return 规则，因此**不能把 settlement 输出称为真实可执行交易 P&L**。

### Evaluation

5D / 20D / 60D 属于同一次 research 的相关结果：

- 不把多个 horizon 混成一个 pooled correlation；
- 相关性和 dimension diagnostics 按 horizon 独立；
- 样本门槛优先按 unique `research_id`，不是 outcome 行数；
- research_id 缺失时，即使行数 >=100 也只能标记 independence 未验证。

## 当前定位

该扩展保留研发和复盘能力，但不构成 CIS 的默认数据层或自动绩效系统。即使该扩展不可用，也不影响 CIS Core 的股票分析结论。
