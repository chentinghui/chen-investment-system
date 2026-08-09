# CIS Research Tooling Extension

本目录是 **CIS Core 的可选外围研究工具**，不属于日常单股分析运行链。

CIS Core 的职责仅包括：

- ChatGPT-native TradingAgents 多角色股票研究；
- Evidence Audit / Risk Review / Critical Dimension Gate；
- CIS 八维评分；
- Market Regime（按交易问题需要）；
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
4. Evaluation 仅在用户明确要求记录、复盘或校准时启用。
5. Extension 故障不得阻塞 CIS Core 的正常股票分析。
6. Extension 不拥有 CIS 最终动作权，也不得自动修改生产评分权重。
7. TradingAgents 7 天 TTL 与 Anthropic Financial Services 上游读取策略仍由 CIS Core/对应外部模块规范管理，不属于本扩展。
