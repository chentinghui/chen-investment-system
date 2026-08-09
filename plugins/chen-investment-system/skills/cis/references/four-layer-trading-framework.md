# CIS 四层结构与双向卖出规则

## 适用范围

当用户询问股票、ETF 或指数的买入、持有、加仓、减仓、止盈、止损、退出或具体价位时，必须执行本规则。对英伟达（NVDA）、QQQ 和纳斯达克100的分析，默认强制使用本规则。

本规则用于组织技术面和持仓动作，不替代基本面、估值、宏观、事件和组合风险研究。

## 固定分析顺序

严格按照以下顺序分析，不得颠倒或跳过：

1. **趋势层**：20日、50日、200日均线，均线排列、斜率和价格所处位置；判断上涨、震荡、修复或下跌趋势。
2. **价格层**：前高、前低、突破位、缺口、整数关口、箱体边界及关键支撑压力区；使用价格区域，不制造精确到小数点的虚假确定性。
3. **成交层**：成交密集区、相对20日平均成交量、放量突破、缩量回调、高位放量滞涨、放量破位和量价背离；盘中成交量必须注明尚未收盘，不能直接与全天均量等同。
4. **风险层**：持仓成本、数量、权重、集中度、最大可承受回撤、资金需求、分批买卖比例和动作失效条件。

核心顺序：

> 先看趋势决定持有方向，再看价格寻找位置，再看成交确认真假，最后用风险层决定仓位。

## Tactical Price / Session Guard

短线交易涉及“当前价”时，必须同时登记：

```text
analysis_timestamp
quote_timestamp
exchange: XNAS | XNYS
market_session: premarket | regular | afterhours | closed
price_type: premarket | live | afterhours | last_close
current_price
quote_max_age_seconds（活跃交易时段）
quote_session_date（closed / last_close）
```

`market_session` 不是调用者可以随意声明的标签。`scripts/tactical_setup_gate.py` 必须根据 `analysis_timestamp + exchange` 的美东交易日历/时段基线自行推导 session；若调用者提供的 `market_session` 与推导结果冲突，直接拒绝。

语义必须匹配：

- `premarket` → `premarket`；
- `regular` → `live`；
- `afterhours` → `afterhours`；
- `closed` → `last_close`。

活跃时段报价必须通过 freshness gate；调用者必须声明该行情源允许的 `quote_max_age_seconds`，且 Core baseline 不允许把超过 3600 秒的报价包装成活跃时段当前价。`closed` 状态必须标明 `quote_session_date`，且只能引用最近一个已完成交易日的正式收盘。

当前 stdlib 日历基线覆盖 XNAS/XNYS 的常规周末、主要完整休市日以及常见提前收盘日；特殊临时休市仍由 Evidence Layer 额外核验，不能把代码基线包装成交易所官方实时日历。

## Tactical Risk / Reward Gate

对 `decision_context=tactical` 或任何明确短线做差价的买入问题，CIS Quality Score 与“现在是否是好交易”必须分开。至少给出：

```text
Entry Zone
Chase Limit（如适用）
Stop / Invalidation
Stop Type
Target 1
Target 2（如适用）
Reward / Risk
```

确定性基线按允许买入区间的**最差 Target 1 R/R**分类：

- `< 1.0` → `reject`；
- `1.0–<1.5` → `weak_setup`；
- `1.5–<2.0` → `acceptable`；
- `>=2.0` → `attractive`。

这些阈值是交易纪律 baseline，不是已经校准的最优参数。

### Stop / Invalidation 语义

`stop_type` 必须明确：

```text
hard_price
close_confirmation
technical_invalidation
```

- `hard_price`：价格触及/越过 Stop 即视为原 setup 失效；
- `close_confirmation`：盘中越过 Stop 先进入 `blocked_pending_stop_confirmation`，只有收盘确认后才失效；
- `technical_invalidation`：需要额外技术失效确认，未确认前也不得继续给出新的入场资格。

对非 `hard_price`，调用者必须明确 `stop_confirmation_met=true/false`，不得让代码猜测。

### Setup 生命周期

旧交易计划不能无限有效：

- 当前价已经越过 hard Stop，或确认型 Stop 已满足确认 → `invalidated_reprice_required`；
- 当前价已经到达/越过 Target 1 → `setup_expired_reprice_required`；
- 越过 Chase Limit → `blocked_do_not_chase`；
- 未进入 Entry Zone → `wait_for_entry`；
- Stop 已盘中越过但确认未完成 → `blocked_pending_stop_confirmation`。

Long 的 Chase Limit 必须满足 `entry_high <= chase_limit < target1`；Short 必须满足 `target1 < chase_limit <= entry_low`。不得出现 Chase Limit 已经越过 Target 1 的无意义计划。

## 双向卖出原则

卖出分析必须同时覆盖盈利止盈和防守止损，不得只给亏损后的卖点。

> **上涨时看压力、估值和量价异常，决定在哪里分批止盈；下跌时看支撑和趋势是否破坏，决定在哪里止损。**

### 盈利止盈

盈利止盈属于主动兑现和风险再平衡，不等于判断标的已经见顶。至少检查：

- 是否到达前高、箱体上沿、历史密集成交区或其他重大压力区；
- 估值是否显著超过自身历史、同业或基本面可支持区间；
- 是否出现高位放量滞涨、长上影、假突破、动能背离或利好兑现后不涨；
- 短期涨幅是否过快、价格是否显著远离20日均线；
- 盈利后仓位是否被动膨胀并超过组合风险预算。

盈利止盈默认采用分批方式。只有持仓背景充分时才给具体比例；常用参考为第一止盈区10%—20%、第二止盈区20%—30%，剩余仓位继续跟随趋势。若趋势、估值和量价均健康，可以选择不卖。

不得仅因为“已经盈利”“涨幅较大”或达到任意固定收益率就机械建议卖出。

### 防守止损

防守止损用于原判断失效或风险超限。至少检查：

- 是否跌破关键突破位、前低或重要成交密集区；
- 是否有效跌破50日或200日均线并无法快速收回；
- 是否放量破位，而不是正常缩量回调；
- 基本面、业绩指引、行业需求或原始投资逻辑是否恶化；
- 组合集中度、杠杆或资金需求是否迫使降低风险。

不得把盘中短暂跌破自动视为有效破位。优先使用收盘确认、连续确认或“价格 + 成交量 + 基本面”组合证据；这也是 `stop_type` 必须显式记录的原因。

## 强制输出字段

对买卖价位或持仓复盘，输出必须同时包含：

1. 当前价格、`price_type`、exchange/session 与资料截止时间；
2. 趋势层结论；
3. 关键支撑、压力和成交确认条件；
4. **继续持有区**；
5. **第一盈利止盈区**及可选卖出比例；
6. **第二盈利止盈区**及可选卖出比例；
7. **回调观察区**；
8. **防守卖出线**及 `stop_type`；
9. **基本面失效条件**；
10. 最终动作及其成立条件。

对短线买入还必须额外给出 Entry Zone、Chase Limit（如适用）、Stop、Stop Type、Target 1/2、R/R、Setup State 和 Tactical Gate 状态。

若资料不足以支持具体价位或比例，必须明确标记“证据不足”或给条件区间，不得猜测。

## 动作解释

- `继续持有区`：趋势和逻辑正常，不需要操作。
- `盈利止盈区`：允许分批兑现，但不是必须卖出；必须说明触发依据。
- `回调观察区`：出现调整但尚未破坏趋势，不应机械止损。
- `防守卖出线`：趋势、量价或基本面失效后降低仓位或退出。
- `blocked_do_not_chase`：赔率或价格位置不支持追价，不等于看空公司。
- `wait_for_entry`：研究逻辑可继续观察，但当前价格没有进入计划区。
- `invalidated_reprice_required`：原交易计划已失效，禁止沿用旧 Entry/Target。
- `setup_expired_reprice_required`：旧 Target 已经实现/越过，需要重新建计划。
- `blocked_pending_stop_confirmation`：价格已触发确认区，但失效确认尚未完成，暂不开放新入场判断。

最终结论必须区分“可以卖”“建议卖”“必须卖”和“暂不卖”，避免把可选风险管理方案写成强制交易指令。
