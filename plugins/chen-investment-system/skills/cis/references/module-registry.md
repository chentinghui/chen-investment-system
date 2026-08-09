# CIS 0.4.4 模块登记表

CIS 采用 **Core Analysis + Optional Research Tooling** 分层，避免把筛选、回测、记录和绩效系统塞进日常单股分析链。

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
| Price / Session Guard | XNAS/XNYS 时段推导、quote freshness、last-close session 校验 | `installed` | **Core, tactical** | 质量门 |
| Tactical R/R Gate | Entry/Stop Type/Target/Chase Limit/RR + Setup Lifecycle | `installed_baseline` | **Core, tactical** | 质量门 |
| Trading Framework | 趋势→价格→成交→风险；止盈+止损 | `installed` | **Core** | 质量门 |
| ETF / QDII Gate | 产品身份、溢价、申赎、时差、流动性 | `installed` | **Core** | 质量门 |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | `installed` | **Core, 按需** | 质量门 |
| Anthropic Financial Services | DCF、Comps、财报、模型、竞争、论点/催化剂 | `upstream_preferred` | **External, 按需** | 无 |
| Original TradingAgents Runtime | 官方 Python 多 Agent 运行 | `explicit_test_only` | **External test** | 无 |
| Quant Factor Ranking Engine | 大股票池候选排序 | `experimental` | **Extension** | 无 |
| Backtest / Validation | 因子/规则/阈值历史验证 | `experimental` | **Extension** | 无 |
| Prediction / Evaluation | 可选研究记录、结果和校准；默认5/20/60交易日 | `experimental_optional` | **Extension** | 无 |

外围研发工具统一位于：

```text
extensions/research_tooling/
```

## 路由边界

- 日常单股分析：只要求 Core；
- 短线/具体买点：Core 内增加 Exchange-aware Price/Session Guard + Quote Freshness + Tactical R/R Gate；
- 大股票池/Top N：按需启用 Quant Extension；
- 规则有效性验证：按需启用 Backtest Extension；
- 用户明确要求记录、复盘或校准：按需启用 Prediction/Evaluation Extension；
- Extension 故障不得阻塞 Core；
- Extension 不能自动改生产评分权重或发布最终买卖动作。

## 状态说明

- `default_methodology`：日常默认由当前 ChatGPT 会话执行的方法论；
- `installed_baseline`：已确定性实现，但阈值仍需未来样本验证；
- `experimental`：已有代码/规则，但尚未充分样本外验证；
- `experimental_optional`：实验能力且不属于默认分析链；
- `explicit_test_only`：只有用户明确要求原版运行/系统测试时使用；
- `upstream_preferred`：专业方法首选上游，必须逐次确认可访问性；
- `fail_closed_gate`：没有明确 pass 就视为未通过。
