# CIS 证据与置信度（0.4.3）

## 来源级别

- **A 级**：监管申报、交易所/基金公司正式资料、经审计财报、官方公告。
- **B 级**：公司投资者资料、业绩发布、管理层原始讲话、权威政府或行业数据。
- **C 级**：可靠市场数据商、主流财经媒体、方法透明的第三方研究。
- **D 级**：聚合页面、二手摘要、社交媒体、未披露方法的估算。

A/B 级优先；C 级用于补充或市场背景；D 级只能形成线索，不得单独支持决策级结论。

## 三类置信度

- **Evidence confidence**：来源质量、覆盖、新鲜度和一致性。
- **Thesis confidence**：论点因果链、可证伪性和反方证据。
- **Valuation confidence**：预测可见度、方法适用性和关键敏感度。

## Evidence Freshness Guard

短线分析中的“资料可靠”不仅要求来源正确，还要求时间口径匹配。以下资料必须明确 `as_of` / `published_at` / `retrieved_at`，不能把没有时间戳的数据当成当前状态：

- Price / Volume：当前交易 session 的可验证报价，或明确标记为最近正式收盘；
- Technical：均线、成交量、波动率等必须使用与价格结论一致的数据截止时间；
- Breaking News / Catalyst：必须检查当前最新公开信息，旧新闻只能作为背景；
- Earnings / Guidance：使用最近一次正式披露，并明确对应报告期；
- Macro：使用最近一次正式发布值，并标明发布日期；
- 13F / 机构持仓：允许披露滞后，但必须明确报告期和披露延迟，不得描述为实时仓位。

对 `decision_context=tactical`，若价格/成交/技术关键证据的数据截止时间不清楚，或关键催化剂检查没有完成，Evidence Audit 不得 `pass`。

### Tactical quote freshness

短线“当前价”还必须满足：

```text
exchange
analysis_timestamp
quote_timestamp
market_session
price_type
quote freshness policy
```

`market_session` 必须由 exchange + timestamp 的交易时段基线验证，不能只相信调用者字符串。活跃时段报价必须有显式允许的最大 age；超过该 age 时 Price Context 直接失败。`last_close` 只能称为“最近收盘参考价”，且 `quote_session_date` 必须对应最近已完成交易日。

`scripts/tactical_setup_gate.py` 负责确定性语义检查。特殊临时休市、交易所异常或供应商延迟仍需 Evidence Layer 依据交易所/数据商资料核验；代码日历不能冒充官方实时交易日历。

## Fail-Closed Audit

Evidence Audit 默认状态不是 `pass`，而是 `unverified`。只有实际检查完成且关键结论的来源、`as_of`、口径和冲突均满足要求后，才能明确写为 `pass`。

以下情况不得 `pass`：

- 关键事实没有可追溯来源；
- 关键市场/财务数据截止时间不明；
- 短线关键行情、技术或催化剂证据的新鲜度未确认；
- 活跃时段报价超过声明 freshness policy，或 session/price_type 与交易所时间冲突；
- 历史研究存在未来信息泄漏；
- 冲突证据尚未解释；
- 关键估值输入只是模型猜测；
- Original TradingAgents 虽然执行成功，但报告中的事实尚未逐项审计。

## 评级规则

- `high`：关键结论由当前、直接且相互一致的 A/B 级证据支持，没有未解决的重大缺口。
- `medium`：核心方向有支持，但存在资料覆盖、时间、口径或预测不确定性。
- `low`：依赖间接来源、关键假设、陈旧资料或未解决冲突。

综合置信度不得高于三类中与最终结论最相关的最低等级。

## 证据登记字段

```text
source_id:
source_name:
source_grade: A | B | C | D
published_at:
period_or_as_of:
retrieved_at:
fact:
limitation:
conflict:
```
