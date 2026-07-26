# CIS 输入输出契约

## 输入规则

- 决策级研究必须有 `subject`、`research_question`、`mode` 和 `as_of`。
- 涉及持仓动作时，还必须有持仓、权重、成本、基准、约束和资金需求。
- 用户陈述不自动等于已核验事实。
- 所有市场敏感数字必须记录时间戳或报告期间。

## 模块返回格式

每个模块统一返回：

```text
module:
workflow:
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
confidence:
  evidence: high | medium | low
  thesis: high | medium | low
  valuation: high | medium | low | not_applicable
open_questions:
next_review:
```

## 内容类型

- **事实**：由具名来源直接支持。
- **计算**：列出方法、输入和单位。
- **假设**：结论成立所依赖但尚未成为事实的条件。
- **判断**：对事实、计算和假设的解释。
- **证伪条件**：一旦出现便要求降低或推翻论点的可观察事件。

## 适配规则

- 保留专业模块生成的报告或工作簿作为支持材料，但将结论转换成上述格式。
- `ready` 才能形成该模块的决策级结论；`limited` 必须说明不能回答什么；`blocked` 只输出缺失输入。
- `evidence` 必须保存来源和数据期间；不得把 Skill 名称当作市场事实的来源。
- Buffett 与数值模块意见不一致时，明确冲突属于资料、预测、估值输入、方法还是时间跨度。
- 不得机械平均置信度、情景概率或目标价。
