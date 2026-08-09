# CIS Integration Decisions

As-of: 2026-08-09. Reverify repository state, licenses, dependencies, paths, account requirements and quality before changing these decisions.

## Current architecture — CIS 0.4.5 Control Plane v2

- `cis` remains the sole user-facing entrypoint and final quality-control layer.
- CIS no longer tries to make one framework do every job. It routes each task to the strongest specialist layer with the least overlap.
- `OpenBB-finance/OpenBB` is accepted as the preferred external data-fabric layer when callable.
- `TauricResearch/TradingAgents` remains the default general-purpose multi-agent stock research methodology.
- `AI4Finance-Foundation/FinRobot` is accepted as the preferred deterministic financial-modeling engine for DCF/Comps/DDM/LBO/WACC/Monte Carlo and related equity-research workflows when callable.
- `microsoft/qlib` is accepted as the preferred external AI Quant / factor / ML research platform.
- `microsoft/RD-Agent` is accepted as the autonomous Quant R&D engine for factor/model discovery and iterative experiment generation.
- `QuantConnect/Lean` remains the accepted external event-driven strategy/backtest validation engine.
- Anthropic Financial Services remains an optional professional-method upstream and deep second opinion, not a reason to duplicate successful FinRobot work.
- CIS-owned rules remain authoritative for evidence, risk, scoring, tactical price discipline, ETF/QDII, portfolio context and final Chinese posture.

Machine-readable registry:

```text
references/external-engine-registry.json
```

Deterministic route planner:

```text
scripts/route_cis.py
```

## Accepted external capabilities

### OpenBB — accepted data fabric

Use for:

- market data;
- fundamentals;
- macro data;
- multi-provider data integration;
- standardized downstream inputs for research/quant/modeling.

Boundary:

- OpenBB does not become a final source-of-truth override;
- issuer filings, regulator filings and direct exchange sources retain higher authority when conflicts are material;
- provider/as-of/currency/unit must remain traceable;
- OpenBB has no decision authority.

### TradingAgents — accepted default general research methodology

Accepted for:

- fundamental / technical / news / sentiment research;
- bull/bear debate;
- research-manager synthesis;
- trader / risk / portfolio perspectives;
- original-runtime external candidate output when explicitly executed.

Boundary:

- Portfolio Manager output is `external_decision_candidate`, never final CIS action;
- original runtime is not required for ordinary analysis;
- technical/risk output does not replace CIS tactical, Evidence, Risk, ETF or Portfolio gates.

### FinRobot — accepted deterministic financial-modeling engine

Accepted for:

- DCF;
- comparable-company analysis;
- DDM/LBO;
- WACC;
- Monte Carlo valuation;
- earnings/modeling workflows;
- IC-style research output where the runtime is callable.

Boundary:

- prefer code-calculated numeric outputs and explicit assumptions/provenance;
- do not average conflicting target prices;
- reconcile WACC, growth, terminal value, margins, capex, peer set and accounting inputs;
- FinRobot agent/judge output has no final CIS action authority.

Fallback: Anthropic Financial Services or transparent CIS calculations. Fallback must be labeled and must never be reported as a FinRobot run.

### Microsoft Qlib — accepted Quant/ML research engine

Accepted for:

- factor research;
- ML signal/model research;
- quant screening;
- portfolio optimization;
- quant research backtests and model evaluation.

Boundary:

- Qlib owns research depth; local Quant tooling is only fallback/sanity tooling;
- all research remains subject to point-in-time data, OOS, leakage and robustness review;
- Qlib output cannot automatically modify CIS production score weights or publish actions.

### Microsoft RD-Agent — accepted autonomous Quant R&D engine

Accepted for:

- factor discovery;
- factor/model joint optimization;
- automatic research loops;
- experiment generation/implementation.

Boundary:

- use only for R&D intent, not routine single-stock questions;
- output is always experimental first;
- promotion path is `RD-Agent → Qlib → LEAN → CIS Backtest Validation → policy review`;
- no automatic production promotion.

### QuantConnect LEAN — accepted strategy-level validation engine

Accepted for:

- event-driven strategy backtests;
- technical/trend/position-sizing rule validation;
- stock/ETF/options strategy paths;
- order, fee, slippage and portfolio-path realism.

Implementation boundary:

- upstream source stays external at `QuantConnect/Lean`;
- CIS owns only adapter/contract/validation logic;
- `execution_status=success` is not `research_quality=accepted`;
- LEAN has `decision_authority=none`;
- current integration does not enable live trading or Broker execution.

### Anthropic Financial Services — accepted optional professional method upstream

Use only the smallest relevant skill and only when the environment can actually access it.

Good uses:

- model audit;
- earnings deep-dive;
- competitive analysis;
- thesis tracking;
- catalyst analysis;
- deep second opinion when the method is genuinely independent.

Do not run a duplicate DCF merely because another LLM skill exists after FinRobot already produced a traceable deterministic model.

## Specialist division of labor

```text
OpenBB       = data integration
TradingAgents= general investment research
FinRobot     = deterministic financial modeling
Qlib         = Quant / ML research
RD-Agent     = Quant R&D discovery loop
LEAN         = execution-realistic strategy validation
CIS          = evidence/risk/score/trade discipline/final decision
```

This is the default architectural doctrine.

## Quant research promotion pipeline

```text
Hypothesis
  ↓
RD-Agent (optional discovery/implementation)
  ↓
Qlib research / independent evaluation
  ↓
LEAN event-driven validation
  ↓
CIS Backtest Validation
  ↓
manual/policy review
  ↓
production rule
```

A factor/model/threshold may enter the pipeline without RD-Agent if it comes from another source, but it may not skip independent research and validation merely because the proposal came from a well-known project.

## CIS ownership boundary

External systems do **not** replace:

- Runtime Guard and upstream identity checks;
- evidence gate, source grades and as-of discipline;
- look-ahead-bias and stale-data checks;
- eight-dimension CIS scoring and coverage thresholds;
- four-layer trading framework;
- profit-taking + defensive-stop discipline;
- cross-border ETF/QDII premium discipline;
- portfolio-data gate;
- investor-specific constraints;
- final Chinese synthesis, falsification conditions and review lifecycle.

## Fallback policy

- OpenBB unavailable → primary/direct/public sources; disclose provider differences.
- TradingAgents runtime unavailable → reviewed ChatGPT-native TradingAgents methodology.
- FinRobot unavailable → Anthropic Financial Services or transparent CIS calculation.
- Qlib unavailable → local Quant extension only for limited screening/sanity; never call it equivalent Qlib.
- RD-Agent unavailable → report R&D stage not run; no silent equivalent substitute.
- LEAN unavailable → if explicitly requested, report unavailable/error; do not substitute baseline backtest.
- Anthropic unavailable → omit that enhancement without blocking unrelated routes.

## Not bundled / deferred

| Candidate | Decision | Reason |
|---|---|---|
| TradingAgents | Accepted external methodology/runtime; do not vendor full source | Strong general multi-agent research, but final authority remains CIS. |
| OpenBB | **Accepted external data fabric** | Adds broad provider/data integration without becoming a decision engine. |
| FinRobot | **Accepted external financial-modeling engine** | Distinct deterministic modeling value; use task-specific routing to avoid overlap. |
| Microsoft Qlib | **Accepted external Quant/ML research engine** | Distinct factor/model/portfolio research depth. |
| Microsoft RD-Agent | **Accepted external Quant R&D engine** | Distinct automated discovery/implementation capability; gated before production. |
| QuantConnect LEAN | **Accepted external strategy validation engine** | Distinct event-driven execution/backtest role. |
| Anthropic Financial Services | Accepted optional method upstream | Useful for professional methods and independent deep review. |
| Vibe-Trading | Optional/future adapter only | Broad integration convenience overlaps existing specialist engines; no reason to replace them. |
| NautilusTrader | Defer | Overlaps LEAN's default execution/backtest role. |
| `agi-now/buffett-skills` | Optional lens | Useful philosophy lens; not a core engine. |

## Admission standard for future modules

Accept a future module only when it adds a non-overlapping capability and has:

1. identifiable upstream and license;
2. callable runtime/dependencies;
3. stable input/output contract;
4. explicit data provenance/as-of semantics;
5. explicit failure mode;
6. no final CIS action authority;
7. representative validation;
8. a clear place in the route graph that does not duplicate an existing specialist without reason.
