# CIS 0.4.2 模块路由

## 总原则

CIS 是唯一用户入口和最终质量控制层。

- 单股票/上市公司研究：默认 `ChatGPT-native TradingAgents Methodology`。
- 大股票池筛选：先 `Quant Factor Ranking Engine`，再对候选做多角色深研。
- 专业估值/财报/模型：按需 `Anthropic Financial Services`。
- 当前市场环境显著影响交易计划：加 `Market Regime Layer`。
- 新规则/因子需要证明有效：走 `Backtest / Validation`。
- 历史研究需要校准：写入 `Prediction Ledger`，到期后走 `Performance Loop`。
- 原版 TradingAgents Python：仅用户明确要求运行/测试时调用。

## 默认路由

| 用户意图 | 默认核心 | 增强/验证 | CIS 最终校验 |
|---|---|---|---|
| 一般股票研究 | ChatGPT-native TradingAgents Methodology | Anthropic（按需） | Evidence + Risk + Critical Dimensions + Score |
| 基本面+技术+新闻综合 | ChatGPT-native Methodology | — | Evidence + Score |
| 多空观点 | Bull/Bear 独立反证 | Research Manager | 冲突保留与裁决 |
| 价值区间/DCF/Comps | ChatGPT-native 上下文 | Anthropic DCF/Comps | valuation + Evidence |
| 财报前后 | ChatGPT-native News/Fundamentals | Anthropic Earnings | catalyst/valuation 更新 |
| 买入/卖出/持有 | ChatGPT-native Methodology | Regime（按需） | Critical Dimensions + 四层交易 + Portfolio Gate |
| 大股票池 Top N | Quant Factor Ranking | Methodology 深研 Top N | CIS Score |
| 量化规则是否有效 | Backtest / Validation | Performance Loop | 不自动改生产规则 |
| 当前牛/熊/风险环境 | Market Regime | 宏观证据 | 不直接触发买卖 |
| ETF / QDII | CIS ETF 模块 | 可验证产品数据 | ETF/QDII专属纪律 |
| 组合再平衡 | 单标的研究 + Regime | Portfolio Gate | 真实组合数据门 |
| 历史复盘/评分校准 | Prediction Ledger | Performance Loop | 不自动改生产权重 |
| 运行原版 TradingAgents | 原版 local/remote | A/B 验证 | external_decision_candidate 仅作输入 |

## Critical Dimension 路由

评分前根据任务选择 `decision_context`：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

关键维度缺失时，即使 coverage >= 85%，仍只能 `provisional`。

## Quant 路由规则

- 只有股票池规模足够大、用户明确要求排名/筛选/Top N，或需要系统化候选生成时运行。
- 所有横截面行必须共享同一 `as_of`。
- `max_drawdown_1y` 可接受负号回撤或正的回撤绝对值；引擎统一转换为绝对值后按“越小越好”排序。
- `quant_score` 与 `cis_score` 分开。
- baseline 因子权重标记 `experimental_uncalibrated`。
- 缺失因子不补零；coverage 不足时不得强行排名为正式结果。

## Backtest 路由规则

任何准备升级成默认规则的因子/阈值/权重，必须检查 look-ahead、survivorship、universe drift、按换手率计算的成本与样本外稳定性。

## Market Regime 路由规则

Regime 只修正宏观/风险环境、安全边际和交易节奏，不直接覆盖公司基本面，也不产生机械买卖信号。布尔输入必须严格类型校验。

## TradingAgents 上游检查

- 读取 `upstream-status.json`。
- 7 天 TTL 未到：不访问上游。
- TTL 到期：下一次股票研究执行 `check_tradingagents_upstream.py` 的同等逻辑，只检查 SHA。
- 新 SHA → `review_required`，本次仍用稳定基线。
- 不使用定时 GitHub Actions 监控。

## TradingAgents 原版运行规则

只有真实 `.propagate()` 成功且结果请求身份匹配，才能说“程序已执行”。即便 `execution_status=success` / `runtime_readiness=remote_ready`，研究质量仍默认为 `unreviewed`，必须再过 CIS Evidence/Risk/Score 等质量门。

## 防重叠规则

- ChatGPT-native Analyst 已覆盖的职责不重复跑同职责 fallback Agent。
- Quant 负责筛选，不重复做最终公司研究。
- Anthropic 负责专业子问题，不拥有最终动作权。
- Market Regime 不重复技术分析，只提供环境层。
- Backtest/Performance 只验证和校准，不自动修改生产规则。
- 最终顺序固定为：候选/证据 → 多角色研究 → 专业增强 → Evidence/Risk → Critical Dimensions → CIS Score → Regime（按需）→ 四层/ETF/组合门 → 最终中文姿态 → Prediction Ledger（按需）。
