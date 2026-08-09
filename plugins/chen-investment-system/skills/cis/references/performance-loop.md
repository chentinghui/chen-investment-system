# CIS Performance / Calibration Loop（0.4.5）

Performance Loop 用于回答：**CIS 过去的判断是否真的有区分度，哪些规则需要提高/降低权重。**

它不允许直接根据短期历史表现自动改写 CIS 规则，也不属于日常单股分析 Core。

## Prediction Ledger

可选工具位于：

```text
extensions/research_tooling/prediction_ledger.py
extensions/research_tooling/record_cis_research.py
runtime/evaluations/predictions.jsonl
```

Ledger 采用 append-only event 模式：

```text
prediction event
  ↓
历史快照不可改写
  ↓
多个 outcome event（按 research_id + horizon 唯一）
```

同一 `research_id` 只能有一个 prediction；同一 `(research_id, horizon_trading_days)` 只能有一个 outcome。禁止在结果已知后修改原始预测快照来“提高历史命中率”。

## 公共数据安全

公开 Ledger 使用结构化 allowlist，不再使用“只屏蔽几个敏感字段”的 blacklist。任意未批准字段（例如 `notes/account/shares/cost_basis/position_size`）直接拒绝。

即使字段名在 allowlist 中，也不得放原始聊天、账号信息或个人持仓说明。个人组合记录应进入私有数据层，而不是公开 calibration ledger。

## 默认观察周期

```text
5 / 20 / 60 trading days
```

这些是同一个 research 的**相关结果**，不是三个独立实验。

因此：

- 5D、20D、60D 的相关性/IC 必须按 horizon 分开计算；
- 不得把三个 horizon 混在一起算一个总体 `score_return_correlation`；
- 样本门槛优先按 unique `research_id`，而不是 outcome 行数；
- 100 个 outcomes 如果只来自 34 次研究，不得称为 100 个独立样本。

## Settlement 当前语义

`settle_due_predictions.py` 仍是 experimental。0.4.5 明确：

```text
entry = research date 之后第一个 benchmark session 的 adjusted close
exit  = 对应 horizon benchmark session 的 adjusted close
return_semantics = next_session_close_to_close_adjusted_price_return
```

它**不是 next-open 可执行策略收益**，也不是实际成交 P&L。Yahoo Adjusted Close 缺失时不再静默 fallback 到 raw close；数据口径不完整保持 unresolved。

退市、破产、现金/股票并购等 terminal event 规则尚未实现；缺少对应终值时必须保持 `unresolved`，不得 forward-fill 或偷偷使用后续可得价格。正式做 alpha/胜率校准前必须补齐这部分，避免 settlement/survivorship bias。

MFE/MAE 当前仍为 `adjusted_close_only` 路径指标，不是日内 High/Low excursion。

## 核心评估

`evaluate_cis_predictions.py` 当前至少按每个 horizon 分别评估：

- CIS 分数与未来收益/超额收益的相关性；
- score bucket；
- Regime / Sector；
- 八维 dimension score 的 Pearson / Spearman 诊断；
- outcome_count 与 unique research sample count。

当输入混合多个 horizon 时，顶层 pooled correlation 必须为空，使用 `horizon_diagnostics` 查看各期限结果。

## 样本纪律

基线：

```text
unique research < 30      → insufficient_sample
30–99                     → exploratory_sample
>=100 且 research_id 可验证 → calibration_candidate
>=100 但 research_id 缺失 → exploratory_independence_unverified
```

即使达到100，还必须检查 ticker、sector、entry week、regime 的聚类与集中度。重复分析同一股票或同一市场阶段不能等价于100个独立实验。

## 权重调整纪律

任何评分权重/阈值调整必须：

1. 有足够独立样本；
2. 明确区分训练期、验证期与样本外期；
3. 说明调整前后表现；
4. 检查是否只是适配单一市场阶段；
5. 检查不同 horizon / 行业 / Regime 的稳定性；
6. 由人工/ChatGPT 审查后修改规则文件，禁止脚本自动覆盖生产权重。

## 版本化

每次规则变化都要记录：

```text
old_version
new_version
change_reason
evidence_window
out_of_sample_result
changed_weights_or_thresholds
```

Performance Loop 是可选研发能力；**校准 ≠ 自动机器学习改权重**，也不得因为 Extension 不成熟影响 CIS Core 日常分析。
