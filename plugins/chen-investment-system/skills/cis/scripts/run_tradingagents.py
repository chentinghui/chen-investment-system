#!/usr/bin/env python3
"""CIS adapter for the external TauricResearch/TradingAgents package.

Execution readiness is not research quality. A successful propagate() returns an
external candidate that still requires CIS evidence/risk/scoring gates.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import date
from typing import Any


def emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))
    raise SystemExit(exit_code)


def package_available() -> bool:
    return importlib.util.find_spec("tradingagents") is not None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TradingAgents as a CIS external decision-candidate engine.")
    parser.add_argument("ticker")
    parser.add_argument("analysis_date", help="YYYY-MM-DD")
    parser.add_argument("--provider", help="Override TradingAgents llm_provider")
    parser.add_argument("--deep-model", help="Override deep_think_llm")
    parser.add_argument("--quick-model", help="Override quick_think_llm")
    parser.add_argument("--debate-rounds", type=int, help="Override max_debate_rounds")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    return parser.parse_args()


def validate_date(raw: str) -> str:
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        emit({"status": "invalid_input", "execution_status": "invalid_input", "research_quality": "rejected", "error": "analysis_date must be YYYY-MM-DD"}, 2)
        raise AssertionError("unreachable")


def main() -> None:
    args = parse_args()
    analysis_date = validate_date(args.analysis_date)

    if not package_available():
        emit({
            "status": "unavailable",
            "execution_status": "unavailable",
            "runtime_readiness": "upstream_only",
            "evidence_audit_status": "not_run",
            "research_quality": "rejected",
            "engine": "TradingAgents",
            "reason": "Python package 'tradingagents' is not installed in this runtime.",
            "ticker": args.ticker,
            "analysis_date": analysis_date,
        }, 3)

    if args.probe_only:
        emit({
            "status": "available",
            "execution_status": "not_run",
            "runtime_readiness": "installed_limited",
            "evidence_audit_status": "not_run",
            "research_quality": "unreviewed",
            "engine": "TradingAgents",
            "ticker": args.ticker,
            "analysis_date": analysis_date,
            "note": "Import probe passed. propagate(), APIs and data providers were not tested.",
        })

    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
    except Exception as exc:
        emit({
            "status": "error",
            "execution_status": "error",
            "runtime_readiness": "installed_limited",
            "evidence_audit_status": "not_run",
            "research_quality": "rejected",
            "engine": "TradingAgents",
            "error": f"Import failed: {exc}",
        }, 4)

    config = DEFAULT_CONFIG.copy()
    if args.provider:
        config["llm_provider"] = args.provider
    if args.deep_model:
        config["deep_think_llm"] = args.deep_model
    if args.quick_model:
        config["quick_think_llm"] = args.quick_model
    if args.debate_rounds is not None:
        if args.debate_rounds < 0:
            emit({"status": "invalid_input", "execution_status": "invalid_input", "research_quality": "rejected", "error": "debate rounds must be >= 0"}, 2)
        config["max_debate_rounds"] = args.debate_rounds

    try:
        graph = TradingAgentsGraph(debug=args.debug, config=config)
        state, decision = graph.propagate(args.ticker, analysis_date)
    except Exception as exc:
        emit({
            "status": "error",
            "execution_status": "error",
            "runtime_readiness": "installed_limited",
            "evidence_audit_status": "not_run",
            "research_quality": "rejected",
            "engine": "TradingAgents",
            "ticker": args.ticker,
            "analysis_date": analysis_date,
            "provider": config.get("llm_provider"),
            "error": str(exc),
            "note": "Execution failed; no TradingAgents decision is accepted.",
        }, 5)

    emit({
        "status": "success",
        "execution_status": "success",
        "runtime_readiness": "installed_ready",
        "evidence_audit_status": "not_run",
        "research_quality": "unreviewed",
        "engine": "TradingAgents",
        "ticker": args.ticker,
        "analysis_date": analysis_date,
        "provider": config.get("llm_provider"),
        "deep_think_llm": config.get("deep_think_llm"),
        "quick_think_llm": config.get("quick_think_llm"),
        "external_decision_candidate": decision,
        "state_present": state is not None,
        "cis_contract": "candidate_only_requires_CIS_quality_gates",
        "env_data_keys_present": {"ALPHA_VANTAGE_API_KEY": bool(os.getenv("ALPHA_VANTAGE_API_KEY"))},
    })


if __name__ == "__main__":
    main()
