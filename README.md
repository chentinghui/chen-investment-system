# 陈氏投资系统（Chen Investment System，CIS）

陈氏投资系统是面向中文投资研究的统一总控插件。它把股票、上市公司、ETF、投资组合、财报、估值、宏观、成长、AI 行业、竞争分析与风险研究组织成一条有证据、有边界、可评分、可复盘的工作流。

当前版本：**0.2.0**

## 核心定位

CIS 不把任何单一专家、单一 Skill、单一估值方法或单一数据源当作最终决策者。

它负责：

- 定义研究问题；
- 校验当前 CIS 版本和资料截止时间；
- 检查数据与能力就绪度；
- 选择一个主专家和最少数量支持专家；
- 调度专业金融 Skills；
- 维护证据门与风险门；
- 解释专家冲突；
- 运行八维统一评分；
- 在涉及买卖时执行四层交易框架；
- 结合组合约束形成最终中文研究姿态；
- 生成证伪条件与复盘计划。

## 当前架构

```text
用户
  ↓
陈氏投资系统 CIS
  ↓
陈氏投资分析师（唯一总控 Agent）
  ↓
任务标准化 + Runtime Guard + 资料就绪度
  ↓
最小专家团队
  ├─ 基本面与财务分析师
  ├─ 成长与竞争分析师
  ├─ 估值分析师
  ├─ 技术与市场结构分析师
  ├─ 宏观与催化剂策略师
  ├─ 定位与资金流分析师
  ├─ 风险经理
  ├─ 证据审计员
  └─ 组合与仓位经理（组合数据门满足时）
  ↓
专业 Skills / 数据 / 外部方法
  ├─ Anthropic Financial Services（首选专业金融 Skill 上游）
  ├─ Buffett Skills（可选长期所有者视角）
  └─ 可用的一手数据、连接器和公开来源
  ↓
证据门 + 风险门 + 冲突处理
  ↓
CIS 八维统一评分（0–100）
  ↓
四层交易框架 / 组合约束（如适用）
  ↓
最终中文研究姿态 + 证伪条件 + 跟踪复盘
```

## CIS 自己维护什么

以下能力属于 CIS 核心，不交给外部 Skill 覆盖：

- 唯一总控和 Agent 编排；
- 证据等级、截止时间和冲突纪律；
- 风险门与风险经理 override；
- 八维评分与 coverage gate；
- 四层交易框架；
- 盈利止盈 + 防守止损双向卖出；
- 跨境 ETF / QDII 产品身份、IOPV、历史溢价和申赎纪律；
- 组合数据门；
- 中文研究姿态、证伪条件和复盘机制。

## Anthropic Financial Services 的定位

CIS 0.2.0 将 Anthropic `financial-services` 设为首选专业金融 Skill 上游。

上游仓库：

```text
https://github.com/anthropics/financial-services
```

当前主要映射包括：

| CIS 任务 | Anthropic Skill |
|---|---|
| DCF | `dcf-model` |
| 可比估值 | `comps-analysis` |
| 三表模型 | `3-statement-model` |
| 模型审计 | `audit-xls` |
| 数据清洗 | `clean-data-xls` |
| 竞争分析 | `competitive-analysis` |
| 财报后分析 | `earnings-analysis` |
| 财报前预览 | `earnings-preview` |
| 首次覆盖 | `initiating-coverage` |
| 模型更新 | `model-update` |
| 行业/主题研究 | `sector-overview` |
| 论点跟踪 | `thesis-tracker` |
| 催化剂管理 | `catalyst-calendar` |
| 投资想法生成 | `idea-generation` |

CIS 优先读取上游当前 `main` 的目标 `SKILL.md`，避免长期依赖陈旧副本。如果使用本地快照，必须记录上游 commit/SHA、同步日期和许可证。

Anthropic Skill 只提供专业子问题的方法和交付物，不能绕过 CIS 发布最终评分或投资姿态。

详细规则见：

- `plugins/chen-investment-system/skills/cis/references/anthropic-financial-services.md`
- `plugins/chen-investment-system/skills/cis/references/external-modules.md`

## Runtime Guard

用户说以下任一表达时：

```text
用陈氏投资系统分析……
启动投资总控……
用我的投资系统分析……
股票研究助手分析……
```

CIS 必须先：

1. 读取当前 CIS `SKILL.md`；
2. 读取必读 references；
3. 能访问 GitHub 时优先核验 `chentinghui/chen-investment-system` 的 `main`；
4. 禁止仅凭聊天记忆恢复旧权重或旧流程；
5. 专业金融任务按 Anthropic 上游映射执行；
6. 外部 Skill 结果必须回到 CIS，通过证据门、风险门、统一评分与必要的交易/组合框架后才能形成最终结论。

## 八维统一评分

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

缺失维度不补零、不猜测。

```text
coverage < 70%        → insufficient，不输出单一总分
70% <= coverage < 85% → provisional
coverage >= 85%       → 质量门通过后才可 decision_grade
```

分数不是自动交易信号。

## 四层交易框架

涉及买入、持有、加仓、减仓、止盈、止损、退出或具体价位时，固定按以下顺序：

1. **趋势层**：20日、50日、200日均线及趋势状态；
2. **价格层**：前高、前低、突破位、缺口、支撑和压力；
3. **成交层**：成交密集区、相对均量和量价确认；
4. **风险层**：成本、权重、集中度、回撤承受力、资金需求和分批比例。

固定原则：

> 先看趋势决定持有方向，再看价格寻找位置，再看成交确认真假，最后用风险层决定仓位。

卖出分析必须同时包含：

- 盈利止盈路径；
- 防守止损路径。

不得只给亏损后的卖点，也不得仅因已经盈利或涨幅较大就机械建议卖出。

## 研究模式

- `quick`：总控 + 1 个主专家；关键风险/证据才加审计。
- `standard`：总控 + 主专家 + 风险经理 + 证据审计员；按问题增加 1–2 个支持专家。
- `deep`：总控 + 3–6 个相关专家 + 风险经理 + 证据审计员。
- `holding_review`：总控 + 技术与市场结构 + 风险经理 + 组合与仓位经理 + 与论点相关专家。

默认模式：`standard`。

## 标准输入

```text
research_type: company | stock | ETF | portfolio | industry | macro | earnings
subject: 名称及股票/基金代码
research_question: 本次要回答的问题
mode: quick | standard | deep | holding_review
as_of: 价格、财报和市场数据截止时间
horizon: 短期 | 1-3年 | 3-10年
constraints: 市场、流动性、集中度、税务、伦理或其他限制
portfolio_context: 持仓、权重、成本、基准和资金需求
source_posture: 用户资料 | 已连接数据源 | 公开资料 | 混合
evidence_provided: 用户提供的文件、数字、链接或无
```

缺失字段只有在会改变研究路线或结论时才询问。

## 研究姿态

没有完整组合背景时，只使用：

- `进入深入研究`
- `继续观察`
- `暂时回避`
- `证据不足`

持仓、权重、成本、基准、约束和资金需求足够时，才可使用：

- `维持`
- `考虑增持`
- `考虑减持`
- `考虑退出`
- `暂不操作`

这些是研究姿态，不是自动交易指令。

## 关键文件

```text
plugins/chen-investment-system/
├─ agents/
│  ├─ chen-chief-investment-analyst.md
│  ├─ fundamental-financial-analyst.md
│  ├─ growth-competitive-analyst.md
│  ├─ valuation-analyst.md
│  ├─ technical-market-analyst.md
│  ├─ macro-catalyst-strategist.md
│  ├─ positioning-flow-analyst.md
│  ├─ risk-manager.md
│  ├─ evidence-auditor.md
│  └─ portfolio-manager.md
└─ skills/cis/
   ├─ SKILL.md
   ├─ references/
   │  ├─ system-workflow.md
   │  ├─ agent-registry.md
   │  ├─ agent-orchestration.md
   │  ├─ agent-contract.md
   │  ├─ scoring-engine.md
   │  ├─ module-registry.md
   │  ├─ module-routing.md
   │  ├─ anthropic-financial-services.md
   │  ├─ evidence-confidence.md
   │  ├─ four-layer-trading-framework.md
   │  ├─ cross-border-etf-premium.md
   │  └─ research-lifecycle.md
   └─ scripts/
```

## 安装

### GitHub repo marketplace

```bash
git clone https://github.com/chentinghui/chen-investment-system.git
cd chen-investment-system
codex plugin marketplace add .
codex plugin add chen-investment-system@chen-investment-system
```

安装或更新后，建议新建一个任务，使新的 Skills 被重新发现。

### Codex CLI

检查安装：

```bash
codex plugin list
```

若当前 CLI 只支持 Skills，可将以下目录复制到用户 Skills 目录：

```text
plugins/chen-investment-system/skills/cis
plugins/chen-investment-system/skills/stock-research-assistant
```

## 证据等级

- **A 级**：监管申报、交易所/基金公司正式资料、经审计财报、官方公告。
- **B 级**：公司投资者资料、业绩发布、管理层原始讲话、权威政府或行业数据。
- **C 级**：可靠市场数据商、主流财经媒体、方法透明的第三方研究。
- **D 级**：聚合页面、二手摘要、社交媒体、未披露方法的估算。

系统分别评估 `Evidence confidence`、`Thesis confidence` 和 `Valuation confidence`。

## 依赖与降级

| 能力 | 类型 | 不可用时 |
|---|---|---|
| CIS | 内置、必需 | 总控、证据登记、风险门和基础研究仍可运行 |
| Anthropic Financial Services | 首选专业上游 | 对应专业模块标记 `limited` 或 `blocked`；不得伪造已运行输出 |
| Buffett | 外部、可选 | 定性所有者模块标记 `limited` 或 `blocked` |
| 数据连接器 | 外部、按任务 | 改用用户资料或公开来源，并降低置信度 |

## 许可证与归属

本仓库 CIS 自有代码使用 MIT License。

Anthropic `financial-services` 是独立上游项目，当前适配记录显示其使用 Apache License 2.0；本仓库默认引用/读取其专业 Skills，不宣称其内容为 CIS 原创。任何 vendoring 或再分发前必须重新核验许可证并保留所需归属信息。

Buffett 上游的许可证状态需在安装或再分发前单独复核。

## 风险声明

本项目用于研究组织、证据核验和分析辅助，不构成投资顾问服务、证券推荐、收益承诺、交易指令、法律或税务意见。市场价格和公司信息会变化；任何结论都必须结合最新资料、个人目标、风险承受能力和独立判断。
