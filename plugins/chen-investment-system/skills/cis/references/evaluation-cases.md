# CIS v1 代表性测试

| 场景 | 预期模式 | 预期主模块 | 关键验收 |
|---|---|---|---|
| “简单看一下贵州茅台值不值得研究” | quick | Buffett（可用时） | 不给未经支持的目标价 |
| “完整研究 AAPL，并做 DCF 和竞争分析” | deep | Valuation 或 Buffett，另一个为支持模块 | 只保留一个主模块 |
| “比较两只 ETF 的持仓重合度”但未提供持仓资料 | standard | ETF | ETF 模块为 blocked，并索取有日期的持仓 |
| “我该不该减持这只股票”但未提供组合资料 | holding_review | Portfolio | 不给减持动作，列出缺失组合输入 |
| “这家公司业绩发布后论点变了吗” | standard | Earnings | 使用 post-print 路线并比较预期基线 |
| “降息如何影响我的银行股” | standard 或 holding_review | Macro | 展示宏观到公司/持仓的传导链 |
| “筛选 AI 数据中心受益公司” | standard | AI Industry | 主题敞口必须连接订单、收入、利润或资本回报 |
| “股票研究助手分析腾讯” | standard | CIS | 旧入口转交 CIS，不直接调用其他模块 |
| 只提供三年前财报并要求当前结论 | standard | 对应业务模块 | 就绪度 limited 或 blocked，降低证据置信度 |
| Buffett 与 DCF 结论冲突 | standard 或 deep | CIS 综合 | 解释业务质量、预测、估值输入或期限差异，不做机械平均 |
| 未安装 Buffett | quick 或 standard | CIS | Buffett 标记 unavailable，定性模块 limited/blocked，其他可用模块继续 |
| 未安装 Public Equity Investing | deep | CIS | 不伪造 DCF 或财务工作流；明确缺失能力和最小输入 |
| 159509 长期处于两位数溢价、用户刚建仓或接近盈亏平衡 | holding_review | ETF | 不因绝对溢价或风险提示公告建议立即退出；先比较建仓溢价、历史区间、申赎状态和投资期限 |
| 四只纳指 ETF 与一只纳斯达克科技市值加权 ETF 同时持有 | holding_review | ETF | 先核验精确基准；不得把所有产品称为完全重复，应区分同一基准、高持仓重合和共享风险因子 |
| 用户给出市值和浮盈，但未给组合基准、约束与资金需求 | holding_review | Portfolio | 不输出精确卖出清单或再平衡比例，只列缺失输入和可验证风险 |
| 高溢价跨境 ETF 发布停复牌或溢价提示公告 | standard 或 holding_review | ETF | 公告是复核触发器而非自动卖出信号；根据历史溢价、申赎机制和组合资料形成条件化结论 |
| “英伟达186美元买入20股，现在能卖吗” | holding_review | Portfolio / Public Equity Investing | 强制按趋势→价格→成交→风险输出；同时给继续持有区、两档盈利止盈区、回调观察区、防守卖出线和基本面失效条件 |
| 英伟达或QQQ已经盈利，趋势、估值和量价仍健康 | holding_review | Portfolio / Public Equity Investing | 不得仅因已有盈利机械建议卖出；必须明确说明“不卖也可以”，盈利止盈仅为可选分批方案 |
| 用户问“为什么总是等亏损才卖” | holding_review | CIS 综合 | 同时解释盈利止盈与防守止损；上涨看压力、估值和量价异常，下跌看支撑和趋势破坏 |
| 盘中NVDA或QQQ成交量仅达到全天均量的一部分 | standard 或 holding_review | CIS 综合 | 必须注明尚未收盘，不得直接把盘中量与全天20日均量比较并下结论 |
