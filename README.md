# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.4.0**

CIS 是一个中文系统化投资研究控制层。它不自动下单，也不把单一模型/分数当成最终决策。

## 核心架构

```text
用户
  ↓
CIS Control Layer
  ↓
Quant Research Engine（大股票池按需预筛）
  ↓
ChatGPT-native TradingAgents Methodology
  ├─ Market / Technical
  ├─ Fundamentals
  ├─ News / Catalyst
  ├─ Sentiment / Positioning（按需）
  ├─ Bull / Bear 独立反证
  ├─ Research Manager
  └─ Trader / Risk / Portfolio Perspective（按需）
  ↓
Anthropic Financial Services（DCF / Comps / Earnings 等按需）
  ↓
CIS Evidence Gate + Risk Gate
  ↓
CIS 八维评分
  ↓
Market Regime（按需）
  ↓
四层交易 / ETF-QDII / Portfolio Gate
  ↓
最终中文研究姿态 + 证伪条件 + 复盘
  ↓
Performance Loop（历史校准）
```

## 0.4.0 主要变化

- 日常股票研究默认改为 **ChatGPT-native TradingAgents Methodology**，不再要求外部 LLM API 或每次运行 TradingAgents Python。
- 原版 TradingAgents Python 保留为显式测试/A-B 验证路径；远程测试每次重新拉取上游 `main`。
- 新增 TradingAgents 上游 SHA 自动检测；只标记 `review_required`，**不会自动覆盖 CIS 方法论**。
- 新增 **Quant Research Engine**：大股票池横截面因子筛选和排序。
- 新增 **Backtest / Validation**：验证因子、阈值、评分规则，检查前视/幸存者偏差和交易成本。
- 新增 **Market Regime Layer**：risk_on / neutral / risk_off 环境分类，用于安全边际和风险条件修正。
- 新增 **Performance Loop**：把历史 CIS 分数和未来实际收益对照，评估评分区分度并支持人工校准。
- 强化多角色独立性：Bull/Bear/Risk 必须尽量使用不同证据/机制，Research Manager 不得创造新事实。

## CIS 八维评分

| 维度 | 权重 |
|---|---:|
| fundamentals | 20 |
| growth | 15 |
| valuation | 15 |
| industry_competitive | 10 |
| technical | 15 |
| catalyst_macro | 10 |
| positioning | 5 |
| risk_resilience | 10 |

```text
coverage < 70%        → insufficient
70% <= coverage < 85% → provisional
coverage >= 85%       → 质量门通过后才可 decision_grade
```

缺失维度不补零、不猜测。最终动作不能只由分数决定。

## Quant Engine

Quant 解决的是“从大量股票中先找谁值得研究”，不是“直接决定买谁”。

默认 baseline 因子包括：动量、相对强弱、营收/EPS增长、FCF margin、ROE、盈利预期修正、FCF Yield、波动率和最大回撤。

baseline 权重目前标记为 **experimental_uncalibrated**，必须通过历史回测和样本外验证后才能调整为生产规则。

脚本：

```text
plugins/chen-investment-system/skills/cis/scripts/quant_factor_engine.py
plugins/chen-investment-system/skills/cis/scripts/backtest_factor_strategy.py
```

## Market Regime

Baseline 使用趋势、50日线斜率、市场广度、VIX、信用利差变化等信息，输出：

```text
risk_on | neutral | risk_off | insufficient
```

Regime 不直接产生买卖动作，只能影响宏观/风险证据、安全边际和交易节奏。

脚本：

```text
plugins/chen-investment-system/skills/cis/scripts/classify_market_regime.py
```

## Performance Loop

到达研究期限后，把 `cis_score` 与实际收益/基准收益对照，检查：

- 高分组是否获得更高未来收益；
- 高分组是否有更高超额收益；
- 不同 Regime 下是否稳定；
- 哪些维度存在系统性偏差。

脚本：

```text
plugins/chen-investment-system/skills/cis/scripts/evaluate_cis_predictions.py
```

脚本**不得自动修改生产权重**；所有权重变化必须经过样本外证据和人工/ChatGPT 审查。

## TradingAgents 上游同步

```text
TauricResearch/TradingAgents main SHA 变化
  ↓
.github/workflows/cis-tradingagents-upstream-watch.yml
  ↓
runtime/tradingagents/upstream-status.json = review_required
  ↓
审查 Agent / Prompt / Graph / Tool / Risk 流程
  ↓
只吸收明确有价值的变化
```

原版 TradingAgents 的显式测试路径仍在：

```text
.github/workflows/cis-tradingagents.yml
plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py
plugins/chen-investment-system/skills/cis/scripts/run_tradingagents_remote.py
```

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时固定执行：

1. 趋势：20/50/200 日均线；
2. 价格：前高前低、突破、缺口、支撑压力；
3. 成交：成交密集区、相对均量、量价确认；
4. 风险：成本、权重、集中度、回撤承受力、资金需求。

卖出必须同时分析盈利止盈和防守止损。

## ETF / QDII

跨境 ETF/QDII 必须核验产品身份、精确基准、IOPV、历史溢价、申赎/额度、时差和流动性，不能简单套用股票结论。

## 关键参考文件

```text
plugins/chen-investment-system/skills/cis/references/
├─ tradingagents-methodology.md
├─ tradingagents.md
├─ quant-engine.md
├─ backtest-validation.md
├─ market-regime.md
├─ performance-loop.md
├─ scoring-engine.md
├─ four-layer-trading-framework.md
├─ cross-border-etf-premium.md
└─ anthropic-financial-services.md
```

## 风险声明

CIS 用于研究组织、证据核验、筛选、回测和分析辅助，不构成收益承诺，也不连接 Broker 自动执行交易。模型、数据、因子和历史回测都可能失效，最终投资决定仍需独立判断。
