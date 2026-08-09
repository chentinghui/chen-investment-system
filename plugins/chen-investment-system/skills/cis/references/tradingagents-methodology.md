# ChatGPT-native TradingAgents Methodology

本文件定义 CIS 0.3.2 的默认股票研究方法。它吸收 `TauricResearch/TradingAgents` 的多角色研究结构，但**默认由当前 ChatGPT 会话直接执行**，不要求运行 TradingAgents Python 包，也不要求 NVIDIA/OpenAI/Ollama 等外部 LLM API。

## 核心原则

- TradingAgents 在 CIS 中首先是一套**研究方法论**，不是日常必须启动的外部程序。
- ChatGPT 直接承担多角色研究编排，并使用本次可核验的公开数据、连接器数据和用户资料。
- 不声称“运行了原版 TradingAgents”，除非本次确实执行官方/上游 Python 图并通过结果校验。
- 方法论输出只是 CIS 的研究输入；CIS 仍拥有证据门、风险门、八维评分、四层交易、ETF/QDII 纪律、组合门和最终中文结论。

## 默认角色结构

### Analyst Layer

1. **Market / Technical Analyst**：趋势、动量、波动、关键价位与市场结构。
2. **Fundamentals Analyst**：收入、利润、现金流、资产负债表、业务质量与关键 KPI。
3. **News / Catalyst Analyst**：财报、公司事件、行业新闻、政策与宏观催化剂。
4. **Sentiment / Positioning Analyst**：只在有可验证数据且会改变结论时使用，关注机构持仓、资金流、拥挤度与市场预期。

### Debate Layer

5. **Bull Researcher**：提出最强看多论据、上涨路径和可验证催化剂。
6. **Bear Researcher**：提出最强看空论据、下行机制和证伪条件。
7. **Research Manager**：解释冲突，不按多数票、不机械平均，形成研究候选结论。

### Decision Layer

8. **Trader Perspective**：仅在涉及交易时，把研究结论转成条件化的入场/等待/止盈/防守方案。
9. **Risk Perspective**：检查尾部风险、事件风险、估值压缩、流动性、集中度和论点失效路径。
10. **Portfolio Perspective**：只有用户真实组合数据足够时才讨论仓位；否则只提供一般候选，不给精确比例。

## 研究模式

- `quick`：调用最相关的 1–2 个 Analyst + 简化 Bull/Bear 反证；优先速度。
- `standard`：通常 Market + Fundamentals + News，必要时 Sentiment；执行 Bull/Bear + Research Manager。
- `deep`：四个 Analyst + 完整 Bull/Bear + Risk；按需加入 Anthropic Financial Services 的 DCF/Comps/Earnings 等专业方法。
- `holding_review`：在 standard/deep 基础上，强制执行 CIS 四层交易框架和组合数据门。

## ChatGPT 直接执行顺序

```text
研究问题 / as_of
  ↓
可核验证据采集
  ↓
Market + Fundamentals + News (+ Sentiment 按需)
  ↓
Bull / Bear 反证
  ↓
Research Manager 综合
  ↓
Trader / Risk / Portfolio（按任务需要）
  ↓
methodology_candidate
  ↓
CIS 证据审计 → 风险门 → 八维评分
  ↓
四层交易 / ETF / 组合门
  ↓
最终中文研究姿态
```

`methodology_candidate` 不是 TradingAgents 官方 `external_decision_candidate`，二者必须区分。

## 与原版 TradingAgents 的关系

原版 TradingAgents Python 仅在以下情况使用：

- 用户明确要求“运行原版 TradingAgents / 跑官方程序 / 做系统测试”；
- 需要对 ChatGPT-native 方法论做 A/B 验证；
- 维护者需要验证上游新功能是否值得吸收。

原版运行路径见 `tradingagents.md`。原版远程运行仍会在每次执行时拉取 `TauricResearch/TradingAgents` 当前 `main`。

## 上游更新同步纪律

TradingAgents 上游变化**不能直接覆盖**本方法论。同步流程固定为：

```text
上游 main SHA 变化
  ↓
自动检测并标记 review_required
  ↓
人工/ChatGPT 语义审查：Agent、Prompt、Graph、工具、风险流程是否有实质改进
  ↓
只吸收对 CIS 有明确价值且不破坏证据/风险纪律的变化
  ↓
更新本文件并记录 reviewed_sha
```

仅 README、徽章、文档排版等非研究逻辑变化，可以审查后标记 `reviewed_no_methodology_change`，无需修改本方法论。

上游状态文件：`runtime/tradingagents/upstream-status.json`。

自动检测 workflow：`.github/workflows/cis-tradingagents-upstream-watch.yml`。

## 证据纪律

- 模型角色不是证据来源；每个事实仍要落到真实数据源。
- 代码仓库更新不代表行情、财报或新闻实时。
- 历史日期研究禁止使用 `analysis_date` 之后的信息。
- Bull/Bear 的任务是暴露不确定性，不是制造戏剧化争论。
- 缺失数据不填 0、不猜测；按 CIS coverage gate 处理。
