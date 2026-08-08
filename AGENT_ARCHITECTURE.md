# 陈氏投资系统：Agent 架构

CIS v2 的目标结构是：

```text
用户
  ↓
陈氏投资分析师（总控 Agent）
  ↓
最小专家团队
  ├─ 基本面与财务
  ├─ 成长与竞争
  ├─ 估值
  ├─ 技术与市场结构
  ├─ 宏观与催化剂
  ├─ 定位与资金流
  ├─ 风险经理
  ├─ 证据审计员
  └─ 组合与仓位（仅组合数据门满足）
  ↓
Skills / 外部工作流 / 数据
  ↓
证据门 + 风险门 + 冲突处理
  ↓
CIS 统一评分引擎（0–100）
  ↓
四层交易框架 / 组合约束（如适用）
  ↓
最终中文研究结论 + 证伪条件 + 复盘计划
```

## 从 agency-agents 借鉴的设计原则

CIS 只迁移 Agent 设计方法，不复制其角色内容：

1. 每个 Agent 有明确身份和职责边界。
2. 每个 Agent 有核心使命与不可违反的关键规则。
3. 每个 Agent 必须产出具体、可检查的交付物。
4. 每个 Agent 使用重复可执行的工作流。
5. 每个 Agent 有成功指标，而不是只写“扮演某专家”。
6. 总控通过交接契约协调专家，并使用独立质量门处理失败与冲突。

`agency-agents` 当前公开仓库采用 MIT License；本仓库的 Agent 文本与投资方法为 CIS 原创实现。

## 关键文件

- Agent 角色：`plugins/chen-investment-system/agents/`
- Agent 登记：`plugins/chen-investment-system/skills/cis/references/agent-registry.md`
- 编排协议：`plugins/chen-investment-system/skills/cis/references/agent-orchestration.md`
- 交接契约：`plugins/chen-investment-system/skills/cis/references/agent-contract.md`
- 评分引擎：`plugins/chen-investment-system/skills/cis/references/scoring-engine.md`
- 可执行评分器：`plugins/chen-investment-system/skills/cis/scripts/score_cis.py`
