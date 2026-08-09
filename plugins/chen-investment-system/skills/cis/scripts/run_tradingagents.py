#!/usr/bin/env python3
"""CIS adapter for the external TauricResearch/TradingAgents package.

This script never pretends TradingAgents is installed. It returns a small JSON
contract that CIS can inspect before using any external decision candidate.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import date
from typing import Any


def emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))
    raise SystemExit(exit_code)


def package_available() -> bool:
    return importlib.util.find_spec("tradingagents") is not None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TradingAgents as a CIS external decision-candidate engine.")
    parser.add_argument("ticker", help="Ticker accepted by the installed TradingAgents data providers, e.g. NVDA or 0700.HK")
    parser.add_argument("analysis_date", help="Analysis date in YYYY-MM-DD format")
    parser.add_argument("--provider", help="Override TradingAgents llm_provider")
    parser.add_argument("--deep-model", help="Override deep_think_llm")
    parser.add_argument("--quick-model", help="Override quick_think_llm")
    parser.add_argument("--debate-rounds", type=int, help="Override max_debate_rounds")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--probe-only", action="store_true", help="Only verify importability; do not run propagate().")
    return parser.parse_args()


def validate_date(raw: str) -> str:
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        emit({"status": "invalid_input", "error": "analysis_date must be YYYY-MM-DD"}, 2)
    return parsed.isoformat()


def main() -> None:
    args = parse_args()
    analysis_date = validate_date(args.analysis_date)

    if not package_available():
        emit(
            {
                "status": "unavailable",
                "runtime_readiness": "upstream_only",
                "engine": "TradingAgents",
                "reason": "Python package 'tradingagents' is not installed in this runtime.",
                "ticker": args.ticker,
                "analysis_date": analysis_date,
            },
            3,
        )

    if args.probe_only:
        emit(
            {
                "status": "available",
                "runtime_readiness": "installed_limited",
                "engine": "TradingAgents",
                "ticker": args.ticker,
                "analysis_date": analysis_date,
                "note": "Import probe passed. APIs/data providers were not tested.",
            }
        )

    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
    except Exception as exc:  # pragma: no cover - depends on external package
        emit(
            {
                "status": "error",
                "runtime_readiness": "installed_limited",
                "engine": "TradingAgents",
                "error": f"Import failed: {exc}",
            },
            4,
        )

    config = DEFAULT_CONFIG.copy()
    if args.provider:
        config["llm_provider"] = args.provider
    if args.deep_model:
        config["deep_think_llm"] = args.deep_model
    if args.quick_model:
        config["quick_think_llm"] = args.quick_model
    if args.debate_rounds is not None:
        if args.debate_rounds < 0:
            emit({"status": "invalid_input", "error": "debate rounds must be >= 0"}, 2)
        config["max_debate_rounds"] = args.debate_rounds

    try:
        graph = TradingAgentsGraph(debug=args.debug, config=config)
        state, decision = graph.propagate(args.ticker, analysis_date)
    except Exception as exc:  # pragma: no cover - depends on external APIs/runtime
        emit(
            {
                "status": "error",
                "runtime_readiness": "installed_limited",
                "engine": "TradingAgents",
                "ticker": args.ticker,
                "analysis_date": analysis_date,
                "provider": config.get("llm_provider"),
                "error": str(exc),
                "note": "Do not treat this as a TradingAgents decision. CIS should fall back or repair runtime dependencies.",
            },
            5,
        )

    emit(
        {
            "status": "success",
            "runtime_readiness": "installed_ready",
            "engine": "TradingAgents",
            "ticker": args.ticker,
            "analysis_date": analysis_date,
            "provider": config.get("llm_provider"),
            "deep_think_llm": config.get("deep_think_llm"),
            "quick_think_llm": config.get("quick_think_llm"),
            "external_decision_candidate": decision,
            "state_present": state is not None,
            "cis_contract": "candidate_only_requires_CIS_quality_gates",
            "env_data_keys_present": {
                "ALPHA_VANTAGE_API_KEY": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
            },
        }
    )


if __name__ == "__main__":
    main()
