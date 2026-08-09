# CIS 模块路由

## 路由原则

从用户要做的决定出发选择一个主模块。支持模块只用于验证关键输入、解释冲突或补足必需视角。专业金融能力优先按 `anthropic-financial-services.md` 路由到 Anthropic `financial-services` 当前上游；只有本次真实读取成功或存在已验证快照时才可标记为可用。

| 用户意图 | 主模块 | 首选路线 | 可选支持 |
|---|---|---|---|
| 是否值得长期研究或持有 | Buffett | `$buffett` 快速或完整路径 | Financial、Competitive Analysis |
| 财务数据是否可比、能否入模 | Financial | Anthropic `clean-data-xls` / `3-statement-model` | `audit-xls` |
| 价值区间或市场隐含预期 | Valuation | Anthropic `dcf-model` 或 `comps-analysis` | Buffett、情景敏感性 |
| 业绩前怎么看预期差 | Earnings | Anthropic `earnings-preview` | Risk、Portfolio |
| 业绩后发生了什么变化 | Earnings | Anthropic `earnings-analysis` | `model-update`、Risk |
| 宏观事件如何影响公司或持仓 | Macro | CIS 宏观传导 + Anthropic `sector-overview`（适用时） | Portfolio、情景分析 |
| 比较 ETF 产品或敞口 | ETF | CIS ETF/index diligence | Portfolio、Risk |
| 分析跨境 ETF / QDII 溢价或是否切换产品 | ETF | CIS `cross-border-etf-premium.md` | Portfolio、Risk |
| 增持、减持、退出、对冲或再平衡 | Portfolio | CIS 组合数据门 + 风险框架 | Risk、Anthropic `thesis-tracker` / `catalyst-calendar` |
| 压力测试或寻找证伪条件 | Risk | CIS 风险经理 + 透明情景分析 | Buffett 卖出标准、Anthropic `thesis-tracker` |
| 检验成长逻辑 | Growth | Anthropic `initiating-coverage` / `sector-overview` | Financial、Valuation、Buffett |
| 研究 AI 投资主题 | AI Industry | Anthropic `idea-generation` / `sector-overview` | Growth、Competitive Analysis、Valuation |
| 比较企业竞争位置 | Competitive Analysis | Anthropic `competitive-analysis` | Buffett、`comps-analysis` |
| 建立或更新投资论点跟踪 | Thesis & Catalysts | Anthropic `thesis-tracker` / `catalyst-calendar` | Risk、Earnings、Macro |

## 运行前检查

1. 先读取当前 CIS 入口与必读 references；不得凭聊天记忆恢复旧评分或旧路由。
2. 确认目标 Anthropic Skill 的当前上游路径或验证快照存在。
3. 确认本次所需的数据类别是否可调用；Skill 存在不等于连接器已授权。
4. 对关键来源执行最小只读检查，或确认用户已提供等价资料。
5. 记录数据截止时间、覆盖范围、冲突和缺口。
6. 按 `ready`、`limited`、`blocked` 标记本次就绪度。
7. 上游 Skill 无法读取时不得伪造其输出；按 `external-modules.md` 降级。
8. 跨境 ETF / QDII 先核验精确基准、IOPV 时点、历史溢价和申赎状态；缺少这些输入时将 ETF 模块降为 `limited` 或 `blocked`。

## 防重叠规则

- CIS 是唯一总控和最终结论所有者。
- Buffett 只负责定性所有权判断，不负责审计级财务标准化或实时市场数据。
- Anthropic Financial Services Skills 负责专业方法和子问题交付，不拥有 CIS 最终评分或动作标签。
- Financial 负责数字与口径，不给最终投资姿态。
- Valuation 负责透明计算，不从估值倍数推断护城河。
- Earnings 负责相对预期的变化，不替代长期论点。
- Macro 负责传导链，不把宏观预测当作公司事实。
- Portfolio 负责总组合后果；缺少组合背景时单股模块不能决定仓位。
- ETF 模块只描述产品身份、敞口和溢价证据；不得把风险提示公告或绝对溢价直接转换成卖出动作。
- Risk 负责下行机制和动作触发条件。
- Growth、AI Industry 和 Competitive Analysis 是组合视角，不另建重复估值引擎。
