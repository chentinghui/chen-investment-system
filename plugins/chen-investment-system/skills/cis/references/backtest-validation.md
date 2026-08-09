# CIS Backtest / Validation Policy

回测的用途是**验证规则是否在历史上具有统计价值**，不是证明未来一定有效。

## 必须验证的对象

- Quant Engine 因子与权重；
- CIS 分数区间与未来收益/超额收益的关系；
- 技术/趋势规则；
- Market Regime 条件化后的规则表现；
- 任何准备提升为“默认规则”的新信号。

## 最低指标集

- CAGR / 年化收益；
- 年化波动率；
- Sharpe Ratio；
- 最大回撤；
- 胜率；
- 基准超额收益；
- 按分数/分位数组的未来收益单调性；
- 样本数量与覆盖时间。

## 强制偏差检查

1. **Look-ahead bias**：历史日期只能使用当时已公开数据。
2. **Survivorship bias**：股票池必须尽可能包含退市/被并购/后来被剔除的标的。
3. **Universe drift**：历史指数成分不能用今天的成分回填。
4. **Restatement leakage**：历史财务数据优先采用当时版本。
5. **Transaction costs**：至少允许配置佣金/点差/滑点的 bps 成本。
6. **Data snooping**：反复调参后必须做样本外验证。

## 样本外纪律

默认分为：

```text
训练/设计期 → 验证期 → 样本外测试期
```

当样本足够时优先使用 walk-forward，而不是一次性在全部历史上找最优参数。

## 最小横截面回测

`scripts/backtest_factor_strategy.py` 接收 point-in-time 数据：

```text
date,ticker,score,forward_return[,benchmark_return]
```

每个日期按 score 选择 Top 分位/Top N，等权形成组合，再计算收益、Sharpe、最大回撤和基准超额收益。

这里的 `forward_return` 必须由独立数据处理流程产生，不能由脚本在知道未来信息的基础上反向构造信号。

## 通过标准

任何规则要从“实验”升级成“默认 CIS 规则”，至少应满足：

- 有足够样本与跨市场环境覆盖；
- 样本外方向一致；
- 结果不是由少数极端交易贡献；
- 成本后仍有价值；
- 对参数小幅变化不敏感；
- 能解释经济/行为机制，而不是纯数据挖掘。

未满足时只能标记 `experimental`。
