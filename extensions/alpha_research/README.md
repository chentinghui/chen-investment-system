# CIS Alpha Research Agent（0.5.0）

`extensions/alpha_research/` 是 CIS 的**可选 Alpha Discovery / Validation 扩展**，不属于日常单股分析默认链，也不拥有最终投资动作权。

## 架构位置

```text
                 CIS Alpha Research Agent
                         │
          ┌──────────────┴──────────────┐
          │                             │
WorldQuant BRAIN / 外部 Alpha       CIS Lightweight Alpha
          │                     factor_library.py
          ↓                             ↓
worldquant/alpha_import.py         alpha_miner.py
          │                             │
          └──────────────┬──────────────┘
                         ↓
                 CIS Alpha Candidate
                         ↓
             Factor / OOS / Cost Review
                         ↓
             CIS Evidence / Risk / Portfolio
                         ↓
                    最终投资结论
```

## CIS Lightweight Alpha Research

轻量研究链为个人使用设计：**不依赖 Qlib、Docker、服务器或外部 Alpha API**。输入一份日线 CSV 即可启动研究。

最小输入：

```csv
date,ticker,close,volume
2026-01-02,AAPL,250.10,45120000
2026-01-02,MSFT,480.20,22310000
```

`factor_engine/factor_library.py` 从日线自动生成 point-in-time 候选因子：

- `momentum_5`：5 日价格动量；
- `momentum_20`：20 日价格动量；
- `reversal_5`：5 日短期反转；
- `low_volatility_20`：20 日低波动；
- `volume_surprise_20`：当日成交量相对过去 20 日均量异常。

因子只使用当前及过去数据；`forward_return` 只作为未来研究标签，不参与因子构造。

`factor_engine/alpha_miner.py` 自动完成：

1. 日线 → 候选因子面板；
2. chronological train / test OOS split；
3. Rank IC / IC hit rate；
4. Top-Bottom forward-return spread；
5. long-short turnover 估计；
6. 0 / 5 / 10 / 20 bps 交易成本敏感性；
7. 因子横截面 Spearman 相关性；
8. 高相关因子冗余标记；
9. 研究候选排序。

运行：

```bash
python extensions/alpha_research/factor_engine/alpha_miner.py daily_bars.csv \
  --output alpha_research.json
```

输出固定：

```text
schema_version = cis.lightweight_alpha_research.v1
research_status = unreviewed
decision_authority = none
```

`candidate_for_cis_validation` 仅表示“值得进入 CIS 下一层独立验证”，**不是可买入信号，也不是已证明 Alpha**。

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
3. Lightweight Alpha Research 不产生 live order，不自动改写 CIS 生产评分权重。
4. 本扩展故障不得阻塞普通 CIS 单股分析。
5. `screen_status=candidate_for_cis_validation` 不是“可买入”或“已验证 Alpha”。
6. Lightweight Alpha 候选仍必须经过 point-in-time、survivorship bias、walk-forward、成本容量、factor exposure regression 和 portfolio risk review。
