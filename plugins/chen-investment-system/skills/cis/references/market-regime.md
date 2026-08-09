# CIS Market Regime Layer

Market Regime Layer 用于描述当前市场环境，并决定**同一个股票信号需要多大确认度和风险折扣**。它不直接产生买卖动作，也不覆盖单公司基本面。

## Baseline 状态

- `risk_on`：趋势、广度、波动和信用环境总体支持风险资产；
- `neutral`：信号混合，维持常规确认要求；
- `risk_off`：趋势/广度恶化且波动或信用压力上升，提高安全边际和风险要求；
- `insufficient`：关键市场数据不足。

## Baseline 输入

至少使用其中 3 类，且必须有明确 `as_of`：

1. 大盘趋势：指数相对 200 日均线、50 日均线斜率；
2. 市场广度：成分股高于 200 日均线比例等；
3. 波动：VIX/实现波动及变化；
4. 信用/流动性：信用利差变化；
5. 宏观政策：利率/流动性方向，只作解释变量，不单独决定 regime。

## 对 CIS 的影响

Regime 不直接修改公司基本面分数。允许的作用仅包括：

- 调整 `catalyst_macro` 与 `risk_resilience` 的证据判断；
- 对买入价安全边际、分批节奏和确认条件提出更严格/更宽松要求；
- 在横截面 Quant 筛选中做条件化回测；
- 解释为什么相同公司在不同市场环境下交易计划不同。

不得简单规定“risk_off = 全部卖出”或“risk_on = 全部买入”。

## 确定性 baseline 分类

`scripts/classify_market_regime.py` 提供透明的规则基线。规则必须标记为 `experimental`，直到经过多周期回测校准。

输出：

```text
as_of
regime
regime_score
signals_used
coverage
status
```

## 防过拟合

- 阈值变化必须经过样本外验证；
- 不允许针对某次历史危机倒推参数；
- 不允许把单一 VIX 数值当作完整市场状态；
- 不把宏观叙事替代价格/广度/信用的实际证据。
