# 陈氏投资系统：CIS 0.4.5 架构

CIS 的核心职责是**股票分析与质量控制**，不是把量化、回测、预测数据库和外部运行时全部塞进默认链。

```text
用户
  ↓
CIS Control Layer
  ↓
ChatGPT-native TradingAgents Methodology
  ├─ Market / Technical
  ├─ Fundamentals
  ├─ News / Catalyst
  ├─ Sentiment / Positioning（按需）
  ├─ Bull / Bear
  └─ Research Manager / Trader / Risk / Portfolio Perspective（按需）
  ↓
Anthropic Financial Services（专业子问题按需）
  ↓
Evidence Audit + Risk Review（fail-closed）
  ↓
Critical Dimensions / Context Checks
  ↓
CIS 八维 Research Grade
  ↓
Market Regime（按需）
  ↓
Tactical Price/Session + Quote Freshness + R/R（短线按需）
  ↓
四层交易 / ETF-QDII / Portfolio Gate
  ↓
最终中文结论
```

## Core 与 Extension

CIS Core 只负责分析、证据、风险、评分和交易纪律。

以下能力物理隔离在 `extensions/research_tooling/`，仅按需使用：

- Quant Factor Ranking：股票池预筛；
- Backtest：规则/因子/阈值验证；
- Prediction/Evaluation：可选记录、结算和校准诊断。

Extension 故障不得阻塞日常单股分析，也不得自动修改 CIS 生产权重。

## 原版 TradingAgents

原版 `TauricResearch/TradingAgents` Python 不是日常默认研究核心，只在用户明确要求运行/测试或做 A/B/上游审查时启用。其输出统一记为：

```text
external_decision_candidate
```

必须再经过 CIS Evidence / Risk / Score / Tactical / ETF / Portfolio 等适用质量门。

### 0.4.5 远程安全边界

```text
Prepare / Analyze Job
contents: read
运行固定 upstream SHA
按 provider 只注入一项所需 Secret
        ↓ Artifact
Trusted Publisher Job
contents: write
无 LLM Secret
不执行第三方代码
```

Cloud/secret-backed 原版运行只有在当前 upstream SHA 等于 `reviewed_sha` 时允许；未审查最新 main 只能零密钥 smoke test。

## CIS 自写 Agent 的定位

`plugins/chen-investment-system/agents/` 保存 CIS 角色契约：

- 总控与最终裁决；
- Evidence / Risk 质量门；
- CIS 专属四层交易、ETF/QDII、组合门；
- 外部方法不可用时的有限 fallback；
- 关键冲突复核。

它们不是要求每次分析独立重复运行的第二套完整研究团队。

## 机器契约

```text
audit_status = unverified | pass | unresolved | fail
risk_status  = unverified | pass | unresolved | fail
risk_override = none | block
```

Tactical setup 与 Research Grade 分开；高分不自动等于当前可以买。

## 关键文件

- 总入口：`plugins/chen-investment-system/skills/cis/SKILL.md`
- 系统流程：`plugins/chen-investment-system/skills/cis/references/system-workflow.md`
- 模块路由：`plugins/chen-investment-system/skills/cis/references/module-routing.md`
- Agent 登记：`plugins/chen-investment-system/skills/cis/references/agent-registry.md`
- Agent 契约：`plugins/chen-investment-system/skills/cis/references/agent-contract.md`
- TradingAgents 方法论：`plugins/chen-investment-system/skills/cis/references/tradingagents-methodology.md`
- 原版 TradingAgents：`plugins/chen-investment-system/skills/cis/references/tradingagents.md`
- 评分引擎：`plugins/chen-investment-system/skills/cis/references/scoring-engine.md`
- 四层交易：`plugins/chen-investment-system/skills/cis/references/four-layer-trading-framework.md`
- Optional Extensions：`extensions/research_tooling/`
