---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。凡用户在投资语境下要求分析、判断、估值、买卖、持仓、财报、风险、目标价、买入价或卖出价的股票/上市公司/ETF，默认进入 CIS；包括“分析 MU”“看看 NVDA”“MU能买吗”“QQQ还能持有吗”等简短表达。纯事实型问题不强制进入完整 CIS。股票/上市公司研究默认使用 TradingAgents 多 Agent 核心；本地不可执行时可通过 GitHub Actions 远程桥真实运行 TradingAgents；专业财务/估值/财报方法按需使用 Anthropic Financial Services；最终由 CIS 执行证据门、八维评分、四层交易、ETF/QDII纪律、组合门和中文结论。
---

# 陈氏投资系统（CIS）0.3.1

CIS 是唯一用户入口和最终质量控制层。

**默认架构：CIS Control Layer + TradingAgents Core（本地或 GitHub Remote）+ Anthropic Financial Services。**

TradingAgents 的 Portfolio Manager、Trader 或 BUY/SELL/HOLD 只能产生 `external_decision_candidate`；最终 CIS 研究姿态必须回到本 Skill 的质量门。

## 自动触发规则

以下情况即使用户没有说“陈氏投资系统”，也默认进入 CIS：

- `分析 MU`、`分析 NVDA`、`分析 159509`；
- `看看英伟达`、`看看美光`，且上下文是投资研究；
- `MU 现在能买吗`、`NVDA 要不要卖`、`QQQ 还能持有吗`；
- 询问合理买入价、目标价、止盈价、止损价、估值、上涨空间、风险、财报影响、仓位或持仓复盘；
- 比较两个或多个股票/ETF 谁更值得研究、买入或持有。

纯事实型问题如公司全称、CEO、跟踪指数、交易时间、代码或上市地点，不强制启动完整 CIS。

判断原则：**只要答案会影响投资研究或交易决策，默认进入 CIS；只是在查稳定事实，不必运行完整 CIS。**

## Runtime Guard：每次强制校验

当 CIS 因显式指令或自动触发规则启动时：

1. 先读取本 `SKILL.md` 与下面的必读 references。
2. 若当前环境可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 当前 `main`，不得凭聊天记忆恢复旧流程、旧权重或旧外部模块。
3. 股票/上市公司任务读取 `references/tradingagents.md`，按“本地执行 → GitHub Actions 远程桥 → fallback”的顺序检查 TradingAgents。
4. 本地包未安装**不再等于 TradingAgents 不可用**；若 GitHub 连接器可写本仓库，可在当前任务内通过远程桥运行。
5. 专业金融任务读取 `references/anthropic-financial-services.md`，只在目标 Skill 本次真实可访问时声称运行。
6. 任何外部结果必须回到 CIS：证据审计 → 风险门 → 冲突处理 → 八维评分 → 四层/ETF/组合门 → 最终中文结论。

## 必读资料

每次运行先读：

1. `references/system-workflow.md`
2. `references/module-registry.md`
3. `references/module-routing.md`
4. `references/external-modules.md`
5. `references/tradingagents.md`
6. `references/anthropic-financial-services.md`
7. `references/agent-registry.md`
8. `references/agent-orchestration.md`
9. `references/scoring-engine.md`

按需读取：

- `references/agent-contract.md`
- `references/io-contract.md`
- `references/evidence-confidence.md`
- `references/investor-profile.md`
- `references/research-lifecycle.md`
- `references/output-modes.md`
- `references/four-layer-trading-framework.md`
- `references/cross-border-etf-premium.md`

## 默认股票研究核心：TradingAgents

有效 TradingAgents 运行可以来自两条路径。

### 本地路径

当前环境可导入 `tradingagents` 且模型/API/数据源就绪时，使用 `scripts/run_tradingagents.py` 或等价方式真实执行 `.propagate()`。

### GitHub Actions 远程路径

当前对话环境不能安装/运行 TradingAgents，但 GitHub 连接器对本仓库有写权限时，按 `references/tradingagents.md` 使用远程桥：

```text
写 runtime/tradingagents/request.json
        ↓
GitHub Actions 自动触发
        ↓
安装 TradingAgents 当前上游 main
        ↓
运行 TradingAgentsGraph(...).propagate(...)
        ↓
写回 runtime/tradingagents/results/<request_id>.json
        ↓
CIS 按 request_id / ticker / analysis_date / status 校验
```

只有匹配本次请求且 `status=success`、`runtime_readiness=remote_ready`、`external_decision_candidate` 非空时，才能声称本次 TradingAgents 实际运行。

进行中、失败、旧 request_id、旧 ticker、旧日期或笼统 `result.json` 都不能冒充本次结果。

远程执行必须在当前任务内完成检查；如果本次无法形成有效结果，立即降级到 fallback，不承诺稍后异步交付。

## 研究深度与 selected_analysts

TradingAgents 原生可选择 `market`、`fundamentals`、`news`、`social` analyst。CIS 只调用会改变结论的最小集合：

- `quick`：1–2 个最相关 analyst；关键证据缺口才扩展。
- `standard`：通常 `market + fundamentals + news`；只有情绪会改变结论时增加 `social`。
- `deep`：四个 analyst 全开，并运行正常 Bull/Bear 与 Risk Debate。
- `holding_review`：按持仓问题选择 analyst，之后强制执行 CIS 四层交易框架；组合资料足够时再执行组合门。

`max_debate_rounds=0` / `max_risk_rounds=0` 只用于 smoke test 或明确的轻量诊断，不得包装成完整 Deep 研究。

### TradingAgents 不能覆盖的 CIS 能力

- GitHub 最新 CIS 版本校验；
- 证据等级和 `as_of`；
- 前视偏差检查；
- 八维统一评分与 coverage gate；
- 四层交易框架；
- 盈利止盈 + 防守止损；
- ETF/QDII 溢价纪律；
- 用户真实组合数据门；
- 用户个人投资规则；
- 最终中文研究姿态与复盘。

## 专业金融方法：Anthropic Financial Services

以下子问题优先调用 Anthropic 对应 Skill，而不是让 TradingAgents 的通用 Agent 粗略替代：

- DCF / Comps；
- 三表 / 数据清洗 / 模型审计；
- earnings preview / earnings analysis；
- initiating coverage / model update；
- competitive analysis；
- sector overview / idea generation；
- thesis tracker / catalyst calendar。

Anthropic 输出进入 CIS 证据登记，可补充或纠正 TradingAgents 通用判断。

## CIS 自写 Agent 的定位

`plugins/chen-investment-system/agents/` 保留，但默认是：

- fallback adapters：本地和远程 TradingAgents 都不能形成有效结果时兜底；
- conflict validators：外部核心之间存在关键冲突时复核；
- CIS-specific adapters：四层交易、组合门、证据审计等 CIS 特有规则。

不得在 TradingAgents 正常运行时无理由重复跑同职责自写 Agent。

## 标准输入

```text
research_type: company | stock | ETF | portfolio | industry | macro | earnings
subject: 名称及 ticker/基金代码
research_question: 本次要回答的问题
mode: quick | standard | deep | holding_review
analysis_date/as_of: 市场、财报和新闻数据截止时间
horizon: 短期 | 1-3年 | 3-10年
constraints: 市场、流动性、集中度、税务或其他限制
portfolio_context: 持仓、权重、成本、基准、资金需求
evidence_provided: 用户资料、连接器、公开资料或无
```

默认 `standard`。涉及用户真实持仓的增减持/退出/仓位影响时使用 `holding_review`。

## 执行顺序

1. Intake：对象、问题、模式、期限、`analysis_date/as_of`。
2. Runtime Guard：读取 GitHub 当前 CIS。
3. Preflight：TradingAgents 本地、TradingAgents Remote、Anthropic、数据源本次就绪度。
4. Evidence：登记事实、计算、假设、来源和限制。
5. Core Research：股票任务优先真实 TradingAgents；本地不可执行时尝试远程桥。
6. Professional Skills：按需 Anthropic。
7. Fallback：本地与远程核心都无有效结果、或存在关键冲突时，才启用 CIS 自写 adapters。
8. Audit：证据审计 + CIS 风险门。
9. Score：满足覆盖后运行 `scoring-engine.md`。
10. Trade Framework：涉及买卖/价位时执行趋势 → 价格 → 成交 → 风险。
11. ETF/Portfolio Gate：按任务执行专属约束。
12. Synthesis：最终中文研究姿态、证伪条件、下一复盘。

## 八维评分

权重只以 `references/scoring-engine.md` 为准：

- fundamentals 20
- growth 15
- valuation 15
- industry_competitive 10
- technical 15
- catalyst_macro 10
- positioning 5
- risk_resilience 10

`coverage < 70%` 不输出单一总分；`70% <= coverage < 85%` 为 provisional；`coverage >= 85%` 且质量门通过才可 decision_grade。

TradingAgents 的 rating、BUY/SELL/HOLD 或 Portfolio Manager 结论不能直接转换为 CIS 分数。

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. **趋势层**：20/50/200日均线和趋势状态；
2. **价格层**：前高前低、突破、缺口、支撑压力；
3. **成交层**：成交密集区、相对均量、量价确认；
4. **风险层**：成本、权重、集中度、回撤承受力、资金需求。

TradingAgents Technical/Market Analyst 只是输入，不替代该框架。卖出必须同时分析盈利止盈和防守止损。

## ETF / QDII

ETF，尤其跨境 ETF / QDII，不默认交给 TradingAgents 做最终产品判断。必须执行 CIS 的精确基准、产品身份、IOPV、历史溢价、申赎/额度、时差和流动性纪律。

## 组合门

只有用户真实持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位/再平衡比例。TradingAgents Portfolio Manager 若没有这些真实组合数据，其结果只能是一般候选。

## 最终研究姿态

无完整组合背景：`进入深入研究` / `继续观察` / `暂时回避` / `证据不足`。

完整 holding review：`维持` / `考虑增持` / `考虑减持` / `考虑退出` / `暂不操作`。

最终输出必须说明：

- CIS 规则版本；
- TradingAgents 是本地、远程、fallback 还是未运行；
- TradingAgents 的 `analysis_date`、request_id（远程时）和数据截止时间；
- Anthropic 专业 Skill 是否实际运行；
- CIS 评分覆盖度；
- 为什么不是更高/更低分；
- 关键证伪条件和复盘触发点。
