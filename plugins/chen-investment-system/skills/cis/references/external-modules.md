# CIS 外部模块适配与降级

外部模块的“存在/可访问”和“本次任务已就绪”是两个独立状态。每次调用前都要检查，不得从 README、历史记录、聊天记忆或模块名称推断当前可用。

## Anthropic Financial Services（首选专业 Skills 上游）

Anthropic `financial-services` 是 CIS 当前首选的专业金融 Skill 上游，用于补充机构化财务建模、估值、业绩研究、覆盖研究、竞争分析、论点跟踪与催化剂管理。

- 上游：`https://github.com/anthropics/financial-services`
- 许可证：Apache License 2.0（每次重大升级或重新分发前重新核验）。
- CIS 不把 Anthropic 的 Agent 当作最终投资决策者；只采用与当前子问题匹配的专业 Skill/方法。
- CIS 总控、证据门、风险门、八维统一评分、四层交易框架、跨境 ETF/QDII 纪律、组合数据门和最终中文研究姿态继续由本仓库拥有。

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

按以下优先级判断：

1. `live_upstream`：本次环境可读取 Anthropic GitHub 上游的对应 `SKILL.md`，先读取当前 `main` 版本再执行；这是首选方式，可避免本地快照漂移。
2. `vendored_snapshot`：当前安装包中存在已同步并带上游 commit/SHA 的快照，可使用快照，但必须记录快照版本。
3. `limited`：上游不可读取且无已验证快照；CIS 只能用自身证据纪律和基础方法完成有限分析，不得声称运行了 Anthropic Skill。
4. `blocked`：缺失专业 Skill 或关键数据会迫使系统猜测时，停止该子模块并列出最小补充要求。

### 调度边界

- 用户调用“陈氏投资系统”时，Anthropic Skill 只能作为 CIS 子模块，不能绕过总控直接发布最终研究姿态。
- 专业 Skill 的结论必须返回 CIS，经过证据审计、风险门、冲突处理和评分覆盖检查。
- 不得把 Anthropic Skill 自带的数据源假设视为当前环境已连接；连接器必须在本次任务实际验证。
- Anthropic Skill 中与 Claude/Cowork/Office JS/MCP 等特定运行时绑定的工具指令，只在当前环境真实具备对应能力时执行；否则保留金融方法，替换为当前可调用的等价工具或标记限制。
- 不得为了“使用上游”而牺牲 CIS 的来源、截止时间、组合数据门和四层交易纪律。

## Buffett

Buffett 是专业定性分析模块/外部依赖，用于商业模式、商业质量、护城河、管理层诚信与能力、资本配置、所有者收益、卖出纪律和长期所有者视角。

- 上游：`https://github.com/agi-now/buffett-skills`
- 本仓库不包含上游源码。
- 发布本版本时，上游未提供明确 LICENSE；安装或分发前必须重新核验。
- 本项目与该上游无隶属、合作或背书关系。

### 调度边界

- Buffett 只返回定性所有权判断，不拥有 CIS 最终结论。
- 不得用护城河判断替代财务核验、估值、实时数据或组合风险。
- CIS 必须把 Buffett 结果与财务、估值、业绩、宏观、组合和风险证据综合。
- 出现冲突时，解释差异来自资料、预测、估值输入、方法还是时间跨度；不得机械平均。

### 缺失时的降级

- 未安装：`capability_status: unavailable`。
- 有等价公司资料、但缺少专用 Buffett Skill：`runtime_readiness: limited`；CIS 可整理一般定性证据，但必须说明“未运行 Buffett 模块”。
- 用户的问题必须依赖完整 Buffett 框架、且没有可替代资料：`runtime_readiness: blocked`；只列出最小补充要求。
- Buffett 不可用不得阻止 CIS 总控、证据登记、风险门和其他可用模块运行。

## 数据连接器

- 插件安装不等于连接器已授权。
- 只有本次任务实际执行并验证过的连接器才可标为可用。
- 连接器不可用时，可使用用户资料或公开资料替代；必须记录 `as_of`、资料期间、来源等级和覆盖限制。
