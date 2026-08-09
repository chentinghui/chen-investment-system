# 陈氏投资系统（Chen Investment System，CIS）

当前版本：**0.3.0**

CIS 是一个中文投资研究控制层。它不再自己维护一整套通用投资 Agent，而是：

- 用 **TradingAgents** 作为默认股票/上市公司多 Agent 研究核心；
- 用 **Anthropic Financial Services** 作为 DCF、Comps、三表、财报和模型等专业金融 Skills 上游；
- 由 **CIS** 保留证据门、八维评分、四层交易、ETF/QDII纪律、组合门、个人规则和最终中文研究姿态。

## 架构

```text
用户
  ↓
陈氏投资系统 CIS
  ↓
CIS Control Layer
  ├─ Runtime Guard / GitHub main 校验
  ├─ 个人投资规则
  ├─ 证据门 / 前视偏差检查
  ├─ 八维评分
  ├─ 四层交易框架
  ├─ ETF/QDII 溢价纪律
  └─ 组合数据门
  ↓
TradingAgents【默认通用研究核心】
  ├─ Fundamentals Analyst
  ├─ Technical Analyst
  ├─ News Analyst
  ├─ Sentiment Analyst
  ├─ Bull / Bear Researchers
  ├─ Research Manager
  ├─ Trader
  ├─ Risk Management Team
  └─ Portfolio Manager
  ↓
external_decision_candidate
  ↓
Anthropic Financial Services【按需专业增强】
  ├─ DCF / Comps
  ├─ 3-Statement Model
  ├─ Earnings Preview / Analysis
  ├─ Model Audit / Update
  ├─ Competitive Analysis
  └─ Thesis / Catalyst
  ↓
CIS 最终质量门
  ↓
证据审计 → 风险门 → 冲突解释 → CIS评分
  ↓
四层/ETF/组合门（如适用）
  ↓
最终中文研究姿态 + 证伪条件 + 复盘计划
```

## 1. TradingAgents 的定位

上游：`https://github.com/TauricResearch/TradingAgents`

CIS 0.3.0 将 TradingAgents 设为股票/上市公司研究的默认通用核心。当前核验（2026-08-09）上游 README 标示 **v0.3.1（2026-07）**，并使用 Apache License 2.0。

TradingAgents 负责：

- 通用基本面；
- 技术指标；
- 新闻与宏观事件；
- 情绪；
- Bull/Bear 多空辩论；
- Trader 候选方案；
- Risk Debate；
- Portfolio Manager 候选决策。

但它的最终判断在 CIS 中只能叫：

```text
external_decision_candidate
```

不能直接变成 CIS 的买入、卖出或持仓动作。

详细规则：`plugins/chen-investment-system/skills/cis/references/tradingagents.md`

可执行适配器：`plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py`

## 2. Anthropic Financial Services 的定位

上游：`https://github.com/anthropics/financial-services`

Anthropic Financial Services 处理 TradingAgents 不应该粗略替代的专业金融工作：

| 任务 | 首选专业 Skill |
|---|---|
| DCF | `dcf-model` |
| 可比估值 | `comps-analysis` |
| 三表模型 | `3-statement-model` |
| 模型审计 | `audit-xls` |
| 数据清洗 | `clean-data-xls` |
| 竞争分析 | `competitive-analysis` |
| 财报前 | `earnings-preview` |
| 财报后 | `earnings-analysis` |
| 首次覆盖 | `initiating-coverage` |
| 模型更新 | `model-update` |
| 行业研究 | `sector-overview` |
| 论点跟踪 | `thesis-tracker` |
| 催化剂 | `catalyst-calendar` |
| 想法生成 | `idea-generation` |

专业结果回到 CIS 的证据登记，并可用于修正 TradingAgents 的通用判断。

## 3. CIS 自己保留什么

这些能力不交给外部框架：

### Runtime Guard

用户说“陈氏投资系统”“投资总控”“用我的投资系统分析”时，先核验 GitHub `main` 当前规则，禁止仅凭聊天记忆恢复旧版本。

### 证据门

记录来源等级、发布日期、资料期间、`as_of`、事实/计算/假设/判断，并检查历史任务的前视偏差。

### 八维统一评分

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
| **合计** | **100** |

```text
coverage < 70%        → insufficient，不输出单一总分
70% <= coverage < 85% → provisional
coverage >= 85%       → 质量门通过后才可 decision_grade
```

TradingAgents 的 BUY/SELL/HOLD 或 rating 不得直接换算成 CIS 分数。

### 四层交易框架

涉及具体买卖/持仓价位时：

1. 趋势层：20/50/200 日均线；
2. 价格层：前高前低、突破、缺口、支撑压力；
3. 成交层：成交密集区、相对均量、量价确认；
4. 风险层：成本、权重、集中度、回撤承受力、资金需求。

TradingAgents Technical Analyst 只是输入，不替代这一步。

卖出必须同时覆盖：

- 盈利止盈；
- 防守止损。

### ETF / QDII 纪律

跨境 ETF / QDII 不默认交给 TradingAgents 做最终产品判断。必须核验：

- 精确基准；
- 产品身份；
- IOPV；
- 建仓与当前溢价；
- 产品自身历史溢价；
- 申赎/额度；
- 时差和流动性。

风险提示公告或绝对高溢价不能单独触发卖出。

### 组合数据门

只有真实持仓、权重、成本、基准、约束和资金需求足够时，才给精确仓位或再平衡比例。

TradingAgents Portfolio Manager 在不知道用户真实组合时，只能给一般候选判断。

## 4. CIS 自写 Agent 的新定位

`plugins/chen-investment-system/agents/` 继续保留，但不再作为默认股票研究团队。

它们只用于：

- `fallback adapter`：TradingAgents 不可运行时兜底；
- `conflict validator`：外部核心结果冲突时复核；
- `CIS-specific adapter`：证据审计、四层交易、组合门等 CIS 特有规则。

不得为了“看起来全面”重复运行同职责 Agent。

## 5. 标准研究流程

```text
Intake
  ↓
Runtime Guard
  ↓
TradingAgents Preflight
  ↓
TradingAgents 通用研究（股票任务）
  ↓
Anthropic 专业 Skills（按需）
  ↓
CIS 证据审计
  ↓
CIS 风险门
  ↓
关键冲突解释
  ↓
CIS 八维评分
  ↓
四层 / ETF / 组合门
  ↓
最终中文研究姿态
  ↓
证伪条件 + 复盘计划
```

## 6. TradingAgents 运行适配

官方 Python 包的基本调用形式以其当前上游 README 为准。CIS 自带包装器：

```bash
python plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py NVDA 2026-08-07 --probe-only
```

真实运行示例：

```bash
python plugins/chen-investment-system/skills/cis/scripts/run_tradingagents.py NVDA 2026-08-07 --provider openai
```

若 `tradingagents` 未安装，适配器返回 `upstream_only/unavailable`，CIS 必须降级，不能假装已运行。

代码更新与市场实时数据是两件事：TradingAgents 版本再新，也必须记录本次行情、新闻、情绪和宏观数据提供商及 `as_of`。

## 7. 研究模式

- `quick`：CIS + TradingAgents 快速链路；必要时最小专业 Skill。
- `standard`：CIS + TradingAgents + 独立证据审计 + 按需 Anthropic。
- `deep`：TradingAgents 全研究链 + Anthropic 专业模型 + CIS 质量门。
- `holding_review`：上述链路 + CIS 四层交易框架 + 真实组合数据门。

ETF/QDII 可绕过 TradingAgents 默认核心，直接走 CIS 专属产品流程。

## 8. 安装

### CIS

```bash
git clone https://github.com/chentinghui/chen-investment-system.git
cd chen-investment-system
codex plugin marketplace add .
codex plugin add chen-investment-system@chen-investment-system
```

### TradingAgents（外部依赖）

CIS 不复制 TradingAgents 源码。需要本地执行时，按其官方当前 README 安装，并配置所选模型与数据提供商。

CIS 自己的验证器不会把“能看到上游仓库”误认为“本地已安装可执行”。

## 9. 关键文件

```text
plugins/chen-investment-system/skills/cis/
├─ SKILL.md
├─ references/
│  ├─ tradingagents.md
│  ├─ anthropic-financial-services.md
│  ├─ system-workflow.md
│  ├─ module-registry.md
│  ├─ module-routing.md
│  ├─ agent-registry.md
│  ├─ agent-orchestration.md
│  ├─ scoring-engine.md
│  ├─ four-layer-trading-framework.md
│  └─ cross-border-etf-premium.md
└─ scripts/
   ├─ run_tradingagents.py
   ├─ score_cis.py
   └─ analyze_etf_premium.py
```

## 10. 许可证与归属

- CIS 自有内容：MIT License。
- TradingAgents：独立上游，当前核验为 Apache License 2.0；本仓库默认通过依赖/接口使用，不宣称其源码为 CIS 原创。
- Anthropic Financial Services：独立上游，当前适配记录为 Apache License 2.0；任何 vendoring/再分发前重新核验。

## 风险声明

CIS 用于研究组织、证据核验和分析辅助，不构成投资顾问服务、收益承诺或自动交易指令。外部框架、模型、数据和市场条件均可能出错或变化，最终投资决定仍需独立判断。
