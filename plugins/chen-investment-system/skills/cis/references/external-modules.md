# CIS 外部模块适配与降级（0.4.5）

外部模块的“存在/可访问”“程序执行成功”“研究质量通过”必须分开判断。README、历史运行记录、聊天记忆或模块名称都不能证明本次已运行，更不能证明结果可靠。

## TradingAgents 上游

- 上游：`TauricResearch/TradingAgents`。
- CIS 日常股票研究默认**不运行其 Python 程序**，而是使用 `tradingagents-methodology.md` 的 ChatGPT-native 稳定方法论。
- 原版 Python 只用于用户明确要求的运行/测试、A/B 验证或上游功能审查。
- 日常上游检查使用 `runtime/tradingagents/upstream-status.json` 的 **7 天 TTL**。
- TTL 的确定性执行器是 `scripts/check_tradingagents_upstream.py`：距离 `last_checked_at` 不足 7 天时不访问上游；达到或超过 7 天后才检查当前 `main` SHA，并可刷新状态文件。
- SHA 变化时标记 `review_required`，当次仍使用 CIS 已验证稳定基线。
- 上游暂时不可访问不阻塞正常研究；披露 `upstream_check=unavailable`。
- 用户明确要求“检查 TradingAgents 更新”时可忽略 TTL 立即检查。
- **不使用定时 GitHub Actions 监控 TradingAgents 上游。**
- 上游变化不得自动覆盖 CIS 方法论。

### 原版远程运行安全边界

原版远程执行仍以 upstream 当前 `main` 为目标，但 0.4.5 增加两层安全门：

1. 第三方 TradingAgents 代码只在 `contents: read` Job 中执行；仓库写回由独立 trusted publisher 完成，publisher 不持有 LLM Secret，也不执行第三方代码。
2. Cloud/secret-backed 运行只有在当前 upstream SHA 与 `reviewed_sha` 一致时才允许；未审查新 SHA 只能使用零密钥 Ollama smoke test。

OpenAI-compatible provider 也使用固定凭据路由：NVIDIA endpoint 只使用 `NVIDIA_API_KEY`；自定义 HTTPS endpoint 只使用 `OPENAI_COMPATIBLE_API_KEY`，不跨 provider fallback。

### 原版运行状态分层

```text
execution_status = success | error | invalid_input | unavailable
runtime_readiness = installed_ready | installed_limited | remote_ready | remote_limited | upstream_only | blocked

evidence_audit_status = not_run | pass | unresolved | fail
research_quality = unreviewed | accepted | rejected
```

`remote_ready` / `installed_ready` 只表示程序运行完成，不表示事实正确、证据可靠或最终结论被 CIS 接受。原版 Portfolio Manager / BUY-SELL-HOLD 统一记为 `external_decision_candidate`，无最终动作权。

## Anthropic Financial Services

Anthropic `financial-services` 是 CIS 首选专业金融 Skill 上游，用于 DCF / Comps、三表、模型审计、Earnings、Competitive、Thesis、Catalyst 等专业子问题。

只有本次真实读取/执行对应 Skill 且关键输入完整时，才能标记为已使用。输出必须回灌 CIS Evidence Gate。

## Curated External Investing Skills Overlay

CIS 对公开投资 Skill 仓库的精选、去重与 Adapter 契约统一维护在：

```text
references/curated-external-skills.md
```

当用户请求以下任务时按需读取该文件：

- 超级趋势/供应链瓶颈/“下一只 LITE、AOSL”式机会寻找；
- 行业漏斗、快速去劣、管理层深挖；
- 既有研究论文漂移检查、突发异动快速归因；
- 仓位计算、账户回撤熔断、下单前纪律门；
- 期权结构比较、交易后复盘。

Overlay 当前精选 20 项外部能力，其中已被 CIS / Anthropic 覆盖的能力只做路由映射，缺失能力以 CIS Adapter 形式补齐。**不得因为 Skill 名称相同就声称第三方代码已运行。** Adapter 默认状态为 `methodology_adapter_unvalidated`，需要经验阈值、统计效果或 edge 证明的部分必须继续走 Backtest / Evaluation，而不能包装成已验证策略。

Daisy Financial Research 与 InvestSkill 中的 point-in-time、防前视、数值校验、数据验证门和 decision-log 设计仅作为 CIS Evidence / Performance 的实现参考，不建立第二套总控、第二套评分权威或自动动作链。

## WorldQuant BRAIN / Alpha Research Source

WorldQuant BRAIN 在 CIS 中只定位为**外部 Alpha 候选来源**，不属于 CIS Core，也没有最终动作权。

```text
WorldQuant BRAIN export / 合法 API JSON
        ↓
extensions/alpha_research/worldquant/alpha_import.py
        ↓
cis.alpha_candidate.v1
        ↓
alpha_validator + factor/OOS diagnostics
        ↓
CIS Evidence / Risk / Portfolio Review
```

边界：

- 第一版不在仓库保存 BRAIN 密码、API key 或 session credential；
- 不自动提交/发布 Alpha；
- 不自动连接 Broker 或发送 live order；
- 导入结果固定 `source=worldquant_brain`、`research_status=unreviewed`、`decision_authority=none`；
- BRAIN Sharpe / Turnover / Fitness 等指标通过只能进入 `candidate_for_cis_validation`；
- 必须继续检查经济解释、数据泄漏/前视偏差、样本外、换手/成本/容量、相关性/分散化。

BRAIN 暂时不可访问时，CIS 可继续用用户提供的合法导出结果或本地 Alpha 研究工具；Alpha Research 故障不得阻塞普通单股分析。

## Buffett / 其他可选方法

任何外部投资方法都只能作为可选视角或证据增强，不得覆盖 CIS 的 Evidence、Risk、Score、Critical Dimension / Context Checks、Regime、Tactical Price/RR Gate、四层交易、ETF/QDII 和组合门。

## 数据连接器

- 代码/Skill 可用不等于数据已授权或实时；
- 行情、财报、新闻、宏观、机构持仓、资金流必须记录实际来源和 `as_of`；
- 短线行情必须记录 exchange、quote timestamp，并由 CIS 验证 regular / premarket / afterhours / last_close 语义及 quote freshness；
- active quote 的 `quote_timestamp` 本身必须属于所声明的 session，不能把盘前旧报价包装成 regular live；
- 历史研究必须使用 point-in-time 数据，禁止 look-ahead leakage；
- 数据不可用时可降级到公开资料/用户资料，但必须说明覆盖限制。

## Optional Research Tooling

Quant、Backtest、Prediction Ledger 和 Performance/Evaluation 是 CIS 仓库中的**可选外围研发工具**，统一位于：

```text
extensions/research_tooling/
```

Alpha Discovery / Validation 是单独的可选研究层：

```text
extensions/alpha_research/
```

它们不依赖外部 LLM，但也不属于日常单股 Core。只有筛选、Alpha 研究、规则验证、记录/复盘/校准任务才调用；其故障不得阻塞 CIS Core。Market Regime 与 Tactical Price/RR Gate 仍属于 CIS Core 的按需分析层。
