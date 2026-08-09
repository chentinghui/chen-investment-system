# CIS 模块登记表

CIS 0.3.0 将“最终控制层”和“默认研究核心”分离：CIS 保留规则、评分和最终质量门；TradingAgents 作为默认通用股票研究/决策候选引擎；Anthropic Financial Services 负责专业金融方法。

“能力状态”表示当前环境是否存在该能力；“本次就绪度”必须在每次任务运行前重新判断。外部模块不得在静态文件中预设为已安装。

| 模块 | 作用 | 默认能力状态 | 本次就绪条件 | 所有者 |
|---|---|---|---|---|
| CIS Control Layer | 受理、Runtime Guard、证据纪律、八维评分、四层交易、ETF/QDII纪律、最终中文结论与复盘 | `installed` | 总是可用 | `$cis` |
| TradingAgents Core | 基本面、技术、新闻、情绪、多空辩论、Trader、Risk Debate、Portfolio Manager 候选决策 | `upstream_default` | `tradingagents` 可执行且所需模型/数据源可用；或只能读取上游时标记 `upstream_only` | TauricResearch/TradingAgents |
| Anthropic Financial Services | DCF、Comps、三表、模型审计、财报研究、首次覆盖、模型更新、竞争分析、论点/催化剂 | `upstream_preferred` | 对应 Skill 可读取或有验证快照，且关键输入完整 | Anthropic Financial Services |
| Buffett | 长期所有者视角：商业质量、管理层、护城河、资本配置 | `external_optional` | Skill 已安装且公司资料足够 | `$buffett` |
| Evidence Audit | 来源、时效、前视偏差、事实/判断、跨模块冲突 | `installed` | 有可审计证据 | CIS |
| CIS Scoring | 八维 0–100 统一评分与 coverage gate | `installed` | 可用维度覆盖足够且质量门通过 | CIS |
| Trading Framework | 趋势→价格→成交→风险；盈利止盈 + 防守止损 | `installed` | 涉及具体买卖/持仓时执行 | CIS |
| ETF / QDII | 产品身份、基准、IOPV、历史溢价、申赎与时差纪律 | `installed` | 产品和溢价数据足够 | CIS |
| Portfolio Gate | 成本、权重、集中度、约束、资金需求 | `installed` | 组合数据完整 | CIS |

## 研究能力映射

| 研究能力 | 默认负责人 | 专业增强 | Fallback |
|---|---|---|---|
| 通用基本面 | TradingAgents Fundamentals Analyst | Anthropic Financial Analysis | CIS 基本面适配器 |
| 技术/市场结构 | TradingAgents Technical Analyst | CIS 四层交易框架最终校验 | CIS 技术适配器 |
| 新闻/宏观 | TradingAgents News Analyst | Anthropic sector/coverage（适用时） | CIS 宏观适配器 |
| 情绪 | TradingAgents Sentiment Analyst | — | CIS 仅使用可验证公开证据 |
| 多空辩论 | TradingAgents Bull/Bear Researchers | — | CIS 独立正反论点 |
| 候选交易决策 | TradingAgents Trader + Risk + Portfolio Manager | — | CIS 条件化研究姿态 |
| DCF / Comps / 三表 | Anthropic Financial Services | — | CIS 透明简化估值，需标 `limited` |
| Earnings | Anthropic Financial Services | TradingAgents 新闻/预期上下文 | CIS 证据化财报复盘 |
| 最终评分 | CIS | TradingAgents 输出只作为证据输入 | 无替代 |
| 最终动作/研究姿态 | CIS | TradingAgents 仅提供 `external_decision_candidate` | 无替代 |

## 本次能力状态

- `installed`：CIS 内置能力可执行。
- `upstream_default`：默认优先使用的外部核心；运行时必须转换为 `installed_ready`、`installed_limited`、`upstream_only`、`unavailable` 或 `blocked`。
- `upstream_preferred`：首选专业方法上游；运行时必须记录 `live_upstream`、`vendored_snapshot`、`limited` 或 `blocked`。
- `external_optional`：可选依赖；运行时转换为 `installed` 或 `unavailable`。

## 本次就绪度

- `ready`：关键输入完整，可形成决策级研究证据。
- `limited`：可提供有用研究，但结论必须保留限制。
- `blocked`：继续会迫使系统猜测，停止该模块。

TradingAgents 仓库持续更新不等于市场数据实时；行情、新闻、情绪和宏观数据必须记录本次实际提供商与 `as_of`。
