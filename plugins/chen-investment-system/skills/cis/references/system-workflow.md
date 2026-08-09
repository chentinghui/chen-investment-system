# CIS 0.3 系统流程

## 0. Runtime Guard

当用户明确调用“陈氏投资系统”“投资总控”“用我的投资系统分析”或等价表达时：

1. 先读取当前 CIS `SKILL.md` 与必读 references。
2. 若当前环境可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 的 `main`；不得凭聊天记忆恢复旧流程或旧权重。
3. 读取 `tradingagents.md`；股票/上市公司任务默认先检查 TradingAgents 本次可执行状态。
4. 读取 `anthropic-financial-services.md`；专业金融子问题按需路由 Anthropic。
5. 只有实际执行成功的外部模块才能记录为本次运行结果。

## 1. 任务受理

识别对象、研究问题、市场、模式、期限、`analysis_date/as_of` 和用户资料。只询问会改变路线或结论的缺失信息。

## 2. 个人规则

读取 `investor-profile.md`。未设置项保持为空；只有用户明确要求保存或修改时才能写入。

## 3. 能力与数据预检

分别检查：

- TradingAgents：包是否可导入、模型 provider、API key、数据 provider、目标市场、历史日期防前视。
- Anthropic Financial Services：目标 Skill 是否可读取/有验证快照，关键输入是否完整。
- CIS 内置：评分器、四层交易框架、ETF/QDII规则、组合数据门。

所有模块给出 `ready`、`limited` 或 `blocked`，并记录外部核心的更具体状态。

## 4. 证据登记

按 `evidence-confidence.md` 登记来源级别、发布日期、资料期间、提取日期、事实、限制和冲突。

TradingAgents 的输出不是天然 A/B 级证据；其中引用的行情、新闻、财务和情绪数据必须按实际来源重新评级。

## 5. 默认通用研究核心：TradingAgents

股票/上市公司任务在 TradingAgents `installed_ready` 时默认执行：

```text
Fundamentals Analyst
+ Technical Analyst
+ News Analyst
+ Sentiment Analyst
        ↓
Bull / Bear Researchers
        ↓
Research Manager
        ↓
Trader
        ↓
Risk Management Team
        ↓
Portfolio Manager
        ↓
external_decision_candidate
```

该候选决策不得直接对用户发布为 CIS 最终动作。

## 6. 专业金融子问题：Anthropic Financial Services

出现以下需求时，按 `anthropic-financial-services.md` 调最小匹配 Skill：

- DCF / Comps；
- 三表 / 模型审计 / 数据清洗；
- earnings preview / earnings analysis；
- initiating coverage / model update；
- competitive analysis；
- sector overview / idea generation；
- thesis tracker / catalyst calendar。

专业结果进入 CIS 证据登记，并用于补充或校正 TradingAgents 通用研究。

## 7. Fallback adapters

TradingAgents 为 `upstream_only`、`unavailable` 或 `blocked` 时：

1. 不伪造外部决策。
2. 原 CIS 专家 Agent 按 `agent-registry.md` 以 fallback adapter 身份运行。
3. 只调用完成任务所需的最小专家集合。
4. 证据审计员仍保持独立。
5. 输出明确说明 TradingAgents 未实际运行及置信度影响。

## 8. 冲突与质量循环

冲突按以下顺序解释：

1. 数据截止时间；
2. 数据源/市场覆盖；
3. 会计或指标口径；
4. 时间跨度；
5. 预测假设；
6. 估值方法；
7. 情绪/新闻短期信号与长期基本面冲突；
8. 事实与判断混淆。

不得通过多数票、简单平均目标价或简单平均专家置信度消除冲突。

证据审计 `unresolved` 或关键风险 `block` 时，先补证一次；仍失败则降级。

## 9. CIS 八维统一评分

按 `scoring-engine.md` 汇总：

`fundamentals`、`growth`、`valuation`、`industry_competitive`、`technical`、`catalyst_macro`、`positioning`、`risk_resilience`。

- coverage < 70%：不输出单一总分；
- 70% <= coverage < 85%：`provisional`；
- coverage >= 85% 且质量门通过：`decision_grade`。

TradingAgents 的 BUY/SELL/HOLD 或 Portfolio Manager 结论不能直接映射成 CIS 分数。

## 10. 四层结构与双向卖出

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时，强制执行：

1. 趋势层：20日、50日、200日均线及趋势状态；
2. 价格层：前高、前低、突破位、缺口、支撑和压力；
3. 成交层：成交密集区、相对均量、量价确认；
4. 风险层：成本、权重、集中度、回撤承受力、资金需求和分批比例。

TradingAgents Technical Analyst 是输入，不替代本步骤。

卖出必须同时覆盖：

- 盈利止盈路径；
- 防守止损路径。

## 11. ETF / QDII 专属门

跨境 ETF / QDII 不把 TradingAgents 作为默认核心。优先执行 CIS 的产品身份、精确基准、IOPV、历史溢价、申赎、额度、时差和流动性纪律。

风险提示公告或绝对高溢价不能单独触发卖出。

## 12. 组合数据门

只有持仓、权重、成本、基准、约束和资金需求足够时，才把候选标的结论转换成精确仓位或再平衡动作。

TradingAgents Portfolio Manager 的仓位意见若缺少用户真实组合背景，只能作为一般候选，不得直接采用。

## 13. 最终研究姿态

无完整组合背景：

- `进入深入研究`
- `继续观察`
- `暂时回避`
- `证据不足`

组合背景完整：

- `维持`
- `考虑增持`
- `考虑减持`
- `考虑退出`
- `暂不操作`

最终结论必须说明 TradingAgents 是否实际运行、Anthropic 专业 Skill 是否实际运行、评分覆盖度、关键冲突和主要限制。

## 14. 跟踪与复盘

按照 `research-lifecycle.md` 记录论点、证伪条件、监控指标、下一事件和复盘日期；如 TradingAgents decision log 可用，可作为外部复盘证据，但不能替代 CIS 自己的论点生命周期。
