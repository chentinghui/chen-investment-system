# 陈氏投资系统：CIS 0.3 架构

CIS 0.3.0 的目标不是自己维护一整套通用投资 Agent，而是把成熟上游作为研究核心，把 CIS 收缩为稳定的个人投资控制层。

```text
用户
  ↓
陈氏投资系统 CIS
  ↓
CIS Control Layer
  ├─ Runtime Guard / GitHub main 校验
  ├─ 个人投资规则
  ├─ 证据门 / 前视偏差检查
  ├─ 八维统一评分
  ├─ 四层交易框架
  ├─ ETF/QDII 溢价纪律
  ├─ 组合数据门
  └─ 最终中文研究姿态
  ↓
TradingAgents（默认通用研究核心）
  ├─ Fundamentals Analyst
  ├─ Technical Analyst
  ├─ News Analyst
  ├─ Sentiment Analyst
  ├─ Bull / Bear Researchers
  ├─ Research Manager
  ├─ Trader
  ├─ Risk Management Team
  └─ Portfolio Manager → external_decision_candidate
  ↓
Anthropic Financial Services（按需专业增强）
  ├─ DCF
  ├─ Comps
  ├─ 3-Statement Model
  ├─ Earnings Preview / Analysis
  ├─ Model Audit / Update
  ├─ Competitive Analysis
  └─ Thesis / Catalyst
  ↓
结果回到 CIS
  ↓
证据审计 → 风险门 → 冲突解释 → CIS评分
  ↓
四层/ETF/组合门（如适用）
  ↓
最终中文结论 + 证伪条件 + 复盘计划
```

## 为什么这样拆分

- TradingAgents 由活跃团队维护通用多 Agent 投资工作流，CIS 不重复造轮子。
- Anthropic Financial Services 处理机构化专业模型，避免让通用 Agent 粗略替代 DCF/Comps/财报建模。
- CIS 只维护用户自己的长期规则、评分、风险纪律和最终输出，降低维护成本和版本漂移。

## CIS 自写 Agent 的定位

`plugins/chen-investment-system/agents/` 保留，但不再是默认股票研究团队：

- `fallback adapter`：TradingAgents 不可运行时兜底；
- `conflict validator`：外部核心之间出现关键冲突时复核；
- `CIS-specific adapter`：执行证据审计、四层交易、组合门等 CIS 特有规则。

不允许在 TradingAgents 正常运行时无理由重复跑同职责 Agent。

## 外部决策不是最终决策

TradingAgents Portfolio Manager 的输出一律标记：

```text
external_decision_candidate
```

它必须经过 CIS：

```text
证据审计
→ 风险门
→ 八维评分
→ 四层交易框架（如适用）
→ ETF/QDII 或组合门（如适用）
→ 最终研究姿态
```

## 关键文件

- 总入口：`plugins/chen-investment-system/skills/cis/SKILL.md`
- TradingAgents 适配：`plugins/chen-investment-system/skills/cis/references/tradingagents.md`
- 可执行适配器：`plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py`
- Anthropic 适配：`plugins/chen-investment-system/skills/cis/references/anthropic-financial-services.md`
- 系统流程：`plugins/chen-investment-system/skills/cis/references/system-workflow.md`
- 模块路由：`plugins/chen-investment-system/skills/cis/references/module-routing.md`
- Agent/Fallback 登记：`plugins/chen-investment-system/skills/cis/references/agent-registry.md`
- 评分引擎：`plugins/chen-investment-system/skills/cis/references/scoring-engine.md`
- 四层交易框架：`plugins/chen-investment-system/skills/cis/references/four-layer-trading-framework.md`
