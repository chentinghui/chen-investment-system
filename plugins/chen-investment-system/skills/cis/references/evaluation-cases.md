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
