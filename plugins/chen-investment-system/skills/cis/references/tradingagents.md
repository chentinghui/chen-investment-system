# TradingAgents 默认研究核心适配

TradingAgents 是 CIS 0.3.1 的默认通用股票研究/候选决策核心，但不是 CIS 的最终规则所有者。

- 上游：`TauricResearch/TradingAgents`，默认分支 `main`。
- 当前核验（2026-08-09）：上游 README 标示 v0.3.1（2026-07）。
- 许可证：Apache License 2.0；每次 vendoring、再分发或重大升级前重新核验。
- CIS 不复制 TradingAgents 完整源码；本地可执行时直接调用，否则优先使用本仓库 GitHub Actions 远程桥。

## 角色分工

TradingAgents 默认承担：Fundamentals、Technical/Market、News、Sentiment、Bull/Bear、Research Manager、Trader、Risk Team 与 Portfolio Manager。

TradingAgents Portfolio Manager 输出只能记为 `external_decision_candidate`，不得直接成为 CIS 最终动作。

## CIS 保留的最终控制权

TradingAgents 不得覆盖：

- Runtime Guard 与当前 GitHub CIS 规则校验；
- 证据等级、资料截止时间、来源冲突与前视偏差审计；
- CIS 八维评分与 coverage gate；
- 四层交易框架（趋势 → 价格 → 成交 → 风险）；
- 盈利止盈 + 防守止损；
- ETF/QDII 产品身份、IOPV、历史溢价、申赎与时差纪律；
- 用户真实组合数据门；
- 用户个人投资规则；
- 最终中文研究姿态、证伪条件与复盘计划。

## 与 Anthropic Financial Services 的关系

TradingAgents 是通用研究团队和候选决策引擎；Anthropic Financial Services 是专业金融方法库。DCF、Comps、三表、模型审计、earnings analysis/preview、initiating coverage、model update、competitive analysis、thesis tracker、catalyst calendar 等专业子问题仍优先路由 Anthropic。

专业结果与 TradingAgents 结果都必须回灌 CIS 证据登记。冲突按资料时点、口径、假设、方法与期限解释，不能机械平均。

## 运行优先级

每次股票任务按以下顺序检查：

1. `installed_ready`：当前运行环境可导入 `tradingagents`，必要模型/API/数据源可用，并且 `.propagate()` 本次成功。
2. `installed_limited`：本地包可运行，但模型、数据源或目标市场存在限制；只采用可核验证据。
3. `remote_ready`：当前对话环境不能直接运行包，但可通过 GitHub 连接器写入请求，并由 `.github/workflows/cis-tradingagents.yml` 在 GitHub Actions 中真实安装/执行 TradingAgents；匹配请求的结果成功写回仓库。
4. `remote_limited`：远程执行链已触发，但模型、数据、Actions、上下文或同步环节失败；不得把失败/进行中的输出当本次结果。
5. `upstream_only`：只能读取上游方法/架构，本地与远程都未成功执行。
6. `unavailable`：上游不可读取且没有任何可执行路径。
7. `blocked`：任务关键结论必须依赖 TradingAgents，但继续会迫使系统猜测。

## GitHub Actions 远程桥

当本地 TradingAgents 不可执行，但 GitHub 连接器对 `chentinghui/chen-investment-system` 有写权限时，CIS 可以在**当前任务内**使用远程桥：

```text
ChatGPT / CIS
  ↓ 写入
runtime/tradingagents/request.json
  ↓ push 自动触发
.github/workflows/cis-tradingagents.yml
  ↓
安装 TauricResearch/TradingAgents 当前 main
  ↓
运行 TradingAgentsGraph(...).propagate(ticker, analysis_date)
  ↓
写回
runtime/tradingagents/results/<request_id>.json
runtime/tradingagents/results/<request_id>.md
  ↓
CIS 读取并校验
  ↓
external_decision_candidate
```

远程 runner：`scripts/run_tradingagents_remote.py`。

### 远程结果强制校验

只有同时满足以下条件，才能声称“本次 TradingAgents 已实际运行”：

- 读取的是 `runtime/tradingagents/results/<本次 request_id>.json`，不能读取笼统旧结果代替；
- `request_id` 与当前任务完全一致；
- `ticker` 与当前标的完全一致；
- `analysis_date` 与当前请求一致；
- `status == success`；
- `runtime_readiness == remote_ready`；
- `tradingagents_upstream_sha` 存在；
- `external_decision_candidate` 非空；
- 数据来源和 `as_of` 可被 CIS 证据审计。

只要有一项不满足，就不能把该文件当作本次 TradingAgents 决策。

## 远程模型后端

### 零密钥 baseline

默认远程 fallback 可在 GitHub Actions 中安装 Ollama，并运行 Qwen3。当前实现强制将 Ollama 服务上下文提高到 32K，避免 GitHub CPU 环境默认 4K 上下文无法容纳 TradingAgents 提示词。

零密钥模式主要解决“可执行性/兜底”，不等同于 frontier 云模型质量。正式 Standard/Deep 研究若配置了更高质量云模型，应优先使用云后端。

### 可选云后端

`run_tradingagents_remote.py` 支持 `backend=openai_compatible`。仓库存在 `TRADINGAGENTS_API_KEY` secret 且请求明确给出 `backend_url`、模型 ID 时，可以在同一架构下切到兼容端点，无需修改 CIS 流程。

不得把 secret 写入 request、result、日志或普通仓库文件。

## selected_analysts 与研究模式

TradingAgents 原生支持 `selected_analysts`。远程桥允许：`market`、`fundamentals`、`news`、`social`。

建议路由：

- `quick`：只选择会改变当前问题结论的 1–2 个 analyst；不为完整性强行全开。
- `standard`：通常 `market + fundamentals + news`；只有市场情绪重要时加入 `social`。
- `deep`：四个 analyst 全开，并保留标准 Bull/Bear 与 Risk Debate。
- `holding_review`：选择与持仓问题相关的 analyst，之后必须执行 CIS 四层交易框架和组合门。

验收/运行时诊断可以把 debate/risk rounds 设为 0，但不能把这种轻量 smoke test 冒充完整 Deep 研究。

## 数据与防前视纪律

- 代码仓库更新不等于行情/新闻实时；每次必须记录实际数据 provider 与 `as_of`。
- 历史日期分析禁止使用晚于 `analysis_date` 的财报、新闻、价格或情绪。
- TradingAgents 输出本身不是 A/B 级证据；其中事实必须按底层来源重新评级。
- 模拟 Trader/Portfolio Manager 结论不等于真实成交能力。

## Fallback

本地和远程 TradingAgents 都不能形成有效结果时：

1. 不伪造 TradingAgents 输出。
2. 原 CIS 专家 Agent 以 `fallback_adapters` 身份按最小团队原则运行。
3. 专业金融任务仍优先使用可用的 Anthropic Financial Services Skills。
4. 最终输出明确标记本次 TradingAgents 状态及其对置信度的影响。
