# Anthropic Financial Services → CIS 适配规范

As-of: 2026-08-09

## 目标

将 `anthropics/financial-services` 作为 CIS 的首选专业金融 Skill 上游，同时保持 CIS 自己的总控、证据纪律、风险门、统一评分、四层交易框架、组合约束与中文最终结论。

上游仓库：`https://github.com/anthropics/financial-services`

许可证：Apache License 2.0。任何 vendoring、fork、再分发或大版本升级前必须重新核验上游许可证、路径和内容。

## 核心原则

1. CIS 是唯一用户入口和最终研究姿态所有者。
2. Anthropic Skill 负责专业方法，不负责 CIS 最终动作标签或 0–100 总分。
3. 每次运行优先读取上游 `main` 的目标 `SKILL.md`，避免长期依赖陈旧本地副本。
4. 如果使用本地快照，必须记录上游仓库、commit/SHA、同步日期和许可证。
5. 不把 Claude/Cowork/MCP/Office JS 等运行时假设硬套到当前环境；只执行当前环境真实具备的工具能力。
6. 上游 Skill 输出必须转换为 CIS `agent-contract.md` / `io-contract.md`，再进入证据门、风险门和评分引擎。
7. Public Equity Investing 仅作为 legacy fallback，不再是默认专业上游。

## 上游 Skill 路由表

### Financial / Valuation

| 任务 | 上游路径 | CIS 主要消费者 |
|---|---|---|
| DCF | `plugins/vertical-plugins/financial-analysis/skills/dcf-model/SKILL.md` | 估值分析师 |
| Comps | `plugins/vertical-plugins/financial-analysis/skills/comps-analysis/SKILL.md` | 估值分析师 |
| 三表模型 | `plugins/vertical-plugins/financial-analysis/skills/3-statement-model/SKILL.md` | 基本面与财务分析师 |
| 模型审计 | `plugins/vertical-plugins/financial-analysis/skills/audit-xls/SKILL.md` | 基本面与财务分析师 / 证据审计员 |
| 数据清洗 | `plugins/vertical-plugins/financial-analysis/skills/clean-data-xls/SKILL.md` | 基本面与财务分析师 |
| 竞争分析 | `plugins/vertical-plugins/financial-analysis/skills/competitive-analysis/SKILL.md` | 成长与竞争分析师 |

### Equity Research

| 任务 | 上游路径 | CIS 主要消费者 |
|---|---|---|
| 财报后分析 | `plugins/vertical-plugins/equity-research/skills/earnings-analysis/SKILL.md` | 基本面与财务分析师 / 宏观与催化剂策略师 |
| 财报前预览 | `plugins/vertical-plugins/equity-research/skills/earnings-preview/SKILL.md` | 宏观与催化剂策略师 |
| 首次覆盖 | `plugins/vertical-plugins/equity-research/skills/initiating-coverage/SKILL.md` | 总控 + 多专家 |
| 模型更新 | `plugins/vertical-plugins/equity-research/skills/model-update/SKILL.md` | 基本面与财务分析师 |
| 行业/主题 | `plugins/vertical-plugins/equity-research/skills/sector-overview/SKILL.md` | 成长与竞争分析师 / 宏观与催化剂策略师 |
| 论点跟踪 | `plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md` | 总控 / 风险经理 |
| 催化剂 | `plugins/vertical-plugins/equity-research/skills/catalyst-calendar/SKILL.md` | 宏观与催化剂策略师 |
| 想法生成 | `plugins/vertical-plugins/equity-research/skills/idea-generation/SKILL.md` | 总控 / 成长与竞争分析师 |

## 当前不直接外包给上游的 CIS 核心能力

以下能力即使 Anthropic 存在相近工作流，也不允许覆盖 CIS 自有规则：

- 八维评分权重与 coverage gate；
- 证据等级、资料截止时间与冲突解释；
- 风险经理的 `risk_override`；
- 四层交易框架：趋势 → 价格 → 成交 → 风险；
- 盈利止盈 + 防守止损双向卖出；
- 跨境 ETF / QDII 产品身份、IOPV、历史溢价和申赎纪律；
- 持仓/权重/成本/资金需求不足时的组合数据门；
- 最终中文研究姿态、证伪条件和复盘计划。

## Runtime Guard

当用户明确说“陈氏投资系统”“投资总控”“用我的投资系统分析”或等价表达时：

1. 先读取 CIS 当前入口与必读 references。
2. 如果可访问 GitHub，优先核验 `chentinghui/chen-investment-system` 的 `main`；不得仅凭聊天记忆恢复旧流程。
3. 在需要专业金融 Skill 时，先查本表并尝试 Anthropic 上游。
4. 只有目标上游路径本次真实可读取，才可标记 `upstream_skill_status: live_upstream`。
5. 无法读取时，检查是否存在带版本信息的 vendored snapshot。
6. 两者都不存在时，标记 `limited/blocked`；不得自动切到旧 Public Equity Investing 并冒充新版 CIS。
7. 如果确需使用 legacy fallback，输出内部状态 `legacy_fallback: true`，并明确它不能改变 CIS 评分规则。
8. 任何外部模块返回后，必须回到 CIS：证据门 → 风险门 → 冲突处理 → 统一评分 → 四层/组合门（如适用）→ 最终结论。

## 适配规则

Anthropic Skill 中出现以下内容时按环境适配：

- `Claude` / `Cowork` / `Claude Code`：视为上游运行环境描述，不改变 CIS 总控身份。
- MCP provider：只有当前会话真实连接并成功读取时才使用；否则寻找当前环境可用的一手/权威来源。
- Office JS：只有 live Excel/Office 环境可用时执行；否则使用当前环境支持的 spreadsheet 工具。
- Python/openpyxl：仅在当前任务确实需要生成/验证工作簿时使用。
- 上游要求用户逐步确认但当前任务是非交互完整研究时：在不牺牲数据正确性的前提下，改为内部 checkpoint；若关键假设确实无法合理确定，再按 CIS 的“只询问会改变路线或结论的问题”规则处理。
- 上游的交易/推荐措辞不得直接变成 CIS 动作；最终姿态必须符合 CIS 的组合数据门和研究姿态词表。

## 上游漂移检查

至少在以下情况重新检查上游：

- Anthropic 更改仓库名、目录或许可证；
- Skill 路径返回 404；
- Skill 的核心方法、输出契约或依赖发生重大变化；
- CIS 大版本升级；
- 准备把上游文件 vendoring 到本仓库。

检查失败时，不猜测新路径。将模块降级，并记录需要人工/联网重新解析的上游路径。
