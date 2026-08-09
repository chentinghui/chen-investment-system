# CIS 0.4.5 代表性测试

| 场景 | 预期模式 | 默认核心/模块 | 关键验收 |
|---|---|---|---|
| “分析 MU” | standard | CIS Core / ChatGPT-native TradingAgents Methodology | 即使未显式说“陈氏投资系统”，也进入 CIS；先 Runtime Guard，再走稳定方法论 |
| “MU现在能买吗” | tactical/standard | CIS Core + Price/Session + Tactical R/R + 四层交易 | 必须区分 Research Grade 与 Tactical Setup Readiness |
| 周末把 `market_session=regular` | tactical | Price/Session Guard | 直接拒绝；调用者不能覆盖代码推导 session |
| 09:35 regular 分析，却使用09:00 premarket quote | tactical | Quote Freshness | 即使 quote age 在允许范围内，也因 quote observation session 不一致而拒绝 |
| `stop_type` 缺失 | tactical | Tactical Gate | fail-closed；不得静默默认 hard stop |
| close-confirmation 昨日已确认失效，今日价格反弹 | tactical | Setup Lifecycle | 仍为 `invalidated_reprice_required`，旧 setup 不得复活 |
| technical invalidation 已确认，但当前价未碰 numeric stop | tactical | Setup Lifecycle | 仍为 `invalidated_reprice_required` |
| “QQQ还能持有吗” | holding_review（有持仓上下文时） | CIS ETF/四层/组合门 | ETF 规则和真实组合门优先，不能只给一般市场观点 |
| “MU全称是什么” | 不启动完整CIS | 直接事实回答 | 纯事实问题不强制运行完整 CIS |
| “完整研究 AAPL，并做 DCF 和竞争分析” | deep | CIS Core + Anthropic（按需） | DCF/竞争分析走专业方法，最终回 CIS 质量门 |
| 原版 TradingAgents `.propagate()` 成功返回 BUY | explicit test | Original TradingAgents + CIS | BUY 仅记为 `external_decision_candidate`；不得直接变成最终动作 |
| TradingAgents current main 与 reviewed_sha 不同，且请求云 Secret | explicit test | Remote Runner security gate | 阻断 secret-backed run，先审查上游；零密钥 Ollama smoke test 仍可用于可执行性检查 |
| 自定义 compatible endpoint 试图使用 NVIDIA profile | explicit test | Provider security | 拒绝；NVIDIA Key 只允许固定 NVIDIA endpoint |
| TradingAgents 执行 Job | explicit test | GitHub Actions | 只有 `contents: read`；写回由独立 trusted publisher 完成 |
| Evidence Auditor 输出“需要条件补证” | standard/deep | Evidence Audit | 机器状态使用 `unresolved`，不使用 `conditional` |
| Risk Manager 认为谨慎但未 block | standard/deep | Risk Review | 使用 `risk_status=unresolved` 或 `pass` + 风险说明；机器 `risk_override` 只有 `none|block` |
| 159509 两位数溢价、用户刚建仓 | holding_review | CIS ETF/QDII | 不因绝对溢价机械退出；比较建仓溢价、历史区间和申赎状态 |
| ETF 历史20条其实来自同一天重复复制 | ETF/QDII | ETF Premium Tool | 拒绝重复日期；不能把重复数据包装成20个有效观察 |
| ETF price=true | ETF/QDII | ETF Premium Tool | JSON boolean 不能当成1.0价格 |
| Quant 同一 as_of 出现重复 ticker | screening | Quant Extension | 拒绝重复 ticker |
| Quant 某因子只有1只股票有数据 | screening | Quant Extension | 该因子不形成 percentile，也不计入 coverage |
| Backtest 同一 period 重复 ticker | backtest | Backtest Extension | 拒绝，避免权重与收益平均口径不一致 |
| 同一次研究生成5D/20D/60D outcomes | evaluation | Evaluation Extension | unique research sample 只算1；相关性按 horizon 分开，禁止 pooled correlation |
| 公共 Prediction 输入 notes/account/shares 等字段 | evaluation | Prediction Ledger | allowlist 直接拒绝，不依赖 blacklist |
| Settlement 缺少 adjusted close | evaluation | Settlement | unresolved；不得 fallback raw close 后仍叫 adjusted_close |
| Settlement 输出 Entry | evaluation | Settlement | 明确是 next-session adjusted-close 研究指标，不得称为 next-open 实际成交收益 |
| GitHub可访问且用户说“陈氏投资系统” | 任意 | Runtime Guard | 先核验当前 `main`，不得凭聊天记忆恢复旧流程 |
