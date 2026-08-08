# CIS Agent Layer

本目录保存陈氏投资系统（CIS）的专家 Agent 角色契约。设计上借鉴 `msitarzewski/agency-agents` 的优秀结构：**明确身份、核心使命、关键规则、具体交付物、重复可执行的工作流、交接协议与成功指标**；投资方法、评分权重、风险规则和中文输出均由 CIS 自行定义。

## 角色

- `chen-chief-investment-analyst.md`：总控 Agent，唯一拥有最终 CIS 研究结论。
- `fundamental-financial-analyst.md`：基本面与财务质量。
- `growth-competitive-analyst.md`：成长、行业结构与竞争优势。
- `valuation-analyst.md`：估值、隐含预期与情景。
- `technical-market-analyst.md`：趋势、价格、成交与市场结构。
- `macro-catalyst-strategist.md`：宏观传导、催化剂与事件路径。
- `positioning-flow-analyst.md`：机构持仓、资金流、拥挤度与定位。
- `risk-manager.md`：下行机制、脆弱性、证伪条件与风险覆盖。
- `evidence-auditor.md`：独立证据/逻辑质量门。
- `portfolio-manager.md`：在组合数据完整时评估仓位与组合后果。

## 运行原则

1. 总控只调度会改变结论或验证关键输入的最少专家。
2. 专家 Agent 不直接取代 Skill；Agent 负责“谁来判断、如何交付”，Skill/工作流负责“具体能力和工具”。
3. 专家统一按 `skills/cis/references/agent-contract.md` 返回。
4. 总控按 `skills/cis/references/scoring-engine.md` 统一评分，但评分不得越过证据门、风险门、四层交易框架或组合数据门。
5. 专家之间出现冲突时，不投票、不机械平均；由总控定位冲突来源并保留少数意见。
