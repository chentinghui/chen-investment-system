# CIS Performance / Calibration Loop

Performance Loop 用于回答：**CIS 过去的判断是否真的有区分度，哪些规则需要提高/降低权重。**

它不允许直接根据短期历史表现自动改写 CIS 规则。

## 每次研究建议记录

```text
research_id
as_of
ticker
mode
cis_score / score_status
quant_score（如有）
regime（如有）
research_posture
horizon_days
thesis_falsifiers
benchmark
```

到达评估日后补充：

```text
realized_return
benchmark_return
max_drawdown_during_horizon
falsifier_triggered
outcome_note
```

## 核心评估

- CIS 分数分桶后的平均未来收益；
- 分桶后的平均超额收益；
- 高分到低分是否具有合理单调性；
- 不同 Market Regime 下是否稳定；
- 不同行业/市值是否存在系统偏差；
- 推荐姿态的方向命中率；
- 主要误判来源：估值、基本面、催化剂、技术、风险或数据时点。

## 权重调整纪律

任何评分权重/阈值调整必须：

1. 有足够独立样本；
2. 明确区分训练期与样本外期；
3. 说明调整前后表现；
4. 检查是否只是适配单一市场阶段；
5. 由人工/ChatGPT 审查后修改规则文件，禁止脚本自动覆盖生产权重。

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

## 确定性工具

`scripts/evaluate_cis_predictions.py` 对历史预测 CSV 做分桶统计、平均收益、超额收益和命中率计算。

Performance Loop 是 CIS 从“专家规则系统”升级为“可校准系统”的关键，但**校准 ≠ 自动机器学习改权重**。
