# Original TradingAgents Runtime Adapter（CIS 0.4.5）

本文件只定义**原版 TradingAgents Python** 的运行与验证规则。CIS 日常股票研究默认使用 `tradingagents-methodology.md` 的 ChatGPT-native 稳定方法论，不要求运行本程序。

- 上游：`TauricResearch/TradingAgents`，默认分支 `main`。
- 许可证：Apache License 2.0；重大升级/再分发前重新核验。
- 本仓库不复制 TradingAgents 完整源码。

## 何时运行原版

仅在以下情况：

- 用户明确要求“运行原版 TradingAgents / 跑官方程序 / 系统测试”；
- 需要对 ChatGPT-native 方法论做 A/B 验证；
- 需要验证上游新 Agent / Prompt / Graph / Tool / Risk 流程是否值得吸收。

普通“分析 MU / NVDA能买吗 / QQQ要不要卖”不自动启动原版。

## 运行状态必须拆分

```text
execution_status = success | error | invalid_input | unavailable
runtime_readiness = installed_ready | installed_limited | remote_ready | remote_limited | upstream_only | blocked

evidence_audit_status = not_run | pass | unresolved | fail
research_quality = unreviewed | accepted | rejected
```

- `execution_status=success`：程序完成。
- `runtime_readiness=remote_ready`：远程程序链路完成。
- `evidence_audit_status=not_run`：尚未通过 CIS 证据审计。
- `research_quality=unreviewed`：结果只能作为候选，不能直接用作最终投资判断。

## GitHub Actions 远程测试桥：安全隔离

0.4.5 将第三方代码执行与仓库写权限彻底拆开：

```text
显式 request
  ↓
Prepare Job（contents: read）
  ├─ 校验 request
  ├─ 读取 reviewed_sha
  └─ 固定本次 upstream SHA
  ↓
Analyze Job（contents: read）
  ├─ 只 checkout 固定 SHA
  ├─ 运行 TradingAgents
  ├─ 按 provider profile 只注入一项所需 Secret
  └─ 产出 result Artifact
  ↓
Trusted Publisher Job（contents: write，无 LLM Secret，不运行第三方代码）
  ↓
runtime/tradingagents/results/<request_id>.json
```

因此第三方 TradingAgents 代码所在 Job **没有仓库写 token**。

### Secret-backed 上游审查门

- `backend=ollama`：零云密钥，可对当前上游 `main` 做显式 smoke test；
- `backend=openai_compatible`：只有当前 upstream SHA 与 `runtime/tradingagents/upstream-status.json` 的 `reviewed_sha` 完全一致时才允许执行；
- 如果 `main` 已变化：远程 cloud run 直接阻断，先完成上游审查；
- 不会为了“继续运行”而静默降级到旧 SHA，也不会把未审查最新代码暴露给云密钥。

这与 7 天 TTL 的日常方法论策略一致：**先发现变化，再审查，再允许 secret-backed 原版运行。**

## Provider / Secret 路由

`run_tradingagents_remote.py` 不再从多个 Secret 中任意 fallback。

```text
backend=ollama
provider_profile=local_ollama
→ 不使用云 Secret

backend=openai_compatible
provider_profile=nvidia
backend_url=https://integrate.api.nvidia.com/v1
→ 只允许 NVIDIA_API_KEY

backend=openai_compatible
provider_profile=custom
→ backend_url 必须为 HTTPS
→ 只允许 OPENAI_COMPATIBLE_API_KEY
```

NVIDIA Key 不得发送到任意自定义 endpoint。Custom endpoint 也不得 fallback 使用 NVIDIA Key。Request schema 不接受 `api_key` 等未知字段，invalid request 不回显原始 payload，避免把秘密写入公开 runtime 结果。

## 原版结果最低身份校验

只有同时满足以下条件，才能声称“本次原版 TradingAgents 程序已实际运行”：

- request_id 完全匹配；
- ticker 完全匹配；
- analysis_date 完全匹配；
- `execution_status == success`；
- `runtime_readiness == remote_ready` 或本地 `installed_ready`；
- `tradingagents_upstream_sha` 存在（远程）；
- `external_decision_candidate` 非空。

即使全部满足，也只能说**程序执行成功**。要成为可接受研究输入还必须：

- `evidence_audit_status == pass`；
- `research_quality == accepted`；
- 关键数据/事实通过 CIS as_of 和来源审计。

## 模型后端纪律

原版运行只是显式测试能力，不为 CIS 设定长期“默认云模型”。模型端点可能下线、限流或改名，因此每次测试必须：

1. 验证当前模型 ID/端点仍可用；
2. 不把 API key 写入 request、result、日志或仓库文件；
3. 云后端只通过 GitHub Actions Secret 注入，并使用 0.4.5 provider-profile 绑定；
4. 模型失败不得冒充 TradingAgents 研究结果；
5. 模型强弱不能绕过 CIS Evidence、Risk、Critical Dimension、Score、Regime 和四层交易框架。

## selected_analysts

远程桥支持 `market`、`fundamentals`、`news`、`social`。

- smoke test：可只开 1 个 Analyst，debate/risk rounds 可设 0；
- 完整原版测试：按当前上游能力设置 Analyst 与 debate/risk；
- 轻量 smoke test 不得包装成完整 Deep 研究。

## 与 CIS 的边界

原版 Portfolio Manager / Trader / BUY-SELL-HOLD 统一记为 `external_decision_candidate`，不得覆盖：

- GitHub Runtime Guard；
- Evidence / `as_of` / look-ahead 审计；
- Risk Review；
- Critical Dimension Gate；
- Quant 与 Backtest 规则；
- CIS 八维评分；
- Market Regime；
- Tactical R/R 与四层交易；
- ETF/QDII纪律；
- 用户真实组合门；
- 最终中文研究姿态。

## 上游更新

日常方法论更新采用 **7 天 TTL** 的使用时检查：`scripts/check_tradingagents_upstream.py` + `runtime/tradingagents/upstream-status.json`。

不使用定时 GitHub Actions。SHA 变化只标记 `review_required`，不会自动覆盖 `tradingagents-methodology.md`。原版显式测试仍以当时 upstream `main` 为目标，但 secret-backed 运行先经过 `reviewed_sha` 安全门；未审查最新 main 只允许零密钥 smoke test。
