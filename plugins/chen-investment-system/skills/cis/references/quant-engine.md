# CIS Quant Research Engine

Quant Engine 是 CIS 的**候选筛选与横截面排序层**，不是最终投资决策器，也不是自动交易器。

## 目标

- 从较大股票池中筛出值得进一步研究的候选；
- 把可量化的质量、成长、估值、动量和风险指标统一成可复现排序；
- 为 ChatGPT-native TradingAgents Methodology 提供候选集合，而不是让大模型从几百/几千只股票中凭印象选股；
- 为后续历史验证和评分校准提供结构化信号。

## 与 CIS 八维评分的边界

`quant_score` 与 `cis_score` 必须分开：

- `quant_score`：横截面筛选/排序，依赖可计算因子；
- `cis_score`：单标的综合研究评分，包含基本面、估值、竞争、技术、催化剂、风险等证据化判断。

不得把 `quant_score` 直接映射成买入/卖出，也不得把它直接替代 CIS 八维分数。

## 默认 baseline 因子

以下仅是**未校准 baseline**，必须通过回测与 Performance Loop 持续验证；权重不具有永久性：

| 因子 | 默认权重 | 方向 |
|---|---:|---|
| momentum_6m | 0.15 | 高优 |
| momentum_12m_ex1m | 0.10 | 高优 |
| revenue_growth | 0.10 | 高优 |
| eps_growth | 0.10 | 高优 |
| fcf_margin | 0.10 | 高优 |
| roe | 0.05 | 高优 |
| earnings_revision_90d | 0.10 | 高优 |
| valuation_fcf_yield | 0.10 | 高优 |
| relative_strength | 0.10 | 高优 |
| volatility | 0.05 | 低优 |
| max_drawdown_1y | 0.05 | 低优 |

## 计算纪律

1. 只在同一可比股票池/同一 `as_of` 做横截面排序。
2. 默认用 percentile rank，降低极端值对结果的影响。
3. 低优因子反向计分。
4. 缺失因子不补零，按可用权重重新归一化。
5. `factor_coverage < 70%` 时不输出正式 `quant_score`。
6. 必须记录股票池、数据截止时间、因子定义、方向、权重和缺失情况。
7. 财务指标必须使用 point-in-time 可得数据，禁止用后来重述/未来披露数据回填历史。

## 使用场景

- “今天最值得研究的美股有哪些？” → Quant Engine 先筛选，再进入 CIS 深研。
- “比较 50 只 AI 股票” → 先横截面排序，再对 Top N 做多角色研究。
- 单只股票买卖判断 → Quant 可以作为补充，不强制运行。

## 输出合同

```text
ticker
as_of
quant_score
factor_coverage
factor_scores
factor_weights
universe
status: ready | provisional | insufficient
```

## 禁止事项

- 不因回测结果好就自动下单；
- 不使用幸存者偏差股票池；
- 不使用未来财报/未来成分股信息；
- 不因单次高分跳过基本面、估值、风险和四层交易框架；
- 不把 baseline 权重宣传为已证明最优。

确定性脚本：`scripts/quant_factor_engine.py`。
