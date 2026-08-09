---
name: cis
description: 作为陈氏投资系统（Chen Investment System，CIS）的唯一用户入口。凡用户在投资语境下要求分析、判断、估值、买卖、持仓、财报、风险、目标价、买入价或卖出价的股票/上市公司/ETF，默认进入 CIS；包括“分析 MU”“看看 NVDA”“MU能买吗”“QQQ还能持有吗”等简短表达。纯事实型问题不强制进入完整 CIS。股票/上市公司研究默认由当前 ChatGPT 会话直接执行 TradingAgents 多角色研究方法论；原版 TradingAgents Python 仅在用户明确要求运行/测试时调用；专业财务、估值和财报方法按需使用 Anthropic Financial Services；最终由 CIS 执行证据门、八维评分、四层交易、ETF/QDII纪律、组合门和中文结论。
---

# 陈氏投资系统（CIS）0.3.2

CIS 是唯一用户入口和最终质量控制层。

**默认架构：ChatGPT → CIS Control Layer → ChatGPT-native TradingAgents Methodology → 专业金融 Skills（按需）→ CIS 最终质量门。**

日常研究不要求外部 LLM API，也不要求运行 TradingAgents Python。

## 自动触发规则

以下情况即使用户没有说“陈氏投资系统”，也默认进入 CIS：

- `分析 MU`、`分析 NVDA`、`分析 159509`；
- `看看英伟达`、`看看美光`，且上下文是投资研究；
- `MU 现在能买吗`、`NVDA 要不要卖`、`QQQ 还能持有吗`；
- 询问合理买入价、目标价、止盈价、止损价、估值、上涨空间、风险、财报影响、仓位或持仓复盘；
- 比较多个股票/ETF 谁更值得研究、买入或持有。

纯事实型问题如公司全称、CEO、跟踪指数、交易时间、代码或上市地点，不强制启动完整 CIS。

## Runtime Guard

当 CIS 启动时：

1. 读取本 `SKILL.md` 与必读 references。
2. 若可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 当前 `main`，不得凭聊天记忆恢复旧规则、旧权重或旧模块。
3. 股票/上市公司任务先读 `references/tradingagents-methodology.md`，默认由 ChatGPT 直接执行其中的多角色研究逻辑。
4. 同时读取 `runtime/tradingagents/upstream-status.json`（可访问时）。若 `review_status=review_required`，说明上游 TradingAgents 已变化但 CIS 方法论尚未审查；不得自动套用未审查的新逻辑。
5. 只有用户明确要求“运行原版 TradingAgents / 跑官方程序 / 系统测试”时，才读 `references/tradingagents.md` 并启动本地或 GitHub Actions 原版运行路径。
6. 专业金融任务按需读 `references/anthropic-financial-services.md`；只有目标 Skill 本次真实可访问时才能声称实际运行。
7. 所有结果必须回到 CIS：证据审计 → 风险门 → 冲突处理 → 八维评分 → 四层/ETF/组合门 → 最终中文结论。

## 必读资料

每次运行先读：

1. `references/system-workflow.md`
2. `references/module-registry.md`
3. `references/module-routing.md`
4. `references/external-modules.md`
5. `references/tradingagents-methodology.md`
6. `references/anthropic-financial-services.md`
7. `references/agent-registry.md`
8. `references/agent-orchestration.md`
9. `references/scoring-engine.md`

按需读取：

- `references/tradingagents.md`（仅原版运行/测试/上游审查）
- `references/agent-contract.md`
- `references/io-contract.md`
- `references/evidence-confidence.md`
- `references/investor-profile.md`
- `references/research-lifecycle.md`
- `references/output-modes.md`
- `references/four-layer-trading-framework.md`
- `references/cross-border-etf-premium.md`

## 默认股票研究核心：ChatGPT-native TradingAgents Methodology

ChatGPT 在当前会话中直接按以下角色结构研究，不需要外部模型 API：

```text
Market / Technical
+ Fundamentals
+ News / Catalyst
+ Sentiment / Positioning（按需）
        ↓
Bull / Bear 反证
        ↓
Research Manager 综合
        ↓
Trader / Risk / Portfolio（按任务需要）
        ↓
methodology_candidate
```

`methodology_candidate` 只是方法论候选，不是原版 TradingAgents 的 `external_decision_candidate`，也不是 CIS 最终动作。

### 研究模式

- `quick`：最相关 1–2 个 Analyst + 简化反证，优先速度。
- `standard`：通常 Market + Fundamentals + News，必要时 Sentiment；执行 Bull/Bear 与 Research Manager。
- `deep`：四个 Analyst + 完整反证与 Risk；按需专业 DCF/Comps/Earnings。
- `holding_review`：在 standard/deep 基础上，强制执行四层交易框架和组合门。

## 原版 TradingAgents：显式测试模式

原版 Python 不再是日常默认链路。仅在用户明确要求时运行。

- 本地可执行：`scripts/run_tradingagents.py`。
- 远程测试：写 `runtime/tradingagents/request.json`，由 `.github/workflows/cis-tradingagents.yml` 运行。
- 远程 workflow 每次都会重新 clone `TauricResearch/TradingAgents` 当前 `main`，因此原版测试路径天然使用当次上游最新版。
- 只有 request_id / ticker / analysis_date 匹配，且 `status=success`、`runtime_readiness=remote_ready`、`external_decision_candidate` 非空时，才能声称原版 TradingAgents 本次实际运行。

## TradingAgents 上游更新策略

方法论不盲目自动升级：

```text
上游 main SHA 变化
  ↓
GitHub Actions 自动检测
  ↓
upstream-status.json 标记 review_required
  ↓
人工/ChatGPT 语义审查 Agent / Prompt / Graph / 工具 / Risk 流程变化
  ↓
只吸收明确提高 CIS 研究质量且不破坏质量门的变化
  ↓
更新 methodology + reviewed_sha
```

检测 workflow：`.github/workflows/cis-tradingagents-upstream-watch.yml`。

状态文件：`runtime/tradingagents/upstream-status.json`。

README/徽章/排版等非研究逻辑变化，审查后可标记 `reviewed_no_methodology_change`。

## 专业金融方法：Anthropic Financial Services

以下子问题优先使用对应专业 Skill：

- DCF / Comps；
- 三表 / 数据清洗 / 模型审计；
- earnings preview / earnings analysis；
- initiating coverage / model update；
- competitive analysis；
- sector overview / idea generation；
- thesis tracker / catalyst calendar。

专业结果进入 CIS 证据登记，用于补充或校正通用研究。

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
2. Runtime Guard：读取 GitHub 当前 CIS 与 TradingAgents 上游审查状态。
3. Evidence：采集并登记事实、计算、假设、来源和限制。
4. Core Research：ChatGPT 直接执行 TradingAgents Methodology。
5. Professional Skills：按需 Anthropic。
6. Audit：证据审计 + CIS 风险门 + 冲突解释。
7. Score：满足覆盖后运行 `scoring-engine.md`。
8. Trade Framework：涉及买卖/价位时执行趋势 → 价格 → 成交 → 风险。
9. ETF/Portfolio Gate：按任务执行专属约束。
10. Synthesis：最终中文研究姿态、证伪条件、下一复盘。

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

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. **趋势层**：20/50/200日均线和趋势状态；
2. **价格层**：前高前低、突破、缺口、支撑压力；
3. **成交层**：成交密集区、相对均量、量价确认；
4. **风险层**：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈和防守止损。

## ETF / QDII

ETF，尤其跨境 ETF / QDII，不默认套用股票多 Agent 结论。必须执行 CIS 的精确基准、产品身份、IOPV、历史溢价、申赎/额度、时差和流动性纪律。

## 组合门

只有用户真实持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位/再平衡比例。

## 最终研究姿态

无完整组合背景：`进入深入研究` / `继续观察` / `暂时回避` / `证据不足`。

完整 holding review：`维持` / `考虑增持` / `考虑减持` / `考虑退出` / `暂不操作`。

最终输出必须说明：

- CIS 规则版本；
- 本次是 `ChatGPT-native methodology` 还是显式原版 TradingAgents 运行；
- 数据截止时间；
- Anthropic 专业 Skill 是否实际运行；
- CIS 评分覆盖度；
- 为什么不是更高/更低分；
- 关键证伪条件和复盘触发点。
