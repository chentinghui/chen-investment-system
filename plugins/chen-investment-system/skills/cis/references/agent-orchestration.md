# CIS 0.4 编排协议

## 1. 最终控制权

`陈氏投资分析师 / CIS Control Layer` 是唯一总控。ChatGPT-native TradingAgents Methodology、Quant、Anthropic、Market Regime、原版 TradingAgents 和任何 fallback adapter 都不能直接发布 CIS 最终动作。

## 2. 默认路由顺序

1. 明确研究对象/股票池、问题、模式、期限和 `as_of`。
2. Runtime Guard：读取当前 GitHub `main` 和 TradingAgents 上游审查状态。
3. 大股票池任务按需先 Quant 预筛；单股票任务跳过。
4. ChatGPT-native TradingAgents Methodology 完成通用多角色研究。
5. DCF/Comps/Earnings/三表等专业子问题按需调用 Anthropic。
6. Evidence Audit + CIS Risk Gate。
7. CIS 八维评分。
8. 当前市场环境会改变交易计划时加入 Market Regime。
9. 涉及买卖/价位时执行四层交易框架；涉及真实仓位时执行组合门。
10. 输出最终中文研究姿态和证伪条件。
11. 需要历史校准时记录到 Performance Loop。

## 3. 多角色独立性

- Fundamentals / Market / News 各自只对职责范围内事实负责。
- Bull 必须建立上涨路径与支持证据。
- Bear 必须寻找不同来源或不同机制的反证，不能只改写 Bull。
- Risk 至少检查一个独立尾部风险/失效机制。
- Research Manager 不得创造新事实，只能裁决已有证据、计算、假设与冲突。
- 关键冲突无法解决时必须保留并降低 confidence。

## 4. 避免重复分析

- Quant 只筛选，不重复做完整公司研究。
- ChatGPT-native Analyst 已完成职责后，不再默认调用同职责 CIS fallback adapter。
- Anthropic 专业模型已运行时，不重复独立建模，除非验证输入或解释冲突。
- Market Regime 不重复 Market Analyst；只提供环境层。
- Backtest / Performance Loop 只做验证与校准，不直接生成买卖动作。
- 原版 TradingAgents 仅显式测试，不与日常方法论无理由双跑。

## 5. 冲突处理

优先检查：数据截止时间 → 数据源/市场覆盖 → 会计口径 → 时间跨度 → 预测假设 → 估值方法 → 短期技术/情绪与长期基本面 → 事实/判断混淆。

不得通过多数票、简单平均目标价或简单平均模型置信度消除冲突。

## 6. 质量循环

如果 `audit_status=unresolved` 或 `risk_override=block`：

- 第一次：定向补证；
- 第二次仍失败：降低 readiness / score status；
- coverage 不足：总评分 `insufficient`；
- 不得因 Quant 高分、Bull 强烈看多或原版 TradingAgents BUY 就绕过质量门。

## 7. 最终综合顺序

```text
Quant 候选（按需）
+ ChatGPT-native 多角色研究
+ Anthropic 专业证据（按需）
+ 其他可验证证据
        ↓
Evidence Audit
        ↓
CIS Risk Gate
        ↓
关键冲突解释
        ↓
CIS 八维评分
        ↓
Market Regime（按需）
        ↓
四层交易 / ETF / Portfolio Gate
        ↓
CIS 最终中文姿态
        ↓
Performance Record / Calibration（按需）
```

## 8. 原版 TradingAgents

只有用户明确要求时运行。其 Portfolio Manager 结论统一记为 `external_decision_candidate`，只能作为外部验证证据，不能覆盖 CIS 最终控制权。
