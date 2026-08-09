# CIS 外部模块适配与降级

外部模块的“存在/可访问”和“本次任务已就绪”是两个独立状态。每次调用前都要检查，不得从 README、历史记录、聊天记忆或模块名称推断当前可用。

## TradingAgents（默认通用研究核心）

TradingAgents 是 CIS 0.3.0 默认的股票研究与候选决策核心，用于基本面、技术、新闻、情绪、多空辩论、Trader、Risk Debate 与 Portfolio Manager 链路。

- 上游：`https://github.com/TauricResearch/TradingAgents`
- 当前核验（2026-08-09）：上游 README 标示 v0.3.1（2026-07）。
- 许可证：Apache License 2.0；每次 vendoring、再分发或重大升级前重新核验。
- 详细边界和运行状态见 `tradingagents.md`。
- CIS 默认引用/调用上游，不复制其完整源码。

### 运行优先级

1. `installed_ready`：`tradingagents` Python 包可导入，模型/API/数据源就绪，实际 `.propagate()` 成功。
2. `installed_limited`：包可运行但部分数据源、模型或市场能力缺失；仅使用可验证部分。
3. `upstream_only`：只能读取上游方法/架构，当前环境无法执行；不得声称已运行。
4. `unavailable`：上游不可读取且包不可用。
5. `blocked`：任务必须依赖该核心，但继续会迫使系统猜测。

### 决策边界

- TradingAgents `Portfolio Manager` 输出统一适配为 `external_decision_candidate`。
- 它不能覆盖 CIS 八维评分、coverage gate、证据门、四层交易框架、ETF/QDII纪律、组合数据门或个人投资规则。
- 代码持续更新不代表行情/新闻实时；每次必须记录实际数据提供商与 `as_of`。
- 历史研究必须防止 look-ahead leakage；任何超出 `analysis_date` 的证据不得进入当时决策。
- TradingAgents 失败时，CIS 自写专家只作为 fallback adapters，不得伪造外部核心结果。

## Anthropic Financial Services（首选专业金融 Skills 上游）

Anthropic `financial-services` 是 CIS 当前首选的专业金融 Skill 上游，用于机构化财务建模、估值、业绩研究、覆盖研究、竞争分析、论点跟踪与催化剂管理。

- 上游：`https://github.com/anthropics/financial-services`
- 许可证：Apache License 2.0（每次重大升级或重新分发前重新核验）。
- Anthropic Skills 是专业子问题工具，不是最终投资决策者。

### 首选专业 Skill 映射

| CIS 能力 | Anthropic 首选 Skill |
|---|---|
| DCF 估值 | `financial-analysis/skills/dcf-model` |
| 可比公司估值 | `financial-analysis/skills/comps-analysis` |
| 三表模型 | `financial-analysis/skills/3-statement-model` |
| 模型审计 | `financial-analysis/skills/audit-xls` |
| 数据清洗/标准化 | `financial-analysis/skills/clean-data-xls` |
| 竞争分析 | `financial-analysis/skills/competitive-analysis` |
| 业绩后分析 | `equity-research/skills/earnings-analysis` |
| 业绩前预览 | `equity-research/skills/earnings-preview` |
| 首次覆盖 | `equity-research/skills/initiating-coverage` |
| 模型更新 | `equity-research/skills/model-update` |
| 行业/主题研究 | `equity-research/skills/sector-overview` |
| 论点跟踪 | `equity-research/skills/thesis-tracker` |
| 催化剂日历 | `equity-research/skills/catalyst-calendar` |
| 选股/想法生成 | `equity-research/skills/idea-generation` |

完整适配规则见 `anthropic-financial-services.md`。

### 运行方式

1. `live_upstream`：可读取 Anthropic GitHub 当前上游目标 `SKILL.md`；首选。
2. `vendored_snapshot`：存在带上游 commit/SHA 的已验证快照。
3. `limited`：上游不可读取且无验证快照，只做有限分析。
4. `blocked`：缺失专业方法或关键输入会迫使系统猜测。

### 与 TradingAgents 的协作

- TradingAgents 负责通用研究团队和候选决策。
- Anthropic 负责 DCF/Comps/模型/财报等专业子问题。
- Anthropic 输出作为证据回到 CIS，也可用于校正 TradingAgents 的通用判断。
- 两者冲突时不得机械平均；按资料时点、口径、假设和方法解释。

## Buffett

Buffett 是可选的长期所有者定性模块，用于商业模式、商业质量、护城河、管理层、资本配置、所有者收益与卖出纪律。

- 上游：`https://github.com/agi-now/buffett-skills`
- 本仓库不包含上游源码。
- 上游许可证状态在安装或分发前必须重新核验。

Buffett 不拥有 CIS 最终结论，也不替代 TradingAgents 的默认通用研究链或 Anthropic 的专业估值模型。

## 数据连接器

- 插件/框架安装不等于连接器已授权。
- 只有本次任务实际执行并验证过的数据源才可标为可用。
- TradingAgents 自带/支持的数据 provider 也必须逐次记录可用性和 `as_of`。
- 连接器不可用时，可使用用户资料或公开资料替代；必须降低置信度并记录覆盖限制。
