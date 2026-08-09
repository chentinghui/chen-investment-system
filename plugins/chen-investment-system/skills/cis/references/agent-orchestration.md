# CIS 0.4.5 编排协议（Control Plane v2）

## 1. 唯一最终控制权

`陈氏投资分析师 / CIS Control Layer` 是唯一总控和最终发布者。所有外部项目、Agent、模型、回测器和数据层都只有**证据权 / 研究权 / 验证权**，没有最终动作权。

固定边界：

```text
External Engines / Agents / Data
            ↓
      evidence candidates
            ↓
      CIS Control Layer
            ↓
Evidence Audit → Risk Gate → Critical Dimensions
            ↓
CIS Score → Asset/Trade/Portfolio Gates
            ↓
最终中文结论
```

禁止：多数票决定买卖、平均目标价消除冲突、外部 BUY/SELL/HOLD 直接覆盖 CIS。

## 2. 总控的核心原则：最少充分路由

总控不追求“模块调用越多越好”，而是为每个任务选择**最少数量、职责不重叠、专业性最高**的模块。

每次任务先标准化：

```text
asset_type
intent
mode = fast | standard | deep
as_of
是否需要当前数据
是否需要估值/财务建模
是否需要量化研究
是否需要发现新因子/模型
是否需要策略级回测
是否涉及真实组合
```

确定性路由器：

```text
scripts/route_cis.py
references/external-engine-registry.json
```

自然语言任务由总控先映射到路由器契约；路由器只产生执行计划，不替代 CIS 分析与最终裁决。

## 3. 专业引擎职责

| 引擎 | CIS 中的主职责 | 什么时候默认调用 | 最终动作权 |
|---|---|---|---|
| OpenBB | 数据基础设施 / provider 聚合 | 需要行情、基本面、宏观、多源数据时 | 无 |
| TradingAgents | 通用多 Agent 股票研究 | 一般股票研究、Bull/Bear、交易假设 | 无 |
| FinRobot | 确定性金融建模 | DCF/Comps/DDM/LBO/WACC/Monte Carlo/财报建模 | 无 |
| Microsoft Qlib | AI量化、因子、ML、组合优化 | Quant research、screening、factor/model research | 无 |
| Microsoft RD-Agent | 自动量化 R&D | 新因子发现、因子-模型联合优化、实验生成 | 无 |
| QuantConnect LEAN | 策略级事件驱动回测 | 可执行规则、订单/费用/滑点/持仓路径验证 | 无 |
| Anthropic Financial Services | 专业方法与二次审查 | deep 模式、模型审计、Earnings/Competitive/Thesis 等 | 无 |

**CIS 不重复实现这些项目已经成熟解决的专业问题。** CIS 只保留自己的证据门、风险门、评分、交易纪律、ETF/QDII纪律、组合门与最终裁决。

## 4. 标准路由顺序

### 4.1 一般股票研究

```text
OpenBB / primary sources
        ↓
TradingAgents Methodology
        ↓
Evidence + Risk + Critical Dimensions
        ↓
CIS Score
        ↓
最终结论
```

### 4.2 估值 / 财务模型

```text
OpenBB / filings
        ↓
TradingAgents contextual research
        ↓
FinRobot deterministic modeling
        ↓
必要时 Anthropic method audit（deep）
        ↓
CIS valuation reconciliation
```

估值冲突必须比较：输入数据、会计口径、WACC、增长率、终值、情景概率、可比公司选择。**禁止简单平均目标价。**

### 4.3 Quant / 因子 / ML

```text
Point-in-time data
        ↓
Qlib
        ↓
CIS evidence/bias review
```

Qlib 负责成熟量化研究，不由 CIS 自己重新实现完整 ML 研究框架。

### 4.4 新因子 / 新模型研发

```text
RD-Agent
   ↓ proposes / implements
Qlib
   ↓ independent quant evaluation
LEAN
   ↓ execution-realistic strategy validation
CIS Backtest Validation
   ↓
experimental → accepted（仅人工/规则审查后）
```

RD-Agent 产出的新因子、新模型、新阈值默认都是 `experimental_research_candidate`，不得自动进入 CIS 生产评分。

### 4.5 策略级历史验证

```text
Strategy specification
        ↓
QuantConnect LEAN
        ↓
Backtest Validation
        ↓
CIS evidence input
```

如果用户明确说“用 LEAN 回测”，LEAN 不可用时必须报告 unavailable/error，**不得拿 baseline evaluator 冒充 LEAN**。

### 4.6 短线 / 买卖价位

```text
OpenBB/current quote + primary catalyst sources
        ↓
TradingAgents research
        ↓
Price/Session Guard
Quote Freshness
Tactical R/R
Four-layer Trading Gate
        ↓
CIS final trade posture
```

普通短线分析不因为 LEAN 存在就自动运行 LEAN；只有用户要求验证规则，或该规则准备升级为系统规则时才调用。

## 5. 冲突仲裁

冲突按以下顺序检查，而不是投票：

1. **事实冲突**：primary source → 数据时效 → provider coverage → 口径。
2. **财务冲突**：会计口径 → restatement → fiscal period → currency/unit。
3. **估值冲突**：模型假设逐项拆解，禁止机械平均。
4. **Quant 与基本面冲突**：先区分预测期限与假设；短期量化弱不等于长期基本面失效，反之亦然。
5. **Qlib 与 LEAN 冲突**：Qlib 负责研究有效性；LEAN 对实际订单路径、费用、滑点和持仓路径拥有更高的**执行验证优先级**，但仍没有最终动作权。
6. **RD-Agent 与现有生产规则冲突**：现有生产规则保持不变，新候选必须通过独立验证。
7. **外部系统与 CIS 风险门冲突**：CIS 风险门优先；`risk_override=block` 直接阻止升级。

关键冲突无法解决时必须保留冲突并降低 confidence/readiness。

## 6. 防重复调用

- OpenBB 只负责数据基础设施，不重复做投资决策。
- TradingAgents 已完成通用公司研究后，不再无理由启动另一套完整通用 Agent 团队。
- FinRobot 做确定性模型时，不再让 LLM 自己心算同一套 DCF。
- Qlib 做 Quant/ML 研究时，本地 Quant Extension 只作为 fallback/sanity check，不冒充等价替代。
- RD-Agent 仅用于 R&D，不用于普通单股问答。
- LEAN 仅用于策略级验证，不重复基本面、新闻和估值研究。
- Anthropic Financial Services 默认只做专业方法补强或 deep second opinion，不与成功的 FinRobot 无理由双跑。

## 7. Fail-closed 降级

外部模块不可用时：

- OpenBB → primary sources / direct provider / web，并披露数据覆盖差异；
- TradingAgents runtime → 使用已审查的 ChatGPT-native TradingAgents Methodology；
- FinRobot → Anthropic Financial Services 或透明 CIS 计算；不得虚构“已运行 FinRobot”；
- Qlib → 本地 Quant Extension 只可做轻量筛选/因子 sanity check；不得声称等价；
- RD-Agent → 无静默替代；报告该 R&D 阶段未运行；
- LEAN → 无静默等价替代；显式 LEAN 请求必须报告 unavailable/error；
- Anthropic → 跳过该增强，不影响其他可完成路径。

## 8. 质量门与最终综合

任何外部结果进入最终结论前必须回到：

```text
Evidence Audit
    ↓
Risk Review
    ↓
Critical Dimension / Context Checks
    ↓
CIS Score / Research Grade
    ↓
Market Regime（按需）
    ↓
Tactical / Four-layer / ETF / Portfolio Gate（按需）
    ↓
CIS 最终中文结论
```

外部模块成功执行只证明“程序完成”，不等于研究质量通过。

## 9. 权限矩阵

- `CIS Control Layer`：唯一最终发布权；
- Evidence / Risk / Critical Gate：可阻止升级，但不能独立发布买卖结论；
- OpenBB：数据权；
- TradingAgents / FinRobot / Qlib / RD-Agent / Anthropic：研究或建模权；
- LEAN：策略验证权；
- 外部项目的 BUY/SELL/HOLD / target / score：一律作为候选输入。

## 10. 生命周期

任何准备升级为 CIS 默认规则的 Quant/阈值/策略，至少经过：

```text
hypothesis
→ implementation
→ point-in-time research
→ independent validation
→ execution realism
→ out-of-sample / robustness review
→ CIS policy review
→ production rule
```

任何外部项目更新也不得自动覆盖稳定 CIS；更新必须先审查能力、接口、依赖、许可证、输出契约与代表性测试。
