# CIS 统一评分引擎（0–100，0.4.4）

评分是研究综合工具，不是自动交易器。任何分数都必须服从 Evidence Gate、Risk Gate、Critical Dimension / Context Checks、Market Regime（按需）、Tactical Gate（短线按需）、四层交易框架和组合数据门。

## 当前校准状态

当前八维权重是 **CIS 生产启发式规则，但尚未完成充分历史/样本外校准**。

- 状态：`production_heuristic_pending_calibration`
- 不允许因为一次或少量回测结果自动调整权重。
- `performance-loop.md` 仅作为可选 Extension 校准规范，不属于日常 Core。
- 权重变化必须有足够样本、样本外结果、不同 Regime 稳定性和明确变更理由，并版本化修改。

## 维度与权重

| 维度 | 权重 | 说明 |
|---|---:|---|
| fundamentals | 20 | 商业/财务质量、现金流、资本配置 |
| growth | 15 | 增长跑道、单位经济、再投资质量 |
| valuation | 15 | 估值吸引力、隐含预期、情景空间 |
| industry_competitive | 10 | 行业结构、竞争位置、护城河方向 |
| technical | 15 | 趋势、价格、成交、市场结构 |
| catalyst_macro | 10 | 催化剂、宏观传导、预期差 |
| positioning | 5 | 机构/资金流/拥挤度等增量证据 |
| risk_resilience | 10 | 抗风险能力；越高越稳健 |
| **合计** | **100** | |

## Quality Score 与 Tactical Setup 分离

0.4.4 不凭感觉重写八维权重。CIS Score 继续回答“标的整体研究质量/吸引力如何”；短线是否适合现在做差价，由独立 Tactical Gate 回答。

因此允许出现：

```text
CIS Quality Score = 88
Tactical Gate = blocked_do_not_chase
```

这表示公司/研究质量高，但当前价格赔率差或已越过追价上限。不得把高分直接翻译成“现在买”。

同样，Tactical Setup 可以处于 `eligible_setup`，但如果 CIS Research coverage 不足，则 Research Grade 仍然保持 `provisional/insufficient`；两套状态不能互相伪造。

## 计算

每个已就绪维度给 0–100 分。缺失维度不补零、不猜测。

```text
coverage = 已有维度权重之和 / 100
weighted_score = Σ(score_i × weight_i) / Σ(available_weight_i)
```

- `coverage >= 85%`：只有全部质量门明确通过后才可 `decision_grade`。
- `70% <= coverage < 85%`：`provisional`。
- `coverage < 70%`：`insufficient`，不输出单一总分。

## Fail-Closed 质量门

`scripts/score_cis.py` 默认：

```text
audit_status = unverified
risk_status  = unverified
```

调用者没有明确提供 `pass` 时，**禁止**进入 `decision_grade`。`audit_status`、`risk_status`、`risk_override` 使用严格枚举；`critical_blocked` 与 context checks 必须是真正 JSON boolean，字符串 `"false"` / `"true"` 会被拒绝。

以下任一成立时，即使 coverage 足够，也不得升级为决策级：

- Evidence Audit 未明确 `pass`；
- Risk Review 未明确 `pass`；
- `risk_override=block`；
- 与结论直接相关的关键维度 `runtime_readiness=blocked`；
- Critical Dimension 缺失；
- Tactical 必需 Context Check 未完成；
- 关键市场/财务数据截止时间不明；
- 涉及仓位但组合数据门不满足。

## Critical Dimension / Context Check Gate

Coverage 不能替代关键维度。当前确定性基线：

```text
generic   → fundamentals + valuation + risk_resilience
long_term → fundamentals + growth + valuation + risk_resilience
tactical  → technical + risk_resilience
             + price_context=True
             + catalyst_event_review=True
earnings  → fundamentals + catalyst_macro + risk_resilience
```

`tactical` 的两个 context checks 只表示检查过程已完成，不要求催化剂一定为正。可以得到“已检查、无明确催化剂”，但不能“没有检查就默认通过”。

例如 valuation 完全缺失时，即使其余维度刚好形成 85% coverage，也只能是 `provisional`，不能 `decision_grade`。

ETF/QDII 不使用上述股票 Critical Dimension 组合替代产品门；ETF 仍必须通过产品身份、溢价、流动性、时差/申赎等专属 Gate。

## Tactical R/R Gate 边界

`scripts/tactical_setup_gate.py` 不修改 CIS Score，只检查：

- exchange-aware Price / Session 语义；
- Quote Freshness；
- Entry Zone；
- Chase Limit；
- Stop / Invalidation 与 Stop Type；
- Target 1 / 2；
- Reward / Risk；
- Setup Lifecycle（active / invalidated / expired / pending confirmation）。

按 Entry Zone 中最差 Target 1 R/R 的 baseline：

```text
<1.0       reject
1.0-<1.5   weak_setup
1.5-<2.0   acceptable
>=2.0      attractive
```

阈值仍需未来样本验证，不作为已证明最优参数。

## Quant 与 CIS Score 的边界

`quant_score` 只做横截面筛选/排序；`cis_score` 是单标的综合研究评分。二者不得直接相互换算，也不能简单平均成最终分数。

## Market Regime 的边界

Regime 不机械加减总分。它作为 `catalyst_macro`、`risk_resilience` 和交易计划的证据输入；必要时提高/降低安全边际与确认要求。

## 分数解释

无完整持仓背景时：

- 85–100：进入深入研究（高优先级）
- 75–84：进入深入研究
- 60–74：继续观察
- 0–59：暂时回避

完整 Holding Review 且所有质量门通过时，分数只能作为动作候选：

- 85–100：`考虑增持` 候选
- 70–84：`维持` 候选
- 55–69：`考虑减持` 候选
- 0–54：`考虑退出` 候选

**最终动作不能只由分数决定。** 必须再经过 Tactical/Four-layer、估值/基本面失效条件、持仓成本、权重、集中度、资金需求和风险预算。

## 评分纪律

- 不允许因为“喜欢公司”提高估值分。
- 不允许技术面强势掩盖基本面失效。
- 不允许机构买入替代基本面证据。
- 不允许把低风险写成高收益；`risk_resilience` 只衡量抗风险能力。
- 总控必须说明“为什么不是更高分”和“什么变化会使分数显著改变”。
- 历史校准必须遵守 `backtest-validation.md`，禁止前视偏差和样本内过拟合。
