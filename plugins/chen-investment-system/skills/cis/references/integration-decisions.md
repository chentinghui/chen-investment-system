# CIS Integration Decisions

As-of: 2026-08-09. Reverify repository state, licenses, dependencies, paths, and quality before changing these decisions.

## Current architecture

- `cis` is the sole user-facing investment-research orchestrator.
- `buffett` is an external, optional qualitative ownership lens unless the user explicitly asks for standalone Buffett analysis.
- Anthropic `financial-services` is the preferred professional Skill upstream for financial modeling, valuation, earnings research, initiating coverage, competitive analysis, thesis tracking, catalyst management, and related institutional research workflows.
- `stock-research-assistant` is retained only as a legacy Chinese alias that hands off to CIS.
- Installed capability and per-task runtime readiness are separate states.

## Accepted external capabilities

- `buffett`: accepted for business quality, management integrity and ability, moat, capital allocation, owner earnings, and sell discipline. Its upstream repository is not bundled because no clear LICENSE was found at publication time.
- `anthropics/financial-services`: accepted as the preferred professional-method upstream. Use the smallest relevant Skill, preserve source/as-of discipline, and adapt environment-specific Claude/Cowork/MCP/Office instructions to currently callable tools. Apache-2.0 was verified when this decision was recorded; reverify before vendoring or redistribution.

## Ownership boundary

Anthropic Financial Services does **not** replace the following CIS-owned capabilities:

- CIS sole orchestration and final research posture;
- evidence gate and evidence-confidence rules;
- risk gate and risk-manager override;
- eight-dimension CIS scoring engine and coverage thresholds;
- four-layer trading framework;
- profit-taking + defensive-stop dual sell framework;
- cross-border ETF/QDII premium discipline;
- portfolio-data gate;
- Chinese synthesis, falsification conditions, monitoring, and review lifecycle.

## Not bundled / deferred

| Candidate | Decision | Reason |
|---|---|---|
| `agi-now/buffett-skills` | External dependency only | Useful qualitative module, but no clear upstream LICENSE was found; link and attribution only, no source redistribution. |
| Anthropic `financial-services` | Live upstream preferred; snapshot optional | Prefer reading current upstream Skill files to avoid drift. Vendor only with explicit upstream SHA, sync date, attribution, and license review. |
| `llmquant/skills@llmquant-etfs` | Defer | Focused ETF router, but its useful path depends on LLMQuant Data or a compatible holdings-data MCP that is not verified. |
| `claude-office-skills/skills@stock-analysis` | Reject | Duplicates accepted capabilities and includes environment-specific metadata and stale example data. |
| `claude-office-skills/skills@competitive-analysis` | Reject | Generic product/marketing intelligence rather than investor-grade public-equity analysis; overlaps CIS composite routing. |
| `rkreddyp/investrecipes@industry-research` | Reject | Non-Codex assumptions and broad research instructions already covered by the accepted engine. |

## Admission standard

Accept a future Skill only when it adds a non-overlapping decision capability, uses callable dependencies, has a redistribution-compatible license when bundled, preserves source provenance and as-of dates, has a clear failure mode for missing data, maps into the CIS envelope, and passes a representative forward test.
