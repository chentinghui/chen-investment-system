# CIS Market Regime Layer（0.4.3）

Market Regime Layer 用于描述当前市场环境，并决定**同一个股票信号需要多大确认度和风险折扣**。它不直接产生买卖动作，也不覆盖单公司基本面。

## Baseline 状态

- `risk_on`：趋势、广度、波动和信用环境总体支持风险资产；
- `neutral`：信号混合，维持常规确认要求；
- `risk_off`：趋势/广度恶化且波动或信用压力上升，提高安全边际和风险要求；
- `insufficient`：关键市场数据、fresh coverage 或有效信号数量不足。

## Regime Profile

0.4.3 hardening 要求显式 `regime_profile`，避免不同人用不同指数/广度口径却得到同一个“Regime”。当前确定性 baseline：

```text
us_broad_v1
- trend proxy: SPY
- breadth universe: S&P 500

us_nasdaq_v1
- trend proxy: QQQ
- breadth universe: Nasdaq-100
```

统一指标定义：

```text
sma50_slope_pct
= 50日SMA相对20个交易日前50日SMA的百分比变化

realized_vol_20d
= 20个交易日收盘到收盘简单收益率的样本标准差 × sqrt(252) × 100
```

如果数据源采用不同定义，不能直接塞入本分类器；应先转换到对应 profile 口径或输出 `insufficient`。

## 输入纪律

必须有明确整体 `as_of`。布尔字段必须是真正 JSON boolean；数字字段也不得接受 JSON boolean，例如 `vix=true` 必须拒绝，不能被 Python 隐式转换成 `1.0`。

每个实际提供的信号都必须在 `signal_as_of` 中提供独立 `YYYY-MM-DD`。整体 `as_of` 不能代替每个数据点的真实日期。

当前 baseline 可使用：

1. `index_above_sma200`：profile 指定的趋势代理是否高于 200 日均线；
2. `sma50_slope_pct`：按上方固定公式计算的 50 日均线斜率代理；
3. `breadth_above_sma200_pct`：profile 指定 universe 中高于200日均线的成分股比例；
4. `vix`：VIX；
5. `realized_vol_20d`：按上方固定公式年化；
6. `high_yield_oas_bps`：高收益信用利差绝对水平；
7. `credit_spread_change_bps_3m`：信用利差 3 个月变化。

## Freshness baseline

`scripts/classify_market_regime.py` 使用保守的日历日新鲜度防线：

- 趋势/广度/VIX/实现波动率：最多 4 个日历日；
- 高收益 OAS / 信用利差变化：最多 14 个日历日。

这些只是防止明显陈旧数据混入“当前市场状态”的 baseline，不是最优预测参数。

0.4.3 hardening 不再因为**一个** stale/missing-dated 信号就让整个 Regime 失效。处理顺序改为：

```text
已提供信号
  ↓
检查 signal_as_of
  ↓
missing / stale → 从本次分类中排除并登记 excluded_signals
  ↓
只用 fresh signals 重新计算 coverage
  ↓
fresh coverage >= 60% 且 fresh signals >= 3
  → 允许 experimental_baseline 分类
否则
  → insufficient
```

因此：

- 有 1 个 stale VIX，但其余 fresh 信号覆盖仍足够 → 可以分类，同时 `freshness_status=partial`；
- stale/missing 太多导致 fresh coverage 不足 → `insufficient_freshness`；
- 未来日期仍直接拒绝输入，不能通过“排除”绕过前视偏差。

## Baseline 分类

`scripts/classify_market_regime.py` 使用加权规则。输出：

```text
as_of
regime_profile
profile_definition
regime
regime_score
raw_weighted_score
signals_used
excluded_signals
coverage              # fresh coverage
observed_coverage     # 所有已提供信号权重覆盖
freshness_status
missing_signal_dates
stale_signals
status
```

阈值仍标记 `experimental_baseline`，需要跨周期样本外验证。

## 对 CIS 的影响

Regime 不直接修改公司基本面分数。允许的作用仅包括：

- 调整 `catalyst_macro` 与 `risk_resilience` 的证据判断；
- 对买入价安全边际、分批节奏和确认条件提出更严格/更宽松要求；
- 在横截面 Quant 筛选中做条件化回测；
- 解释为什么相同公司在不同市场环境下交易计划不同。

不得简单规定“risk_off = 全部卖出”或“risk_on = 全部买入”。

## 防过拟合

- 阈值变化必须经过样本外验证；
- 不允许针对某次历史危机倒推参数；
- 不允许把单一 VIX 数值当作完整市场状态；
- 不把宏观叙事替代价格、广度、波动和信用的实际证据；
- freshness tolerance 只用于阻止明显 stale 输入，不得包装成预测优势；
- profile 变化必须显式记录，不得把 `us_broad_v1` 与 `us_nasdaq_v1` 的结果混为同一口径。
