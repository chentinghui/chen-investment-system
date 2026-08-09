# CIS Integration Decisions

As-of: 2026-08-09. Reverify repository state, licenses, dependencies, paths, account requirements and quality before changing these decisions.

## Current architecture — CIS 0.4.5

- `cis` is the sole user-facing entrypoint and final quality-control layer.
- `TauricResearch/TradingAgents` methodology is the default general-purpose stock/issuer research method.
- Anthropic `financial-services` is the preferred professional Skill upstream for DCF, Comps, three-statement models, earnings, model audit/update, competitive analysis, thesis tracking and catalysts.
- CIS-owned rules remain authoritative for evidence, scoring, trading framework, ETF/QDII, portfolio context and final Chinese posture.
- Quant/Backtest/Prediction/Evaluation remain optional repository-owned research tooling.
- CIS currently has **no external strategy-level trading/backtest engine connected**.
- `stock-research-assistant` is only a legacy alias that hands off to CIS.

## Accepted external capabilities

### TradingAgents — accepted as default research methodology

Accepted for:

- fundamental / technical / news / sentiment analyst team;
- bull/bear debate;
- research manager synthesis;
- trader proposal;
- risk-management debate;
- portfolio-manager external candidate decision when original runtime is explicitly executed.

Boundary:

- Portfolio Manager output is `external_decision_candidate`, never the final CIS action.
- TradingAgents technical output does not replace CIS four-layer trading rules.
- TradingAgents risk output does not replace CIS evidence audit, portfolio data gate or ETF/QDII rules.
- Code freshness does not imply real-time data freshness.
- Historical analysis must preserve `analysis_date` and prevent look-ahead leakage.

### Anthropic Financial Services — accepted as professional-method upstream

Use the smallest relevant Skill. Preserve source/as-of discipline and adapt tool-specific instructions to callable tools in the current environment.

Boundary: it supplies professional subproblem methods, not final CIS actions.

## Quant / Backtest ownership boundary

Current repository-owned capabilities:

- `extensions/research_tooling/quant_factor_engine.py` for cross-sectional candidate ranking;
- `extensions/research_tooling/backtest_factor_strategy.py` for lightweight `date,ticker,score,forward_return` validation;
- Prediction/Evaluation tools for research tracking and calibration.

These tools do not constitute a full event-driven trading engine. If a requested strategy requires order simulation, complex position paths, options lifecycle handling, or other unsupported execution semantics, CIS must disclose the limitation instead of silently substituting the baseline evaluator.

## Buffett / other optional lenses

Useful external frameworks may be added as non-authoritative research perspectives. They do not replace CIS quality gates.

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

## Fallback policy

CIS self-authored expert agents are retained, but only as:

- fallback adapters when TradingAgents cannot run;
- conflict validators when external outputs materially disagree;
- CIS-specific adapters for evidence, trading and portfolio rules.

They should not duplicate a successful TradingAgents run by default.

For quantitative validation, use the smallest repository-owned research tool that correctly models the question. Do not represent an unsupported execution model as if it were validated.

## Not bundled / deferred

| Candidate | Decision | Reason |
|---|---|---|
| TradingAgents | External dependency/methodology; do not vendor full source by default | Stay current with active upstream; use stable methodology/adapter and verify runtime. |
| Anthropic `financial-services` | Live upstream preferred; snapshot optional | Prefer current Skill files; vendor only with upstream SHA, date, attribution and license review. |
| `agi-now/buffett-skills` | External optional dependency | License status must be reverified before redistribution. |
| FinRobot | Defer | Large functional overlap with TradingAgents + Anthropic; avoid duplicate decision/model stacks. |
| Microsoft Qlib / RD-Agent | Defer | Add ML research only when it supplies a distinct Alpha-discovery capability and has a clear validation contract. |
| NautilusTrader | Defer | Do not add a second execution stack without a concrete need and maintenance plan. |
| OpenBB | Future optional data aggregation layer | Useful as data infrastructure; not needed as a decision engine. |

## Admission standard

Accept a future module only when it adds a non-overlapping capability, has callable dependencies, preserves source provenance and dates, has a clear failure mode, fits inside the CIS control envelope, and passes representative forward tests.
