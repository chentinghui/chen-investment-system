# CIS Agent 统一交接契约（0.4.2）

所有专家 Agent / 方法论角色必须返回可审计结构，方便总控比较、质量门和评分。

```text
agent:
role:
task:
capability_status: installed | unavailable
runtime_readiness: ready | limited | blocked
execution_status: not_applicable | not_run | success | error
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
3. `runtime_readiness != ready` 时，候选分只能 provisional；关键输入缺失时用 `not_available`。
4. 专家必须把“事实、计算、假设、判断”分开。
5. Evidence Audit 与 Risk Review 均采用 fail-closed：未明确 `pass` 时不得输出 `decision_grade`。
6. `risk_override=block`、关键数据 `blocked` 或 Critical Dimension 缺失时，总控不得输出决策级评分/动作。
7. 所有外部市场敏感数字必须带日期/期间。
8. Original TradingAgents 的 `execution_status=success` / `remote_ready` 只能证明程序执行完成；默认 `evidence_audit_status=not_run`、`research_quality=unreviewed`，不得冒充研究质量通过。
