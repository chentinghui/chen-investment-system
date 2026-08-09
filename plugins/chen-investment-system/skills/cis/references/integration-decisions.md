# CIS Integration Decisions

As-of: 2026-08-09. Reverify repository state, licenses, dependencies, paths, account requirements and quality before changing these decisions.

## Current architecture — CIS 0.4.5

- `cis` is the sole user-facing entrypoint and final quality-control layer.
- `TauricResearch/TradingAgents` methodology is the default general-purpose stock/issuer research and external decision-candidate method.
- Anthropic `financial-services` is the preferred professional Skill upstream for DCF, Comps, three-statement models, earnings, model audit/update, competitive analysis, thesis tracking and catalysts.
- `QuantConnect/Lean` is the accepted external strategy-level quant/backtest engine; CIS owns only the adapter and validation contract.
- CIS-owned rules remain authoritative for evidence, scoring, trading framework, ETF/QDII, portfolio context and final Chinese posture.
- `stock-research-assistant` is only a legacy alias that hands off to CIS.

## Accepted external capabilities

### TradingAgents — accepted as default research core methodology

Accepted for:

- fundamental / technical / news / sentiment analyst team;
- bull/bear debate;
- research manager synthesis;
- trader proposal;
- risk-management debate;
- portfolio-manager external candidate decision when original runtime is explicitly executed;
- persistent decision-log/reflection when the installed version provides it.

Boundary:

- Portfolio Manager output is `external_decision_candidate`, never the final CIS action.
- TradingAgents technical output does not replace CIS four-layer trading rules.
- TradingAgents risk output does not replace CIS evidence audit, portfolio data gate or ETF/QDII rules.
- Code freshness does not imply real-time data freshness.
- Historical analysis must preserve `analysis_date` and prevent look-ahead leakage.

Verification recorded 2026-08-09:

- upstream `main` exists;
- README reports v0.3.1 (2026-07);
- README documents package use via `TradingAgentsGraph(...).propagate(ticker, date)`;
- repository LICENSE is Apache License 2.0.

### Anthropic Financial Services — accepted as professional-method upstream

Use the smallest relevant Skill. Preserve source/as-of discipline and adapt Claude/Cowork/MCP/Office-specific instructions to callable tools in the current environment.

Boundary: it supplies professional subproblem methods, not final CIS actions.

### QuantConnect LEAN — accepted as external quant/backtest engine

Accepted for:

- event-driven strategy backtests;
- technical/trend/position-sizing rule validation;
- stocks / ETFs / options strategy paths when the LEAN project and data support them;
- order, fee, portfolio path and strategy-performance statistics;
- future strategy-level validation before a new CIS rule is promoted from `experimental`.

Implementation boundary:

- upstream source stays external at `QuantConnect/Lean`;
- do **not** vendor, copy or git-submodule LEAN into CIS;
- CIS maintains `integrations/lean/cis_lean_adapter.py` and `references/quantconnect-lean.md`;
- adapter v1 uses the official Lean CLI local-backtest path plus result-JSON parsing;
- `execution_status=success` is not `research_quality=accepted`;
- LEAN has `decision_authority=none` and cannot change production rules automatically;
- current integration does not enable live trading or Broker execution.

As of 2026-08-09, QuantConnect's official Lean CLI documentation states that local engine commands use Docker and the CLI requires membership in a paid organization tier. Account, organization workspace, data licensing and credentials remain external to CIS.

### Buffett — optional external lens

Useful for business quality, management, moat, capital allocation and long-term owner discipline. It does not replace TradingAgents or Anthropic professional models.

## CIS ownership boundary

External systems do **not** replace:

- Runtime Guard and GitHub `main` verification;
- evidence gate, source grades and as-of discipline;
- look-ahead-bias checks;
- eight-dimension CIS scoring engine and coverage thresholds;
- four-layer trading framework;
- profit-taking + defensive-stop dual sell framework;
- cross-border ETF/QDII premium discipline;
- portfolio-data gate;
- personal investor rules;
- final Chinese synthesis, falsification conditions and review lifecycle.

LEAN additionally does not replace the CIS Backtest Validation Policy. Its outputs remain historical evidence subject to bias, execution-realism, out-of-sample and robustness review.

## Fallback policy

CIS self-authored expert agents are retained, but only as:

- fallback adapters when TradingAgents cannot run;
- conflict validators when external outputs materially disagree;
- CIS-specific adapters for evidence, trading and portfolio rules.

They should not duplicate a successful TradingAgents run by default.

For quantitative validation:

- LEAN is preferred for strategy-level event-driven backtests;
- `extensions/research_tooling/backtest_factor_strategy.py` remains a lightweight cross-sectional baseline evaluator;
- do not silently substitute the baseline evaluator when the user explicitly asked for LEAN.

## Not bundled / deferred

| Candidate | Decision | Reason |
|---|---|---|
| TradingAgents | External dependency/methodology; do not vendor full source by default | Stay current with active upstream; use stable methodology/adapter and verify runtime. |
| Anthropic `financial-services` | Live upstream preferred; snapshot optional | Prefer current Skill files; vendor only with upstream SHA, date, attribution and license review. |
| QuantConnect LEAN | **Accepted external quant engine; adapter only** | Adds strategy-level backtest capability without turning CIS into a trading-engine fork. |
| `agi-now/buffett-skills` | External optional dependency | License status must be reverified before redistribution. |
| FinRobot | Defer | Large functional overlap with TradingAgents + Anthropic; avoid duplicate decision/model stacks. |
| Microsoft Qlib / RD-Agent | Defer | LEAN now owns the default strategy-level quant/backtest role; add ML research only when a distinct need exists. |
| NautilusTrader | Defer | Overlaps LEAN's trading-engine role; avoid maintaining two default execution stacks. |
| OpenBB | Future optional data aggregation layer | Useful as data infrastructure; not needed as a decision engine. |

## Admission standard

Accept a future module only when it adds a non-overlapping capability, has callable dependencies, preserves source provenance and dates, has a clear failure mode, fits inside the CIS control envelope, and passes representative forward tests.
