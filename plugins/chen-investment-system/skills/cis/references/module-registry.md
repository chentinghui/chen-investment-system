# CIS 模块登记表

“能力状态”表示当前环境是否存在该能力；“本次就绪度”必须在每次任务运行前重新判断。外部模块不得在静态文件中预设为已安装。

| 模块 | 作用 | 默认能力状态 | 本次就绪条件 | 所有者 |
|---|---|---|---|---|
| CIS | 受理、路由、证据纪律、综合结论与复盘 | `installed` | 总是可用 | `$cis` |
| Buffett | 商业质量、管理层、护城河、所有者收益、资本配置、卖出纪律 | `external_optional` | Skill 已安装且有足够的公司和业务资料 | `$buffett` |
| Financial | 财务标准化、预测架构和模型核验 | `external_optional` | Public Equity Investing 可用，且有财报、期间、单位和口径 | `$public-equity-investing` |
| Valuation | DCF、可比估值、价格桥接和敏感性 | `external_optional` | 有价格、股本、净负债、预测和透明假设 | `$public-equity-investing` |
| Earnings | 业绩前预期、业绩后变化和模型影响 | `external_optional` | 有事件日期、业绩材料及明确预期基线 | `$public-equity-investing` |
| Macro | 利率、通胀、政策、汇率和商品的权益传导 | `external_optional` | 有宏观事实及公司/组合敞口证据 | `$public-equity-investing` |
| ETF | 指数方法、产品敞口、成分、费用、集中度和重合度 | `external_optional` | 有基金身份、基准方法、费用和注明日期的持仓数据 | `$public-equity-investing` |
| Portfolio | 仓位、对冲、组合风险、增减持和跟踪 | `external_optional` | 有持仓、权重及与动作相关的约束 | `$public-equity-investing` |
| Risk | 结构、财务、情景、流动性、杠杆和论点风险 | `mixed` | 有与风险类型匹配的基础资料 | CIS + 可用外部模块 |
| Growth | 跑道、单位经济、再投资质量和融资型增长 | `mixed` | 有增长驱动、单位经济及资本需求资料 | CIS + 可用外部模块 |
| AI Industry | AI 价值链、敞口证明、采用率、经济性、依赖和技术风险 | `mixed` | 有从主题到 KPI 的传导证据 | CIS + 可用外部模块 |
| Competitive Analysis | 市场结构、同行经济、战略位置和护城河方向 | `mixed` | 有竞争集合、市场定义和可比资料 | CIS + 可用外部模块 |

## 本次能力状态

- `installed`：当前环境已发现并可调用。
- `unavailable`：当前环境未发现，或调用所需权限不可用。
- `external_optional`：静态登记中的外部可选依赖；运行时必须转换为 `installed` 或 `unavailable`。
- `mixed`：可由 CIS 基础规则与一个或多个外部模块共同完成，实际范围取决于本次资料和能力。

## 本次就绪度

- `ready`：关键输入完整，模块可以形成决策级结果。
- `limited`：可以提供有用研究，但关键结论必须保留限制。
- `blocked`：缺失输入会迫使系统猜测，停止该模块并提出最小补充要求。

能力已安装不等于本次任务 `ready`。接入或替换模块前，继续执行 `integration-decisions.md` 的准入标准。
