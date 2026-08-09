# CIS 0.3 编排协议

## 1. 最终控制权

`陈氏投资分析师` 是唯一 CIS 总控。TradingAgents、Anthropic Financial Services、Buffett 和 CIS fallback adapters 都不能绕过总控直接发布 CIS 最终研究姿态。

TradingAgents Portfolio Manager 的结论统一记为 `external_decision_candidate`。

## 2. 默认路由顺序

1. 明确研究对象、问题、模式、期限和 `as_of/analysis_date`。
2. 运行 Runtime Guard，读取当前 GitHub `main` 规则。
3. 股票/上市公司任务先检查 TradingAgents 本次运行状态。
4. TradingAgents 可用时，默认让其完成通用多 Agent 研究链。
5. 需要 DCF、Comps、三表、财报、首次覆盖等专业子问题时，调用最小匹配的 Anthropic Skill。
6. TradingAgents 不可用或出现关键冲突时，才启用对应 CIS fallback adapter。
7. Standard/Deep/Holding Review 保留独立证据审计与 CIS 风险门。
8. 涉及具体买卖时执行 CIS 四层交易框架；涉及真实仓位时再过组合数据门。

## 3. 避免重复分析

- TradingAgents Fundamentals 已运行时，不再默认调用 CIS 基本面 adapter。
- TradingAgents Technical 已运行时，CIS 技术 adapter 只负责四层交易框架及关键冲突复核。
- TradingAgents News/Sentiment 已运行时，不再用 CIS 自写 Agent 复制同一新闻摘要。
- Anthropic DCF/Comps 已运行时，不再跑独立重复估值，除非验证输入或解释冲突。
- 外部 Risk Team 不替代 CIS 风险门；二者职责不同。

## 4. 专业结果回灌

Anthropic 专业 Skill 输出必须进入同一证据登记：

- 来源与 `as_of`；
- 关键模型输入；
- 情景假设；
- 估值/财务结论；
- 限制和证伪条件。

若专业结果与 TradingAgents 候选决策冲突，总控必须展示冲突，不能机械平均。

## 5. 冲突处理

依次检查：

1. 数据截止时间；
2. 数据源与市场覆盖；
3. 会计/指标口径；
4. 时间跨度；
5. 预测假设；
6. 估值方法；
7. 技术/情绪短期信号与长期基本面；
8. 事实与判断混淆。

## 6. 质量循环

如果证据审计返回 `audit_status=unresolved` 或 CIS 风险门返回 `risk_override=block`：

- 第一次：定向补证或重新调用对应外部/专业模块；
- 第二次仍失败：降低该模块 `runtime_readiness`；
- 关键维度覆盖不足：总评分 `insufficient`；
- 不得因为 TradingAgents 输出明确 BUY/SELL/HOLD 就绕过质量门。

## 7. 最终综合顺序

固定为：

```text
TradingAgents 通用研究/候选决策
+ Anthropic 专业金融证据（按需）
+ 其他可验证证据
        ↓
CIS 证据审计
        ↓
CIS 风险门
        ↓
关键冲突解释
        ↓
CIS 八维统一评分
        ↓
四层交易框架（涉及价位/买卖时）
        ↓
ETF/QDII专属门或组合数据门（如适用）
        ↓
CIS 最终中文研究姿态
        ↓
证伪条件 + 跟踪计划
```

外部引擎负责提高研究质量；CIS 负责保证结果符合用户自己的投资纪律。
