# CIS 精选外部投资 Skill Overlay（2026-08-17）

本文件记录 CIS 对公开投资 Skill 仓库的**去重后精选能力**。目标不是把第三方仓库整体复制进 CIS，而是：

1. 已由 CIS Core / Anthropic Financial Services 覆盖的能力只做路由映射；
2. 真正缺失的能力定义为 CIS Adapter；
3. 所有外部方法均无最终动作权，最终仍必须经过 CIS Evidence / Risk / Critical Dimension / Score / Tactical / Portfolio 等适用质量门；
4. 不因外部仓库更新自动覆盖稳定方法论；需要真实调用上游时逐次核验可访问性与当前版本；
5. 本文件只吸收工作流思想与接口设计，不要求复制第三方实现。

## 评估来源

- Anthropic `anthropics/financial-services`：专业金融建模、财报、竞争格局、催化剂与 idea sourcing；
- AI Berkshire `xbtlin/ai-berkshire`：价值投资、行业漏斗、瓶颈猎手、管理层、论文漂移与快速事件归因；
- Claude Trading Skills `tradermonty/claude-trading-skills`：仓位、回撤熔断、交易纪律、复盘与期权策略；
- Daisy Financial Research `Agents365-ai/daisy-financial-research`：point-in-time、防前视、数值校验、scratchpad/decision-log 设计；
- InvestSkill `yennanliu/InvestSkill`：数据验证门、bear case、催化剂、期权与标准化单股框架。

## 最终精选 20 项

| # | 能力 / Skill | 主要来源 | CIS 处理 | 默认路由 |
|---|---|---|---|---|
| 1 | `bottleneck-hunter` | AI Berkshire | **新增 Adapter** | 主题/产业链机会研究 |
| 2 | `industry-funnel` | AI Berkshire | **新增 Adapter** | 行业 → ≤10 → Top 3 |
| 3 | `quality-screen` | AI Berkshire | **新增 Adapter** | 快速去劣/是否值得深研 |
| 4 | `management-deep-dive` | AI Berkshire | **新增 Adapter** | 管理层成为核心变量时 |
| 5 | `thesis-drift` | AI Berkshire | **新增 Adapter** | 复盘既有 research_id |
| 6 | `news-pulse` | AI Berkshire | **新增 Adapter** | 异动/突发事件快速归因 |
| 7 | `financial-data` rigor | AI Berkshire | 映射 Evidence Audit | 关键数字交叉验证 |
| 8 | `investment-checklist` | AI Berkshire | 映射 Critical Dimension Gate | 深研前快速检查 |
| 9 | `comps-analysis` | Anthropic | 现有上游优先 | 相对估值 |
| 10 | `dcf-model` | Anthropic | 现有上游优先 | 内在价值/敏感性 |
| 11 | `earnings-preview` | Anthropic | 现有上游优先 | 财报前预期差/情景 |
| 12 | `earnings-analysis` | Anthropic | 现有上游优先 | 财报后更新 |
| 13 | `competitive-analysis` | Anthropic | 现有上游优先 | 竞争格局/市场定位 |
| 14 | `catalyst-calendar` | Anthropic | 现有上游优先 | 催化剂时间表 |
| 15 | `idea-generation` | Anthropic | 映射 Quant + Core | 股票池/主题选股 |
| 16 | `position-sizer` | Claude Trading Skills | **新增 Adapter** | 任何明确交易计划 |
| 17 | `drawdown-circuit-breaker` | Claude Trading Skills | **新增 Adapter** | 真实账户回撤/连亏控制 |
| 18 | `pre-trade-discipline-gate` | Claude Trading Skills | **新增 Adapter** | 下单前 fail-closed 检查 |
| 19 | `options-strategy-advisor` | Claude Trading Skills | **新增 Adapter** | 期权结构比较 |
| 20 | `signal-postmortem` | Claude Trading Skills | **新增 Adapter** | 交易结束后的复盘 |

## 为什么没有继续堆更多 Skill

以下能力评估过，但不单独引入：

- `investment-team` / `research-bundle` / `us-stock-analysis`：与 CIS 的 ChatGPT-native TradingAgents Methodology + Bull/Bear + Research Manager 大面积重叠；
- `thesis-tracker`：CIS 已有 `research-lifecycle.md` 的 `research_id / core_thesis / thesis_falsifiers / change_since_prior`，只补 `thesis-drift`；
- `result-validator` / `data-quality-checker`：与 Evidence Audit、Risk Review、Critical Dimension Gate 重叠；
- `portfolio-manager` / `portfolio-review`：CIS 已有 Portfolio Gate，且真实组合结论必须基于用户真实持仓数据；
- `technical-analysis` / `technical-analyst`：CIS 已有 Technical + Tactical Price/RR，不再建立第二套技术面权威；
- `bear-case`：CIS 已要求 Bull/Bear 独立反证，不重复新建；
- Daisy 的 `decision-log`、point-in-time guard、numerical validation：作为 Performance/Evidence 的实现参考，不建立第二个总控数据库。

# 新增 Adapter 契约

以下 Adapter 是 CIS 原生接口，不代表已经运行第三方代码。

## 1. Bottleneck Hunter Adapter

触发：用户要求“找下一个 LITE / AOSL”“某超级趋势的供应链瓶颈”“谁最可能因为供给约束受益”。

流程：

```text
Theme / End demand
  ↓
Value-chain map
  ↓
Physical / capacity / certification / yield / lead-time constraints
  ↓
Constraint severity + duration
  ↓
Public-company exposure
  ↓
Capacity response + competition
  ↓
Valuation + catalyst + downside
  ↓
Candidate list → CIS Core 深研
```

必须区分：

- 真正物理瓶颈 vs 只是在热点叙事中出现；
- 订单/产能/良率/交期证据 vs 模型猜测；
- 行业需求增长 vs 公司实际收入暴露；
- 暂时短缺 vs 可持续壁垒。

输出至少包含：`bottleneck`, `evidence`, `duration`, `company_exposure`, `capacity_response`, `key_customer_risk`, `valuation_risk`, `candidate_status`。

`candidate_status` 只能是：

```text
reject | watch | candidate_for_cis_research
```

无直接买入权。

## 2. Industry Funnel Adapter

触发：用户要求从一个行业/主题中筛 3–10 家公司。

```text
Universe
  ↓ hard exclusions
Qualified set
  ↓ quality / exposure / balance-sheet / valuation / catalyst rank
≤10 names
  ↓ CIS evidence check
Top 3 for deep research
```

硬排除必须写明理由，不允许因为“模型不喜欢”而删除。大股票池计算按需路由 Quant Extension；最终 Top 3 必须回 CIS Core。

## 3. Quality Screen Adapter

目标：快速回答“这家公司值不值得继续研究”，不是直接给买卖信号。

优先检查：

- 持续经营/现金流与融资依赖；
- 明显稀释、债务或流动性压力；
- 审计/会计/治理重大红旗；
- 商业模式是否能解释；
- 毛利/ROIC/FCF 等质量指标是否与行业结构一致；
- 估值是否已经使好公司失去安全边际。

输出：`pass | conditional | reject` + 证据。`pass` 只表示值得深研。

## 4. Management Deep Dive Adapter

仅当管理层对论文影响显著时启用。至少评估：

- 历史指引可信度；
- 资本配置：回购、并购、债务、股权激励、再投资；
- 内部人经济利益与普通股东是否一致；
- 治理结构与关键人风险；
- 危机期行为记录；
- 重大承诺的兑现记录。

事实与评价分栏；人格猜测不得作为证据。

## 5. Thesis Drift Adapter

输入必须至少包含同一 `research_id` 的 prior 与 current 版本。

变化分为：

```text
fact_change
assumption_change
valuation_change
catalyst_change
risk_change
wording_only
```

输出：

```text
thesis_status = stable | strengthened | weakened | review_required | falsified
```

只改变措辞不得触发 thesis 变化；关键事实或 falsifier 命中必须进入 `review_required` 或 `falsified`。

## 6. News Pulse Adapter

用于“为什么突然大涨/大跌”“刚刚这条新闻影响多大”。

按顺序：

1. 事件发生时间与信息发布时间；
2. 优先确认公司/监管/政府/交易所等一手来源；
3. 将事件与市场原预期比较；
4. 区分一次性 headline 与会改变收入、利润率、资本结构、估值或监管路径的事件；
5. 对照价格/成交量反应；
6. 输出 `temporary_noise | monitor | thesis_relevant | thesis_breaking`。

不得用股价上涨反向证明新闻一定利好。

## 7. Position Sizer Adapter

只在存在明确 Entry 与 Stop/Invalidation 时计算。

股票 baseline：

```text
risk_budget = account_equity × allowed_risk_pct
per_share_risk = abs(entry - hard_stop)
raw_shares = floor(risk_budget / per_share_risk)
```

之后还必须经过：

- 最大单标的权重；
- Portfolio Gate 集中度；
- 流动性；
- 事件风险；
- gap risk（硬止损不保证成交价）。

对于期权，不把正股止损公式直接套到合约；优先使用合约最大损失、premium at risk、spread defined-risk 计算。

若账户规模、当前组合权重或风险预算未知，只能给公式/区间，不能伪造“建议买 X 股”。

## 8. Drawdown Circuit Breaker Adapter

该模块依赖**真实账户/交易历史**。无真实数据时不得声称已触发或未触发。

可配置检查：

- 单日最大亏损；
- 连续亏损次数；
- 周/月 drawdown；
- 已实现 + 未实现风险；
- 是否处于重大事件后失真状态。

输出：

```text
risk_permission = allowed | reduced | blocked | unavailable
```

`blocked` 时 Pre-Trade Discipline Gate 必须阻止新增风险交易；不能被高 Research Grade 覆盖。

## 9. Pre-Trade Discipline Gate Adapter

任何明确“准备下单”的请求可启用。以下任一关键项失败则 fail-closed：

- thesis / setup 不清楚；
- quote stale 或 session 语义错误；
- Entry / Stop / Target 不完整；
- Tactical R/R 不达标；
- position size 未定义；
- 当前事件风险未检查；
- drawdown circuit breaker = blocked；
- 交易与 Portfolio Gate 明显冲突。

输出：

```text
trade_gate = pass | wait | blocked | unavailable
```

## 10. Options Strategy Advisor Adapter

目标是比较结构，不是预测“哪张期权一定涨”。

至少检查：

- 方向 / 目标价 / 时间窗口；
- DTE；
- ATM/ITM/OTM；
- IV / IV event risk；
- bid-ask spread、volume、open interest；
- Delta / Gamma / Theta / Vega；
- 最大损失、最大收益或收益上限；
- breakeven；
- assignment / exercise / expiration 风险；
- earnings / CPI / FOMC 等事件。

优先比较 defined-risk 结构。若用户明确做 0DTE，额外标记 gamma/theta 与流动性风险，并保持 Tactical Setup 与长期 Research Grade 分离。

## 11. Signal Postmortem Adapter

交易结束后按“过程质量”和“结果”分离复盘：

```text
original_thesis
planned_entry / stop / target / size
actual_execution
outcome
MAE / MFE（若有可靠数据）
rule_adherence
thesis_error
execution_error
risk_error
what_would_change_next_time
```

盈利交易也可能是坏执行；亏损交易也可能是好执行。不得以最终盈亏反推当时决策质量。

## 12. Financial Data / Decision Audit Pattern

吸收 AI Berkshire、Daisy、InvestSkill 的共同优点，落到 CIS Evidence 层：

- 关键估值输入至少记录来源、日期、单位、币种、期间；
- 重要数字优先交叉核验，冲突不得静默平均；
- 银行/保险等金融机构不得机械套普通工业公司的 DCF；
- 历史技术/量化计算先做 `as_of` 截断，禁止 future rows；
- 任何自动日志/复盘结果不得获得最终动作权。

# 路由优先级

```text
快速去劣 / 行业筛选 / 瓶颈寻找
    → Curated Adapter / Quant
    → 候选回 CIS Core

单股深研
    → CIS Core
    → Management / Competitive / DCF / Comps 等按需增强

财报
    → CIS Core + Anthropic Earnings

突发异动
    → News Pulse
    → Evidence + Tactical Context

准备交易
    → Tactical Price/RR
    → Position Sizer
    → Drawdown Circuit Breaker（有真实账户数据时）
    → Pre-Trade Discipline Gate

期权
    → 正股 CIS 研究
    → Options Strategy Advisor
    → Tactical / Risk / Liquidity checks

交易结束
    → Signal Postmortem（仅用户要求记录/复盘时）
    → Performance/Evaluation Extension（按需）
```

# 安全与维护

- 外部 Skill 名称只用于来源追踪与方法映射；CIS 不宣称第三方作者认可本整合；
- 真实运行第三方代码前继续遵守现有 upstream review / credential / read-only 边界；
- 新 Adapter 初始状态统一视为 `methodology_adapter_unvalidated`，需要样本与回测验证的阈值不得包装成已证实 edge；
- 若外部上游与 CIS 冲突，以 CIS fail-closed Evidence / Risk / Tactical / Portfolio Gate 为最终规则。
