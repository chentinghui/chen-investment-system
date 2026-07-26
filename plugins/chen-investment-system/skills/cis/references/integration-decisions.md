# CIS Integration Decisions

As-of: 2026-07-26. Reverify repository state, licenses, dependencies, and quality before changing these decisions.

## v1 architecture

- `cis` is the sole user-facing investment-research orchestrator.
- `buffett` is an external, optional qualitative ownership lens unless the user explicitly asks for standalone Buffett analysis.
- `stock-research-assistant` is retained only as a legacy Chinese alias that hands off to CIS.
- Installed capability and per-task runtime readiness are separate states.

## Accepted external capabilities

- `buffett`: accepted for business quality, management integrity and ability, moat, capital allocation, owner earnings, and sell discipline. Its upstream repository is not bundled because no clear LICENSE was found at publication time.
- `public-equity-investing`: accepted as an optional source-backed workflow engine for financials, valuation, earnings, macro transmission, ETF/index constituent diligence, portfolio risk, scenarios, research artifacts, and supporting model work. OpenAI bundled/curated source is not copied.

## Not bundled

| Candidate | Decision | Reason |
|---|---|---|
| `agi-now/buffett-skills` | External dependency only | Useful qualitative module, but no clear upstream LICENSE was found; link and attribution only, no source redistribution. |
| OpenAI Public Equity Investing | External optional enhancement | Third-party/curated plugin capability; reference by dependency name only. |
| `llmquant/skills@llmquant-etfs` | Defer | Focused ETF router, but its useful path depends on LLMQuant Data or a compatible holdings-data MCP that is not verified. |
| `claude-office-skills/skills@stock-analysis` | Reject | Duplicates accepted capabilities and includes environment-specific metadata and stale example data. |
| `claude-office-skills/skills@competitive-analysis` | Reject | Generic product/marketing intelligence rather than investor-grade public-equity analysis; overlaps CIS composite routing. |
| `rkreddyp/investrecipes@industry-research` | Reject | Non-Codex assumptions and broad research instructions already covered by the accepted engine. |

## Admission standard

Accept a future Skill only when it adds a non-overlapping decision capability, uses callable dependencies, has a redistribution-compatible license when bundled, preserves source provenance and as-of dates, has a clear failure mode for missing data, maps into the CIS envelope, and passes a representative forward test.
