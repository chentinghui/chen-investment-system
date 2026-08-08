# CIS Agent Layer

This directory is the source-of-truth for Chen Investment System specialist agent role contracts.

The design borrows the useful structural ideas of `msitarzewski/agency-agents`—specialized identity, explicit mission, critical rules, concrete deliverables, repeatable workflow, handoff contracts, and measurable success criteria—while keeping all investment methodology, scoring, risk policy, and wording original to CIS.

## Architecture

- `chen-chief-investment-analyst.md`: chief/orchestrator. Owns routing, conflict resolution, quality gates, scoring synthesis, and final CIS conclusion.
- `fundamental-financial-analyst.md`: business quality, financial quality, accounting consistency, and capital allocation.
- `growth-competitive-analyst.md`: growth runway, unit economics, industry structure, moat direction, and competitive position.
- `valuation-analyst.md`: DCF/comps/expectations, scenario ranges, and valuation uncertainty.
- `technical-market-analyst.md`: trend, price structure, volume confirmation, and trading-location evidence.
- `macro-catalyst-strategist.md`: macro transmission, dated catalysts, expectations, and event paths.
- `positioning-flow-analyst.md`: institutional ownership, positioning, flows, concentration, and market-crowding evidence.
- `risk-manager.md`: downside mechanisms, fragility, invalidation conditions, and risk overrides.
- `evidence-auditor.md`: independent evidence/logic quality gate; defaults to unresolved when evidence is insufficient.
- `portfolio-manager.md`: holding-level and portfolio-level consequences when position context is complete.

## Operating rule

CIS uses the smallest expert team that can materially improve the answer. Specialists do not issue the final CIS research posture or portfolio action. Every specialist returns the common contract defined in `skills/cis/references/agent-contract.md`; the chief agent resolves conflicts and applies `skills/cis/references/scoring-engine.md` only after evidence and risk gates pass.
