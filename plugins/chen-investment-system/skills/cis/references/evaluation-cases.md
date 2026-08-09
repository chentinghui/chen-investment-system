# CIS 0.3 代表性测试

| 场景 | 预期模式 | 默认核心/模块 | 关键验收 |
|---|---|---|---|
| “分析 MU” | standard | CIS → TradingAgents（可运行时） | 即使未显式说“陈氏投资系统”，也必须进入 CIS；先执行 Runtime Guard，再走默认股票研究核心 |
| “MU现在能买吗” | standard | CIS → TradingAgents + CIS四层交易 | 自动进入 CIS；涉及买入位置时必须执行四层交易框架 |
| “QQQ还能持有吗” | holding_review（有持仓上下文时） | CIS ETF/四层/组合门 | 自动进入 CIS；ETF 规则和真实组合门优先，不能只给一般市场观点 |
| “MU全称是什么” | 不启动完整CIS | 直接事实回答 | 纯事实问题不强制运行 TradingAgents/CIS完整流程 |
| “QQQ跟踪什么指数” | 不启动完整CIS | 直接事实回答 | 纯产品事实可直接回答；若继续问是否值得买，再进入 CIS |
| “简单看一下贵州茅台值不值得研究” | quick | TradingAgents（可运行时） | 先检查外部核心状态；不凭旧CIS Agent直接给结论 |
| “完整研究 AAPL，并做 DCF 和竞争分析” | deep | TradingAgents + Anthropic | 通用研究走 TradingAgents；DCF/竞争分析走 Anthropic；最终回 CIS |
| TradingAgents 包未安装但 GitHub 上游可读 | standard | CIS fallback | 标记 `upstream_only`；不得声称已运行 `.propagate()` |
| TradingAgents `.propagate()` 成功返回 BUY | standard | TradingAgents + CIS | BUY 仅记为 `external_decision_candidate`；必须再过证据门与CIS评分 |
| TradingAgents 与 Anthropic DCF 方向冲突 | deep | CIS综合 | 展示数据/假设/期限冲突，不机械平均目标价或投票 |
| TradingAgents Technical 看多，但四层框架显示趋势破坏 | holding_review | CIS四层交易 | 四层框架拥有最终交易位置约束，不能被外部Technical覆盖 |
| TradingAgents Portfolio Manager 给仓位，但用户未提供真实组合 | holding_review | CIS组合门 | 不采用精确仓位；列出缺失成本/权重/约束/资金需求 |
| TradingAgents 代码版本很新但新闻数据陈旧 | standard | Evidence Audit | 明确区分代码更新与数据时效，降低证据置信度 |
| 历史日期回测/复盘 | deep | TradingAgents + Evidence Audit | 禁止使用 `analysis_date` 之后的信息；检查 look-ahead leakage |
| “这家公司业绩发布后论点变了吗” | standard | TradingAgents + Anthropic Earnings | Anthropic `earnings-analysis` 为专业核心，TradingAgents提供市场上下文 |
| “比较两只 ETF 的持仓重合度”但未提供持仓资料 | standard | CIS ETF | ETF 模块 blocked/limited；不强制调用 TradingAgents |
| 159509 两位数溢价、用户刚建仓 | holding_review | CIS ETF/QDII | 不因绝对溢价机械退出；比较建仓溢价、历史区间和申赎状态 |
| 高溢价跨境 ETF 发布风险提示公告 | holding_review | CIS ETF/QDII | 公告只是复核触发器，不是自动卖出信号 |
| “英伟达186美元买入20股，现在能卖吗” | holding_review | TradingAgents + CIS四层/组合门 | 同时给继续持有区、两档止盈、回调观察、防守线、基本面失效条件 |
| 英伟达/QQQ已有盈利但趋势和估值仍健康 | holding_review | CIS四层交易 | 不因盈利机械卖出；明确止盈是可选方案 |
| 盘中成交量尚未收盘 | standard/holding_review | Evidence Audit | 不把盘中量直接与全天均量比较 |
| Anthropic DCF Skill 无法读取 | deep | TradingAgents + CIS fallback | 不伪造专业DCF；valuation维度 limited 或 blocked |
| GitHub可访问且用户说“陈氏投资系统” | 任意 | Runtime Guard | 先核验 `chentinghui/chen-investment-system` 当前 `main` |
| “股票研究助手分析腾讯” | standard | CIS | 旧入口只转交 CIS；CIS 再决定 TradingAgents/Anthropic 路由 |
| TradingAgents运行失败 | standard/deep | CIS fallback adapters | 不终止整个CIS；按最小fallback团队继续并降低置信度 |
| Buffett 与 TradingAgents 长期质量判断冲突 | deep | CIS综合 | Buffett仅作为定性外部视角，不直接推翻数据化研究；解释差异 |
