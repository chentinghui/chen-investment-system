# Original TradingAgents Runtime Adapter（CIS 0.4.0）

本文件只定义**原版 TradingAgents Python** 的运行与验证规则。CIS 日常股票研究默认使用 `tradingagents-methodology.md` 的 ChatGPT-native 方法论，不要求运行本程序。

- 上游：`TauricResearch/TradingAgents`，默认分支 `main`。
- 许可证：Apache License 2.0；重大升级/再分发前重新核验。
- 本仓库不复制 TradingAgents 完整源码。

## 何时运行原版

仅在以下情况：

- 用户明确要求“运行原版 TradingAgents / 跑官方程序 / 系统测试”；
- 需要对 ChatGPT-native 方法论做 A/B 验证；
- 需要验证上游新 Agent / Prompt / Graph / Tool / Risk 流程是否值得吸收。

普通“分析 MU / NVDA能买吗 / QQQ要不要卖”不自动启动原版。

## 运行状态

1. `installed_ready`：当前环境可导入 `tradingagents`，模型/API/数据源可用，并且 `.propagate()` 本次成功。
2. `installed_limited`：包可运行但模型/数据/市场存在限制。
3. `remote_ready`：GitHub Actions 远程运行成功，结果身份完整匹配。
4. `remote_limited`：远程链路失败/超时/结果不完整。
5. `upstream_only`：只能读取上游方法/代码，未实际运行。
6. `unavailable`：上游和运行路径都不可用。
7. `blocked`：任务必须依赖原版结果但继续会迫使系统猜测。

## GitHub Actions 远程测试桥

```text
runtime/tradingagents/request.json
  ↓
.github/workflows/cis-tradingagents.yml
  ↓
每次重新 clone TauricResearch/TradingAgents 当前 main
  ↓
TradingAgentsGraph(...).propagate(...)
  ↓
runtime/tradingagents/results/<request_id>.json
  ↓
CIS 校验
  ↓
external_decision_candidate
```

远程 runner：`scripts/run_tradingagents_remote.py`。

只有同时满足以下条件，才能声称“本次原版 TradingAgents 已实际运行”：

- request_id 完全匹配；
- ticker 完全匹配；
- analysis_date 完全匹配；
- `status == success`；
- `runtime_readiness == remote_ready`；
- `tradingagents_upstream_sha` 存在；
- `external_decision_candidate` 非空；
- 数据来源与 `as_of` 可被 CIS 审计。

## 模型后端纪律

原版运行只是显式测试能力，不再为 CIS 设定长期“默认云模型”。模型端点可能下线、限流或改名，因此每次测试必须：

1. 先验证当前模型 ID/端点仍可用；
2. 不把 API key 写入 request、result、日志或仓库文件；
3. 云后端只通过 GitHub Actions Secret 注入；
4. 模型失败不得冒充 TradingAgents 研究结果；
5. 模型强弱不能绕过 CIS Evidence、Risk、Score、Regime 和四层交易框架。

`backend=openai_compatible` 可用于 NVIDIA NIM 等兼容端点；零密钥 smoke test 可使用 Ollama，但它只用于可执行性验证，不代表正式研究质量。

## selected_analysts

远程桥支持 `market`、`fundamentals`、`news`、`social`。

- smoke test：可只开 1 个 Analyst，debate/risk rounds 可设 0；
- 完整原版测试：按当前上游能力设置 Analyst 与 debate/risk；
- 轻量 smoke test 不得包装成完整 Deep 研究。

## 与 CIS 的边界

原版 Portfolio Manager / Trader / BUY-SELL-HOLD 统一记为 `external_decision_candidate`，不得覆盖：

- GitHub Runtime Guard；
- Evidence / `as_of` / look-ahead 审计；
- Quant 与 Backtest 规则；
- CIS 八维评分；
- Market Regime；
- 四层交易与止盈/止损；
- ETF/QDII纪律；
- 用户真实组合门；
- 最终中文研究姿态。

## 上游更新

`.github/workflows/cis-tradingagents-upstream-watch.yml` 定期检测上游 `main` SHA。

SHA 变化只会把 `runtime/tradingagents/upstream-status.json` 标记为 `review_required`；不会自动覆盖 `tradingagents-methodology.md`。只有审查确认研究逻辑有价值后才人工/ChatGPT 更新方法论并记录 `reviewed_sha`。
