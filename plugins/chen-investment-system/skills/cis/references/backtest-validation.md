# CIS Backtest / Validation Policy（0.4.5）

回测的用途是**验证规则是否在历史上具有统计价值**，不是证明未来一定有效。

## 引擎路由

CIS 现在区分两类回测：

```text
QuantConnect LEAN
  → 首选策略级外部回测引擎
  → 事件驱动、订单、费用、持仓路径、股票/ETF/期权等可执行策略验证

extensions/research_tooling/backtest_factor_strategy.py
  → 轻量横截面 baseline evaluator
  → date,ticker,score,forward_return 的 Top-N / 因子排序 sanity check
```

只要任务需要验证**可执行交易规则**，优先读取 `quantconnect-lean.md` 并通过：

```text
integrations/lean/cis_lean_adapter.py
```

调用外部 LEAN。不要为了“多一个结果”默认同时跑两套引擎。只有 A/B 校验、实现差异审查或结果冲突调查时才并行比较。

LEAN 不属于 CIS Core。Lean CLI、Docker、账户、数据或项目不可用时，不得阻塞普通单股研究；但若用户明确要求“用 LEAN 回测”，必须披露 `execution_status`，不能用 baseline evaluator 冒充 LEAN。

只有真实执行成功并解析到 LEAN statistics JSON，才能说“已运行 LEAN 回测”。任何 LEAN 成功结果初始都必须标记：

```text
engine_role = external_quant_validation
decision_authority = none
research_quality = unreviewed
```

## 必须验证的对象

- Quant Engine 因子与权重；
- CIS 分数区间与未来收益/超额收益的关系；
- 技术/趋势规则；
- Market Regime 条件化后的规则表现；
- 任何准备提升为“默认规则”的新信号。

## 最低指标集

策略级 LEAN 回测优先记录：

- CAGR / 年化收益；
- 年化波动率；
- Sharpe Ratio；
- 最大回撤；
- 胜率；
- 基准超额收益；
- 总订单/交易数量；
- 费用、换手率及可获得的容量信息；
- 样本数量与覆盖时间。

因子/横截面研究还必须记录：

- 按分数/分位数组的未来收益单调性；
- 平均换手率与累计交易成本。

LEAN 适配器会把可识别的百分比指标归一化为小数，同时保留 `statistics_raw`。CIS 不得只保留摘要数字而丢弃原始统计。

## 强制偏差检查

无论使用 LEAN 还是 baseline evaluator，都必须检查：

1. **Look-ahead bias**：历史日期只能使用当时已公开数据。
2. **Survivorship bias**：股票池必须尽可能包含退市/被并购/后来被剔除的标的。
3. **Universe drift**：历史指数成分不能用今天的成分回填。
4. **Restatement leakage**：历史财务数据优先采用当时版本。
5. **Transaction costs**：成本按实际组合换手率/订单路径扣减，不能假设零费用、零滑点或无限流动性。
6. **Data snooping**：反复调参后必须做样本外验证。
7. **Cross-section uniqueness**：baseline evaluator 同一 period 的 `(date,ticker)` 必须唯一。重复 ticker 会让持仓权重与收益平均口径不一致，因此直接拒绝。
8. **Return validity**：baseline evaluator 的 `forward_return` / benchmark return 必须为有限数值，不能低于 -100%；`cost_bps` 必须是有限非负数。
9. **Row completeness**：baseline evaluator 的 `date/ticker/score/forward_return` 是必需输入。任何一行缺失或损坏都直接报错，不得静默 drop；否则退市、坏数据或极端亏损样本可能被系统性排除，造成结果偏高。可选 `benchmark_return` 若留空视为缺失，但若非空却无法解析，也必须报错。
10. **Execution realism**：LEAN 策略必须审查订单类型、成交模型、手续费、滑点、分红拆股、期权到期/行权、交易时段和数据分辨率是否与真实策略一致。

**LEAN 本身不会自动消除前视偏差、幸存者偏差、过拟合或不现实的交易假设。** 引擎运行成功不能替代这些质量门。

## 样本外纪律

默认分为：

```text
训练/设计期 → 验证期 → 样本外测试期
```

`extensions/research_tooling/backtest_factor_strategy.py` 支持 `train_end` / `validation_end` 分段，并单独报告 `out_of_sample` 指标。样本足够时优先使用 walk-forward；当前脚本仍是 baseline evaluator，不声称已实现完整机构级回测框架。

LEAN 策略也必须显式保留样本外区间。参数优化、阈值选择或策略选择若使用过同一时期，该时期不能再被称为真正独立样本外测试。

## 最小横截面回测

仅适用于 baseline evaluator。输入：

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

## LEAN 结果真实性门

对任何声称来自 QuantConnect LEAN 的结果，至少记录：

```text
actual project / strategy
backtest period
benchmark
key parameters
fee/slippage assumptions
result_file
execution_status
research_quality
```

只有 `execution_status=success` 且结果文件包含可识别 statistics 时，才可作为“已运行结果”。`runtime_readiness=ready`、README、历史截图或旧 JSON 都不能证明本次已经运行。

## 通过标准

任何规则要从“实验”升级成“默认 CIS 规则”，至少应满足：

- 有足够样本与跨市场环境覆盖；
- 样本外方向一致；
- 结果不是由少数极端交易贡献；
- 成本后仍有价值；
- 对参数小幅变化不敏感；
- 能解释经济/行为机制，而不是纯数据挖掘；
- 若使用 LEAN，订单/费用/数据/执行假设足够接近拟采用的真实策略。

未满足时只能标记 `experimental`；LEAN 的 `research_quality` 仍保持 `unreviewed` 或审查后的受限状态，不能直接升级为生产规则。
