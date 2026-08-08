# CIS Agent 统一交接契约

所有专家 Agent 必须返回同一结构，方便总控比较、审计和评分。

```text
agent:
role:
task:
capability_status: installed | unavailable
runtime_readiness: ready | limited | blocked
as_of:
data_cutoff:
findings:
evidence:
calculations:
assumptions:
risks:
thesis_falsifiers:
conflicts:
score_contribution:
  dimension: fundamentals | growth | valuation | industry_competitive | technical | catalyst_macro | positioning | risk_resilience | not_applicable
  score: 0-100 | not_available
  rationale:
  evidence_coverage: 0-100
confidence:
  evidence: high | medium | low
  thesis: high | medium | low
  valuation: high | medium | low | not_applicable
handoff_to:
open_questions:
next_review:
```

## 交接规则

1. `score_contribution` 是候选分，不是最终 CIS 总分。
2. 同一维度若多个专家给分，总控不得直接平均；先解释输入、方法、期限差异，再确定采用值或范围。
3. `runtime_readiness != ready` 时，候选分只能标为 provisional；关键输入缺失时用 `not_available`。
4. 专家必须把“事实、计算、假设、判断”分开。
5. 风险经理的 `risk_override=block` 或审计员 `audit_status=unresolved` 时，总控不得输出决策级评分/动作。
6. 所有外部市场敏感数字必须带日期/期间。
