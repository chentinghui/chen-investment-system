# CIS 0.4.5 编排协议

## 1. 最终控制权

`陈氏投资分析师 / CIS Control Layer` 是唯一总控。ChatGPT-native TradingAgents Methodology、Anthropic、Market Regime、原版 TradingAgents 和 Optional Research Tooling 都不能直接发布 CIS 最终动作。

## 2. 默认 Core 路由顺序

1. 明确研究对象、问题、模式、期限和 `as_of`。
2. Runtime Guard：读取当前 GitHub `main` 和 TradingAgents 上游审查状态。
3. ChatGPT-native TradingAgents Methodology 完成通用多角色研究。
4. DCF/Comps/Earnings/三表等专业子问题按需调用 Anthropic。
5. Evidence Audit + CIS Risk Gate；机器枚举统一为 `audit_status/risk_status = pass|unresolved|fail|unverified`，`risk_override=none|block`。
6. Critical Dimension Gate + CIS 八维评分。
7. 当前市场环境会改变交易计划时加入 Market Regime。
8. 涉及买卖/价位时执行四层交易框架；短线增加 Price/Session + Quote Freshness + Tactical R/R + Setup Lifecycle；涉及真实仓位时执行组合门。
9. 输出最终中文分析结论和证伪条件。

## 3. Optional Research Tooling 路由

只有任务明确需要时才额外调用 `extensions/research_tooling/`：

- 大股票池/Top N → Quant；
- 新规则/因子/阈值验证 → Backtest；
- 用户明确要求记录、复盘或校准 → Prediction/Evaluation。

这些工具不属于默认 Core，故障不得阻塞单股分析。

## 4. 多角色独立性

- Fundamentals / Market / News 各自只对职责范围内事实负责；
- Bull 建立上涨路径与支持证据；
- Bear 寻找不同来源或不同机制的反证，不能只改写 Bull；
- Risk 至少检查一个独立尾部风险/失效机制；
- Research Manager 不得创造新事实，只能裁决已有证据、计算、假设与冲突；
- 关键冲突无法解决时必须保留并降低 confidence。

## 5. 避免重复分析

- Quant 只筛选，不重复做完整公司研究；
- ChatGPT-native Analyst 已完成职责后，不再默认调用同职责 fallback adapter；
- Anthropic 已完成专业模型时，不无理由重复建模；
- Market Regime 不重复 Market Analyst，只提供环境层；
- Backtest / Evaluation 只做研发验证与复盘；
- 原版 TradingAgents 仅显式测试，不与日常方法论无理由双跑。

## 6. 冲突处理

优先检查：数据截止时间 → 数据源/市场覆盖 → 会计口径 → 时间跨度 → 预测假设 → 估值方法 → 短期技术/情绪与长期基本面 → 事实/判断混淆。

不得通过多数票、简单平均目标价或模型置信度消除冲突。

## 7. 质量循环

如果 `audit_status` 未通过或风险门阻塞：定向补证；仍失败则降低 readiness / score status。不得因 Quant 高分、Bull 强烈看多或原版 TradingAgents BUY 绕过质量门。

## 8. 最终综合顺序

```text
ChatGPT-native 多角色研究
+ Anthropic 专业证据（按需）
+ 其他可验证证据
        ↓
Evidence Audit
        ↓
CIS Risk Gate
        ↓
Critical Dimensions / Context Checks
        ↓
CIS 八维评分
        ↓
Market Regime（按需）
        ↓
Tactical R/R / 四层交易 / ETF / Portfolio Gate
        ↓
CIS 最终中文结论
```

Optional Research Tooling 是外围输入/研发能力，不追加到每次默认执行链。

## 9. 原版 TradingAgents

只有用户明确要求时运行。其 Portfolio Manager 结论统一记为 `external_decision_candidate`，只能作为外部验证证据，不能覆盖 CIS 最终控制权。

远程执行采用安全隔离：第三方 TradingAgents 代码所在 Job 仅有 `contents: read`；结果作为 Artifact 交给不持有 LLM Secret 的 trusted publisher 写回。Cloud/secret-backed 运行要求当前上游 SHA 已被审查；未审查最新 main 只能做零密钥 smoke test。
