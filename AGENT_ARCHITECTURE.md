# 陈氏投资系统：CIS 0.4.5 架构

CIS 的核心职责是**股票分析与质量控制**，不是把量化、回测、预测数据库和外部运行时全部塞进默认链。QuantConnect LEAN 被放在独立 External Quant 层，只在策略级验证时调用。

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

策略/规则需要量化验证时另行分支：
CIS Strategy / Rule
  ↓
Backtest Validation Policy
  ↓
integrations/lean/cis_lean_adapter.py
  ↓
External QuantConnect LEAN
  ↓
Backtest Statistics（unreviewed）
  ↓
偏差 / 样本外 / 成本 / 执行真实性审查
  ↓
量化证据回灌 CIS（无最终动作权）
```

## Core、External Quant 与 Extension

CIS Core 只负责分析、证据、风险、评分和交易纪律。

**External QuantConnect LEAN**：

- 策略级事件驱动回测首选引擎；
- 独立安装、独立升级；
- 不 vendor、不复制、不作为 git submodule；
- CIS 只维护 `integrations/lean/` 适配器和结果契约；
- 当前只启用 backtest / result parsing，不启用 live trading 或 Broker 自动执行；
- `execution_status=success` 不等于 `research_quality=accepted`。

以下能力物理隔离在 `extensions/research_tooling/`，仅按需使用：

- Quant Factor Ranking：股票池预筛；
- Baseline Backtest：`date,ticker,score,forward_return` 横截面因子/Top-N sanity check；
- Prediction/Evaluation：可选记录、结算和校准诊断。

External/Extension 故障不得阻塞日常单股分析，也不得自动修改 CIS 生产权重。

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

## QuantConnect LEAN 边界

```text
engine = QuantConnect LEAN
engine_role = external_quant_validation
decision_authority = none
execution_status = success | invalid_input | unavailable | error
research_quality = unreviewed
```

LEAN 负责回答“这套可执行规则历史上怎么表现”，不负责回答“公司基本面值不值得投”，也不负责 CIS 最终买卖裁决。

需要策略级回测时：

```text
references/quantconnect-lean.md
+ references/backtest-validation.md
        ↓
integrations/lean/cis_lean_adapter.py
```

只有本次真实执行成功并解析到可识别 statistics JSON，才能声称 LEAN 已运行。Lean CLI / Docker 基础环境存在，只能说明 `runtime_readiness`，不能证明账户、数据、项目和策略已可执行。

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

Tactical setup 与 Research Grade 分开；高分不自动等于当前可以买。LEAN 的回测统计又是第三类独立证据，不能覆盖前两者。

## 关键文件

- 总入口：`plugins/chen-investment-system/skills/cis/SKILL.md`
- 系统流程：`plugins/chen-investment-system/skills/cis/references/system-workflow.md`
- 模块路由：`plugins/chen-investment-system/skills/cis/references/module-routing.md`
- 外部模块：`plugins/chen-investment-system/skills/cis/references/external-modules.md`
- LEAN 契约：`plugins/chen-investment-system/skills/cis/references/quantconnect-lean.md`
- 回测验证：`plugins/chen-investment-system/skills/cis/references/backtest-validation.md`
- LEAN 适配器：`integrations/lean/cis_lean_adapter.py`
- Agent 登记：`plugins/chen-investment-system/skills/cis/references/agent-registry.md`
- Agent 契约：`plugins/chen-investment-system/skills/cis/references/agent-contract.md`
- TradingAgents 方法论：`plugins/chen-investment-system/skills/cis/references/tradingagents-methodology.md`
- 原版 TradingAgents：`plugins/chen-investment-system/skills/cis/references/tradingagents.md`
- 评分引擎：`plugins/chen-investment-system/skills/cis/references/scoring-engine.md`
- 四层交易：`plugins/chen-investment-system/skills/cis/references/four-layer-trading-framework.md`
- Optional Extensions：`extensions/research_tooling/`
