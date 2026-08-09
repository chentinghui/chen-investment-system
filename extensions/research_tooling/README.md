# CIS Research Tooling Extension

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

## 0.4.3 Tactical Alignment

可选 Prediction/Evaluation 的默认 horizon 已改为：

```text
5 / 20 / 60 trading days
```

`settle_due_predictions.py` 不再把研究日或研究日前的收盘价当作后续可执行 Entry。第一版使用指定 benchmark 的后续 session 作为交易日历代理：研究日之后的第一个 benchmark session 才能成为 entry session；目标 horizon 也按 benchmark sessions 计数。若股票在对应 session 没有价格，则保持 unresolved，不把后面的价格偷偷替代。

当前 MFE/MAE 仍基于 adjusted close 路径，所以 outcome 会明确写入：

```text
path_metric_basis = adjusted_close_only
```

这不是盘中 High/Low 版 MFE/MAE，不能混淆。

## 当前定位

该扩展保留研发和复盘能力，但不构成 CIS 的默认数据层或自动绩效系统。即使该扩展不可用，也不影响 CIS Core 的股票分析结论。
