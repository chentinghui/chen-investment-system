# CIS Alpha Research Agent（0.4.5）

`extensions/alpha_research/` 是 CIS 的**可选 Alpha Discovery / Validation 扩展**，不属于日常单股分析默认链，也不拥有最终投资动作权。

## 架构位置

```text
WorldQuant BRAIN / 外部 Alpha 来源
        ↓
worldquant/alpha_import.py
        ↓
CIS Alpha Candidate
        ↓
worldquant/alpha_validator.py
        ↓
Factor / OOS Diagnostics
        ├─ factor_engine/factor_test.py
        ├─ factor_engine/cross_section.py
        └─ ml_research/model_test.py
        ↓
CIS Evidence / Risk / Portfolio Review
        ↓
最终投资结论
```

## WorldQuant BRAIN

BRAIN 只作为 **Alpha Research Agent / Alpha 候选来源**。第一版不保存账号密码、不内置登录、不自动提交 Alpha、不自动交易。

`alpha_import.py` 接受用户导出的 JSON，或未来由合法 BRAIN Python API 权限取得的 JSON，并归一化为：

```text
schema_version = cis.alpha_candidate.v1
source = worldquant_brain
research_status = unreviewed
decision_authority = none
```

`alpha_validator.py` 只做研究筛选。即使 Sharpe / Turnover / Fitness 等指标通过，也只能进入 `candidate_for_cis_validation`，必须继续做：

- economic rationale review；
- data leakage / look-ahead review；
- out-of-sample validation；
- turnover / cost / capacity review；
- correlation / diversification review。

## Factor Engine

`factor_engine/cross_section.py` 提供无第三方依赖的横截面诊断：

- average-tie percentile ranks；
- Spearman Rank IC；
- IC hit rate；
- Top-Bottom forward-return spread；
- `(date,ticker)` 唯一性和有限数值输入检查。

`factor_engine/factor_test.py` 是 CLI 包装器，用于用户提供的 point-in-time 因子数据。它不自动抓取数据，也不把历史相关性解释成未来 Alpha。

## ML Research

`ml_research/model_test.py` **不训练模型**，只验证外部产生的 prediction：

- train / validation / test 分层诊断；
- 默认要求 test split；
- test 少于 3 个有效横截面 period 标记 `oos_status=insufficient`；
- 仍需单独检查 feature timestamp、purging/overlap、调参偏差和成本容量。

## 安全边界

1. 所有输出固定 `decision_authority=none`。
2. WorldQuant 候选不得携带 API key、password、brokerage、live-order 等字段进入公共研究契约。
3. 本扩展不得自动改写 CIS 生产评分权重。
4. 本扩展故障不得阻塞普通 CIS 单股分析。
5. `screen_status=candidate_for_cis_validation` 不是“可买入”或“已验证 Alpha”。
