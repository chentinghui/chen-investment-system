# ChatGPT-native TradingAgents Methodology

本文件定义 CIS 0.4.0 的默认股票研究方法。它吸收 `TauricResearch/TradingAgents` 的多角色结构，但默认由当前 ChatGPT 会话直接执行，不要求运行 TradingAgents Python，也不要求外部 LLM API。

## 核心原则

- TradingAgents 在 CIS 中首先是一套研究方法论，不是日常必须启动的外部程序。
- ChatGPT 直接承担多角色研究编排，并使用本次可核验的公开数据、连接器数据和用户资料。
- 不声称“运行了原版 TradingAgents”，除非本次确实执行上游 Python 图并通过结果校验。
- 方法论输出只是 CIS 的研究输入；CIS 保留证据门、风险门、八维评分、Market Regime、四层交易、ETF/QDII纪律、组合门和最终中文结论。

## 默认角色结构

### Analyst Layer

1. **Market / Technical Analyst**：趋势、动量、波动、关键价位与市场结构。
2. **Fundamentals Analyst**：收入、利润、现金流、资产负债表、业务质量与关键 KPI。
3. **News / Catalyst Analyst**：财报、公司事件、行业新闻、政策与宏观催化剂。
4. **Sentiment / Positioning Analyst**：只在有可验证数据且会改变结论时使用，关注机构持仓、资金流、拥挤度与市场预期。

### Debate Layer

5. **Bull Researcher**：提出最强看多论据、上涨路径和可验证催化剂。
6. **Bear Researcher**：主动寻找与 Bull 不同的反证来源、下行机制和证伪条件。
7. **Research Manager**：解释冲突，不按多数票、不机械平均；不得创造新的事实。

### Decision Layer

8. **Trader Perspective**：仅在涉及交易时，把研究结论转成条件化的入场/等待/止盈/防守方案。
9. **Risk Perspective**：检查尾部风险、事件风险、估值压缩、流动性、集中度和论点失效路径。
10. **Portfolio Perspective**：只有用户真实组合数据足够时才讨论仓位；否则只提供一般候选，不给精确比例。

## 多角色独立性协议

同一个模型扮演多个角色存在相关性错误风险，因此强制执行：

- **Source separation**：Bull 与 Bear 尽可能使用不同证据来源/不同机制，不允许 Bear 只把 Bull 结论改成否定句。
- **Evidence ownership**：每个 Analyst 的事实必须能追溯到来源；角色意见本身不算证据。
- **No fact creation by manager**：Research Manager 只能裁决已登记证据、计算和假设，禁止引入未核验新事实。
- **Risk independence**：Risk 必须至少提出一个不依赖 Bull/Bear 主论点的尾部风险或失效机制。
- **Conflict preservation**：关键冲突无法解决时保留冲突并降低 confidence，不通过多数票消除。
- **As-of discipline**：所有角色共享同一 `analysis_date/as_of`，历史研究禁止未来信息泄漏。

## 研究模式

- `quick`：最相关 1–2 个 Analyst + 简化 Bull/Bear 反证；优先速度。
- `standard`：通常 Market + Fundamentals + News，必要时 Sentiment；执行 Bull/Bear + Research Manager。
- `deep`：四个 Analyst + 完整 Bull/Bear + Risk；按需加入 DCF/Comps/Earnings 等专业方法。
- `holding_review`：在 standard/deep 基础上，强制执行 CIS 四层交易框架和组合数据门。

## ChatGPT 直接执行顺序

```text
研究问题 / as_of
  ↓
可核验证据采集
  ↓
Market + Fundamentals + News (+ Sentiment 按需)
  ↓
Bull / Bear 独立反证
  ↓
Research Manager 综合
  ↓
Trader / Risk / Portfolio（按任务需要）
  ↓
methodology_candidate
  ↓
CIS Evidence → Risk → Score → Regime（按需）
  ↓
四层交易 / ETF / 组合门
  ↓
最终中文研究姿态
```

`methodology_candidate` 不是 TradingAgents 官方 `external_decision_candidate`。

## 与 Quant Engine 的关系

大股票池任务允许先使用 `quant-engine.md` 做横截面预筛：

```text
Universe → Quant Top N → 本方法论深研 → CIS 最终质量门
```

Quant 不能替代 Bull/Bear、估值、风险或证据审计。

## 与原版 TradingAgents 的关系

原版 TradingAgents Python 仅在以下情况使用：

- 用户明确要求运行原版/官方程序/系统测试；
- 需要对 ChatGPT-native 方法论做 A/B 验证；
- 维护者需要验证上游新功能是否值得吸收。

原版运行路径见 `tradingagents.md`，远程执行每次拉取上游当前 `main`。

## 上游更新同步纪律

TradingAgents 上游变化不能直接覆盖本方法论：

```text
上游 main SHA 变化
  ↓
自动检测 → review_required
  ↓
审查 Agent / Prompt / Graph / Tool / Risk 变化
  ↓
只吸收明确提高 CIS 质量且不破坏现有质量门的变化
  ↓
更新本文件 + reviewed_sha
```

上游状态：`runtime/tradingagents/upstream-status.json`。

自动检测：`.github/workflows/cis-tradingagents-upstream-watch.yml`。

## 证据纪律

- 模型角色不是证据来源；每个事实仍要落到真实数据源。
- 代码仓库更新不代表行情、财报或新闻实时。
- 历史日期研究禁止使用 `analysis_date` 之后的信息。
- Bull/Bear 的任务是暴露不确定性，不是制造戏剧化争论。
- 缺失数据不填 0、不猜测；按 CIS coverage gate 处理。
