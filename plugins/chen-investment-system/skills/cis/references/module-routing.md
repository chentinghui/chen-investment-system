# CIS 0.4.2 模块路由

## 总原则

CIS 是唯一用户入口和最终质量控制层，但**不是所有工具都属于 Core**。

- 单股票/上市公司研究：默认只走 CIS Core；
- 大股票池筛选：按需调用 `extensions/research_tooling/quant_factor_engine.py`；
- 专业估值/财报/模型：按需调用 Anthropic Financial Services；
- 当前市场环境显著影响交易计划：加 Market Regime；
- 新规则/因子需要证明有效：按需调用 Backtest Extension；
- 用户明确要求历史记录/复盘/校准：按需调用 Prediction/Evaluation Extension；
- 原版 TradingAgents Python：仅用户明确要求运行/测试时调用。

## 默认路由

| 用户意图 | 默认核心 | 可选增强 | CIS 最终校验 |
|---|---|---|---|
| 一般股票研究 | ChatGPT-native TradingAgents Methodology | Anthropic（按需） | Evidence + Risk + Critical Dimensions + Score |
| 基本面+技术+新闻综合 | ChatGPT-native Methodology | — | Evidence + Score |
| 多空观点 | Bull/Bear 独立反证 | Research Manager | 冲突保留与裁决 |
| 价值区间/DCF/Comps | ChatGPT-native 上下文 | Anthropic DCF/Comps | valuation + Evidence |
| 财报前后 | ChatGPT-native News/Fundamentals | Anthropic Earnings | catalyst/valuation 更新 |
| 买入/卖出/持有 | ChatGPT-native Methodology | Regime（按需） | Critical Dimensions + 四层交易 + Portfolio Gate |
| 大股票池 Top N | CIS 受理 | **Quant Extension** | 候选再回到 CIS Core 深研 |
| 量化规则是否有效 | CIS 受理 | **Backtest Extension** | 不自动改生产规则 |
| 当前市场环境 | Market Regime | 宏观证据 | 不直接触发买卖 |
| ETF / QDII | CIS ETF 模块 | 可验证产品数据 | ETF/QDII专属纪律 |
| 组合再平衡 | 单标的研究 + Regime | Portfolio Gate | 真实组合数据门 |
| 历史复盘/评分校准 | CIS 受理 | **Prediction/Evaluation Extension** | 不自动改生产权重 |
| 运行原版 TradingAgents | 原版 local/remote | A/B 验证 | external_decision_candidate 仅作输入 |

## Critical Dimension 路由

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
earnings  → fundamentals + catalyst_macro + risk_resilience
```

关键维度缺失时，即使 coverage >= 85%，仍只能 `provisional`。

## Optional Research Tooling

统一位于：

```text
extensions/research_tooling/
```

路由规则：

- Quant：只有股票池规模足够大、明确要求排名/筛选/Top N 时运行；横截面必须同一 `as_of`；
- Backtest：任何准备升级成默认规则的因子/阈值/权重才运行；
- Prediction/Evaluation：只有用户明确要求记录、复盘或校准时运行；
- 单股分析不得因为这些文件存在而自动运行；
- Extension 故障不得阻塞 CIS Core。

## Market Regime 路由

Regime 只修正环境、安全边际和交易节奏，不直接覆盖公司基本面，也不产生机械买卖信号。

## TradingAgents 上游检查

- 读取 `upstream-status.json`；
- 7 天 TTL 未到：不访问上游；
- TTL 到期：下一次股票研究执行 `check_tradingagents_upstream.py` 的同等逻辑，只检查 SHA；
- 新 SHA → `review_required`，本次仍用稳定基线；
- 不使用定时 GitHub Actions 监控。

## TradingAgents 原版运行

只有真实 `.propagate()` 成功且结果请求身份匹配，才能说程序已执行。即便 `execution_status=success` / `runtime_readiness=remote_ready`，研究质量仍需 CIS Evidence/Risk/Score 复核。

## 防重叠规则

- ChatGPT-native Analyst 已覆盖的职责不重复跑同职责 fallback Agent；
- Quant 只筛选，不重复做最终公司研究；
- Anthropic 只负责专业子问题，不拥有最终动作权；
- Market Regime 不重复技术分析，只提供环境层；
- Backtest/Evaluation 只验证和复盘，不自动修改生产规则；
- 最终顺序固定为：证据 → 多角色研究 → 专业增强 → Evidence/Risk → Critical Dimensions → CIS Score → Regime（按需）→ 四层/ETF/组合门 → 最终中文结论。
