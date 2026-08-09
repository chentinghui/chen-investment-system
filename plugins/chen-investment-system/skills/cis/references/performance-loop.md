# CIS Performance / Calibration Loop（0.4.2）

Performance Loop 用于回答：**CIS 过去的判断是否真的有区分度，哪些规则需要提高/降低权重。**

它不允许直接根据短期历史表现自动改写 CIS 规则。

## Prediction Ledger

0.4.2 新增：

```text
scripts/prediction_ledger.py
runtime/evaluations/predictions.jsonl
```

Ledger 采用 append-only event 模式：

```text
prediction event
  ↓
历史快照不可改写
  ↓
outcome event
  ↓
按 research_id 合并评估
```

禁止在结果已知后修改原始预测快照来“提高历史命中率”。同一 `research_id` 只能有一个 prediction 和一个 outcome。

## Prediction 最低字段

```text
research_id
as_of
ticker
cis_version
cis_score / score_status
research_posture
horizon_days
benchmark
dimension_scores
quant_score（如有）
regime（如有）
thesis_falsifiers
```

到达评估日后，追加 outcome event：

```text
research_id
evaluation_as_of
realized_return
benchmark_return
max_drawdown_during_horizon
falsifier_triggered
outcome_note
```

市场价格/基准数据仍必须来自可审计数据源；Ledger 负责不可篡改记录与结算契约，不自行发明行情。

## 核心评估

`scripts/evaluate_cis_predictions.py` 现在至少评估：

- CIS 分数分桶后的平均未来收益；
- 分桶后的平均超额收益；
- 高分到低分是否具有合理单调性；
- 不同 Market Regime 下是否稳定；
- **不同 horizon_days 下是否稳定**，避免把 30 天和 365 天结果混为一个总体结论；
- 各八维 dimension score 与未来收益/超额收益的相关诊断；
- 最大回撤与 falsifier 触发率（有数据时）。

## 权重调整纪律

任何评分权重/阈值调整必须：

1. 有足够独立样本；
2. 明确区分训练期、验证期与样本外期；
3. 说明调整前后表现；
4. 检查是否只是适配单一市场阶段；
5. 检查不同投资期限/行业的稳定性；
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

这样历史研究可以按当时版本复盘，禁止用今天的新规则假装当时已经知道。

Performance Loop 是 CIS 从“专家规则系统”升级为“可校准系统”的关键，但**校准 ≠ 自动机器学习改权重**。
