# CIS 0.4.5 模块登记表

CIS 采用 **Core Analysis + External Engines + Optional Research Tooling** 分层，避免把筛选、回测、记录和绩效系统塞进日常单股分析链。

| 模块 | 作用 | 默认状态 | 所属层 | 最终动作权 |
|---|---|---|---|---|
| CIS Control Layer | 受理、Runtime Guard、最终中文结论 | `installed` | **Core** | **有** |
| ChatGPT-native TradingAgents Methodology | 基本面、技术、新闻、情绪、多空反证、Trader/Risk视角 | `default_methodology` | **Core** | 无 |
| TradingAgents TTL Checker | 7天缓存式上游 SHA 检查 | `installed` | **Core Runtime** | 无 |
| Evidence Audit | 来源、时效、新鲜度、前视偏差、冲突 | `fail_closed_gate` | **Core** | 质量门 |
| Risk Review | 尾部风险、论点失效、集中度/流动性 | `fail_closed_gate` | **Core** | 质量门 |
| Critical Dimension Gate | 按任务确保关键维度存在 | `installed` | **Core** | 质量门 |
| Tactical Context Checks | Price Context + Catalyst/Event Review 完成检查 | `installed` | **Core, tactical** | 质量门 |
| CIS Scoring | 八维加权 + coverage；短线仍保持 Research Grade 与交易赔率分离 | `production_heuristic_pending_calibration` | **Core** | 无单独动作权 |
| Market Regime Layer | profile化 risk_on / neutral / risk_off + fresh-signal filtering | `experimental` | **Core, 按需** | 无 |
| Price / Session Guard | US-equity common session baseline、quote observation session、freshness、last-close session 校验 | `installed` | **Core, tactical** | 质量门 |
| Tactical R/R Gate | Entry/Stop Type/Target/Chase Limit/RR + persistent Setup Lifecycle | `installed_baseline` | **Core, tactical** | 质量门 |
| Trading Framework | 趋势→价格→成交→风险；止盈+止损 | `installed` | **Core** | 质量门 |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | `installed` | **Core** | 质量门 |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | `installed` | **Core, 按需** | 质量门 |
| Anthropic Financial Services | DCF、Comps、财报、模型、竞争、论点/催化剂 | `upstream_preferred` | **External, 按需** | 无 |
| Original TradingAgents Runtime | 官方 Python 多 Agent 运行；secret-backed 仅 reviewed SHA | `explicit_test_only` | **External test** | 无 |
| QuantConnect LEAN | 首选策略级事件驱动回测；订单、费用、持仓路径和策略统计 | `external_optional` | **External quant, 按需** | 无 |
| Quant Factor Ranking Engine | 大股票池候选排序；同一 as_of、ticker 唯一、最小横截面观测 | `experimental` | **Extension** | 无 |
| Baseline Backtest Evaluator | `date,ticker,score,forward_return` 横截面因子/Top-N sanity check | `experimental_baseline` | **Extension** | 无 |
| Prediction / Evaluation | 可选研究记录、结果和校准；默认5/20/60交易日；公开 allowlist | `experimental_optional` | **Extension** | 无 |

外部 LEAN 适配层位于：

```text
integrations/lean/
```

外围研发工具统一位于：

```text
extensions/research_tooling/
```

## 路由边界

- 日常单股分析：只要求 Core；
- 短线/具体买点：Core 内增加 Price/Session Guard + Quote Freshness + Tactical R/R Gate；
- 大股票池/Top N：按需启用 Quant Extension；
- 可执行交易规则/策略有效性验证：首选 **QuantConnect LEAN**；
- 仅横截面 score/forward-return sanity check：可使用 Baseline Backtest Evaluator；
- 用户明确要求记录、复盘或校准：按需启用 Prediction/Evaluation Extension；
- External/Extension 故障不得阻塞 Core；
- 外部量化结果不能自动改生产评分权重或发布最终买卖动作。

## QuantConnect LEAN 状态边界

LEAN 由 CIS 外部独立维护，不 vendor、不复制源码、不作为 git submodule。CIS 只维护：

```text
integrations/lean/cis_lean_adapter.py
references/quantconnect-lean.md
```

状态分层：

```text
execution_status = success | invalid_input | unavailable | error
runtime_readiness = ready | lean_cli_missing | docker_missing | unavailable
research_quality = unreviewed
```

`execution_status=success` 只证明本次 LEAN 回测完成并解析出结果，不证明策略无偏差、稳健或适合实盘。最终仍受 `backtest-validation.md` 约束。

当前集成只做回测/结果解析，**不启用 LEAN live trading 或 Broker 自动执行**。

## 0.4.5 安全边界

Original TradingAgents Remote Runner 分为：

```text
Prepare/Analyze: contents: read
      ↓ Artifact
Trusted Publisher: contents: write, 无 LLM Secret, 不执行第三方代码
```

Cloud/secret-backed execution 只有当当前 upstream SHA 与 `reviewed_sha` 一致时才允许。NVIDIA profile 只使用 NVIDIA 固定 endpoint + `NVIDIA_API_KEY`；custom profile 只使用 HTTPS endpoint + `OPENAI_COMPATIBLE_API_KEY`。

## 状态说明

- `default_methodology`：日常默认由当前 ChatGPT 会话执行的方法论；
- `installed_baseline`：已确定性实现，但阈值仍需未来样本验证；
- `external_optional`：外部可调用能力，不属于默认单股研究链；
- `experimental`：已有代码/规则，但尚未充分样本外验证；
- `experimental_baseline`：轻量研究 evaluator，不冒充完整策略回测引擎；
- `experimental_optional`：实验能力且不属于默认分析链；
- `explicit_test_only`：只有用户明确要求原版运行/系统测试时使用；
- `upstream_preferred`：专业方法首选上游，必须逐次确认可访问性；
- `fail_closed_gate`：没有明确 pass 就视为未通过。
