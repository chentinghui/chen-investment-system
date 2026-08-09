# CIS Backtest / Validation Policy（0.4.5）

回测的用途是**验证规则是否在历史上具有统计价值**，不是证明未来一定有效。

## 当前引擎边界

CIS 当前仓库只内置轻量 Python 横截面 baseline evaluator：

```text
extensions/research_tooling/backtest_factor_strategy.py
  → date,ticker,score,forward_return
  → Top-N / 因子排序 sanity check
```

当前**没有接入独立事件驱动交易/回测引擎**。因此如果任务需要订单撮合、复杂持仓路径、期权生命周期、分钟/Tick 级执行或其他 baseline evaluator 未实现的能力，必须明确报告 `not_implemented` / 能力不足，不得把轻量 evaluator 冒充完整策略回测。

## 必须验证的对象

- Quant Engine 因子与权重；
- CIS 分数区间与未来收益/超额收益的关系；
- 可由当前 Python 研究环境正确表达的技术/趋势规则；
- Market Regime 条件化后的规则表现；
- 任何准备提升为“默认规则”的新信号。

## 最低指标集

策略/规则研究至少记录：

- 累计收益 / CAGR（适用时）；
- 年化波动率（适用时）；
- Sharpe Ratio（适用时）；
- 最大回撤（适用时）；
- 胜率或命中率（适用时）；
- 基准超额收益；
- 交易/观察数量；
- 费用、换手率；
- 样本数量与覆盖时间。

因子/横截面研究还必须记录：

- 按分数/分位数组的未来收益单调性；
- 平均换手率与累计交易成本。

## 强制偏差检查

任何回测/因子验证都必须检查：

1. **Look-ahead bias**：历史日期只能使用当时已公开数据。
2. **Survivorship bias**：股票池必须尽可能包含退市/被并购/后来被剔除的标的。
3. **Universe drift**：历史指数成分不能用今天的成分回填。
4. **Restatement leakage**：历史财务数据优先采用当时版本。
5. **Transaction costs**：成本按实际组合换手率/可表达的交易路径扣减，不能假设零费用、零滑点或无限流动性。
6. **Data snooping**：反复调参后必须做样本外验证。
7. **Cross-section uniqueness**：baseline evaluator 同一 period 的 `(date,ticker)` 必须唯一。
8. **Return validity**：`forward_return` / benchmark return 必须为有限数值，不能低于 -100%；`cost_bps` 必须是有限非负数。
9. **Row completeness**：`date/ticker/score/forward_return` 是必需输入，坏行不得静默 drop。
10. **Execution realism**：如果研究包含 next-open、止损、限价、滑点或其他执行假设，必须明确实现方式；当前 evaluator 未实现的执行细节不能用 close-to-close 结果代替。

## 样本外纪律

默认分为：

```text
训练/设计期 → 验证期 → 样本外测试期
```

`extensions/research_tooling/backtest_factor_strategy.py` 支持 `train_end` / `validation_end` 分段，并单独报告 `out_of_sample` 指标。样本足够时优先使用 walk-forward；当前脚本仍是 baseline evaluator，不声称已实现完整机构级交易仿真框架。

参数优化、阈值选择或策略选择若使用过同一时期，该时期不能再被称为真正独立样本外测试。

## 最小横截面回测

输入：

```text
date,ticker,score,forward_return[,benchmark_return]
```

每个日期按 score 选择 Top 分位/Top N，等权形成组合。

交易成本按：

```text
one_way_turnover = 0.5 × Σ|new_weight - old_weight|
transaction_cost = one_way_turnover × configured_cost_rate
```

首次从现金建仓按 100% one-way turnover 处理。若持仓完全不变，下期换手成本为 0。

`forward_return` 必须由独立数据处理流程产生，不能由脚本在知道未来信息的基础上反向构造信号。任何必需行缺少 `forward_return` 时回测必须停止，而不是把该证券从样本中删除。

## 通过标准

任何规则要从“实验”升级成“默认 CIS 规则”，至少应满足：

- 有足够样本与跨市场环境覆盖；
- 样本外方向一致；
- 结果不是由少数极端观察贡献；
- 成本后仍有价值；
- 对参数小幅变化不敏感；
- 能解释经济/行为机制，而不是纯数据挖掘；
- 执行假设与研究结论的口径一致。

未满足时只能标记 `experimental`。当前 Python baseline 的能力边界必须随结果一起披露。
