# CIS Quant Factor Ranking Engine（0.4.2）

Quant 层的职责是：**从大股票池中系统化筛选“谁值得先研究”**。它不是最终买卖引擎，也不自动产生 CIS 动作。

当前 baseline 状态：`experimental_uncalibrated`。

## 定位

```text
Point-in-time Universe
  ↓
可比因子数据
  ↓
横截面 percentile ranking
  ↓
quant_score + factor_coverage
  ↓
Top N
  ↓
ChatGPT-native TradingAgents Methodology
  ↓
CIS 最终质量门
```

`quant_score` 与 `cis_score` 严格分开，不允许直接平均或换算。

## 默认 baseline 因子

- momentum_6m
- momentum_12m_ex1m
- revenue_growth
- eps_growth
- fcf_margin
- roe
- earnings_revision_90d
- valuation_fcf_yield
- relative_strength
- volatility
- max_drawdown_1y

权重只用于未校准 baseline，必须通过回测与 Performance Loop 持续验证。

## Point-in-time / As-of 强制规则

同一次横截面排名的所有股票必须共享**完全相同的 `as_of`**。代码 `validate_as_of()` 会拒绝：

- 缺少 `as_of` 的行；
- 不同日期混在同一横截面中的输入。

这用于避免把不同信息时点的股票直接混排。

## Max Drawdown 输入合同

金融数据常把最大回撤写成负数，例如 `-0.35`；有些数据源写成正的损失幅度 `0.35`。

0.4.2 默认：

```text
max_drawdown_1y → abs(value) → 越小越好
```

因此 `-0.10` 会优于 `-0.50`，不会出现“回撤更深反而得分更高”的符号错误。

## 缺失值与覆盖率

- 缺失因子不补零；
- `factor_coverage < 70%` → `insufficient`；
- 70%–<85% → `provisional`；
- >=85% → `ready`，但仍只是 Quant 候选，不是 CIS 决策级结论。

## 数据要求与能力边界

当前脚本是**Quant Factor Ranking Engine**，不是完整 Data Engine。调用方仍需提供：

- point-in-time 历史股票池；
- 调整后的价格序列；
- 当时可得的财报/预期数据；
- 退市/被并购标的（回测时）；
- 一致的字段定义与单位。

因此“从数千只股票自动选 Top20”的完整生产能力仍取决于 point-in-time 数据管线，不能把排名函数夸大为完整机构级量化平台。

## 与 Backtest 的关系

任何因子、权重、阈值要升级为默认生产规则，必须先通过 `backtest-validation.md`：

- look-ahead / survivorship / universe drift / restatement leakage；
- 按换手率计算交易成本；
- train / validation / out-of-sample；
- 参数稳定性与经济机制。

## 输出合同

```text
engine = cis_quant_factor_ranking
status = experimental_uncalibrated
universe
as_of
factor_config
results[]:
  ticker
  as_of
  quant_score
  factor_coverage
  status
  factor_scores
```

Quant 负责“先研究谁”，TradingAgents 方法论负责“为什么”，CIS 负责最终证据、风险、评分和交易纪律。
