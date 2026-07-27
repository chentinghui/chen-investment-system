# CIS 模块路由

## 路由原则

从用户要做的决定出发选择一个主模块。支持模块只用于验证关键输入、解释冲突或补足必需视角。表中的外部路线只有在运行前检查确认可用时才执行，否则按 `external-modules.md` 降级。

| 用户意图 | 主模块 | 首选路线 | 可选支持 |
|---|---|---|---|
| 是否值得长期研究或持有 | Buffett | `$buffett` 快速或完整路径 | Financial、Competitive Analysis |
| 财务数据是否可比、能否入模 | Financial | `$public-equity-investing` → `financials-normalizer` | `model-audit-tieout` |
| 价值区间或市场隐含预期 | Valuation | `dcf-model-builder` 或 `comps-valuation` | Buffett、`scenario-sensitivity-generator` |
| 业绩前怎么看预期差 | Earnings | `earnings-preview` | Risk、Portfolio |
| 业绩后发生了什么变化 | Earnings | `earnings-deep-dive` | `equity-model-update`、Risk |
| 宏观事件如何影响公司或持仓 | Macro | `economic-impact-report` | Portfolio、情景分析 |
| 比较 ETF 产品或敞口 | ETF | ETF/index diligence | Portfolio、Risk |
| 分析跨境 ETF / QDII 溢价或是否切换产品 | ETF | CIS `cross-border-etf-premium.md` | Portfolio、Risk、可用的 ETF/index diligence |
| 增持、减持、退出、对冲或再平衡 | Portfolio | `portfolio-risk-management` | Risk、`thesis-tracker`、`catalyst-calendar` |
| 压力测试或寻找证伪条件 | Risk | `scenario-sensitivity-generator` 或 `portfolio-risk-management` | Buffett 卖出标准 |
| 检验成长逻辑 | Growth | `initiating-coverage` | Financial、Valuation、Buffett |
| 研究 AI 投资主题 | AI Industry | `idea-generation` 或 `economic-impact-report` | Growth、Competitive Analysis、Valuation |
| 比较企业竞争位置 | Competitive Analysis | `initiating-coverage` 或 `company-tearsheet` | Buffett、`comps-valuation` |

## 运行前检查

1. 确认专业 Skill 或工作流在当前环境存在。
2. 确认本次所需的数据类别是否可调用；插件安装不等于连接器已授权。
3. 对关键来源执行最小只读检查，或确认用户已提供等价资料。
4. 记录数据截止时间、覆盖范围、冲突和缺口。
5. 按 `ready`、`limited`、`blocked` 标记本次就绪度。
6. 外部模块缺失时记录 `capability_status: unavailable`，不得伪造调用。
7. 跨境 ETF / QDII 先核验精确基准、IOPV 时点、历史溢价和申赎状态；缺少这些输入时将 ETF 模块降为 `limited` 或 `blocked`。

## 防重叠规则

- CIS 是唯一总控和最终结论所有者。
- Buffett 只负责定性所有权判断，不负责审计级财务标准化或实时市场数据。
- Financial 负责数字与口径，不给最终投资姿态。
- Valuation 负责透明计算，不从估值倍数推断护城河。
- Earnings 负责相对预期的变化，不替代长期论点。
- Macro 负责传导链，不把宏观预测当作公司事实。
- Portfolio 负责总组合后果；缺少组合背景时单股模块不能决定仓位。
- ETF 模块只描述产品身份、敞口和溢价证据；不得把风险提示公告或绝对溢价直接转换成卖出动作。
- Risk 负责下行机制和动作触发条件。
- Growth、AI Industry 和 Competitive Analysis 是组合视角，不另建重复估值引擎。
