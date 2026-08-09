# CIS Market Regime Layer（0.4.3）

Market Regime Layer 用于描述当前市场环境，并决定**同一个股票信号需要多大确认度和风险折扣**。它不直接产生买卖动作，也不覆盖单公司基本面。

## Baseline 状态

- `risk_on`：趋势、广度、波动和信用环境总体支持风险资产；
- `neutral`：信号混合，维持常规确认要求；
- `risk_off`：趋势/广度恶化且波动或信用压力上升，提高安全边际和风险要求；
- `insufficient`：关键市场数据、覆盖或新鲜度不足。

## 输入纪律

必须有明确整体 `as_of`。布尔字段必须是真正 JSON boolean，禁止把字符串 `"false"` 当成布尔值。

0.4.3 新增 per-signal freshness：每个实际参与分类的信号都必须在 `signal_as_of` 中提供独立 `YYYY-MM-DD`。整体 `as_of` 不能代替每个数据点的真实日期。

示例：

```json
{
  "as_of": "2026-08-09",
  "signal_as_of": {
    "vix": "2026-08-09",
    "breadth_above_sma200_pct": "2026-08-09",
    "high_yield_oas_bps": "2026-08-08"
  }
}
```

当前 baseline 可使用：

1. `index_above_sma200`：大盘是否高于 200 日均线；
2. `sma50_slope_pct`：50 日均线斜率；
3. `breadth_above_sma200_pct`：市场广度；
4. `vix`：隐含波动率；
5. `realized_vol_20d`：20 日实现波动率；
6. `high_yield_oas_bps`：高收益信用利差绝对水平；
7. `credit_spread_change_bps_3m`：信用利差 3 个月变化。

只看信用利差变化不够，因此同时保留信用利差**绝对水平**。例如信用环境已经极端紧张，即使近三个月略有收窄，也不能简单判为 risk-on。

## Freshness baseline

`scripts/classify_market_regime.py` 使用保守的日历日新鲜度防线：

- 趋势/广度/VIX/实现波动率：最多 4 个日历日；
- 高收益 OAS / 信用利差变化：最多 14 个日历日。

这些只是防止明显陈旧数据混入“当前市场状态”的 baseline，不是最优预测参数。周末、节假日或数据提供方发布时间变化时，仍需解释实际数据口径。

以下情况不得输出正式 `risk_on / neutral / risk_off`：

- 已使用信号缺少 `signal_as_of`；
- 信号日期晚于整体 `as_of`；
- 任一已使用信号超过其 freshness baseline；
- coverage 不足或有效信号少于 3 个。

## Baseline 分类

`scripts/classify_market_regime.py` 使用加权规则而不是简单等权票决。只有 coverage、新鲜度和有效信号数量均满足要求时才输出正式 baseline regime，否则为 `insufficient`。

输出：

```text
as_of
regime
regime_score
raw_weighted_score
signals_used
coverage
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
- freshness tolerance 只用于阻止明显 stale 输入，不得包装成预测优势。
