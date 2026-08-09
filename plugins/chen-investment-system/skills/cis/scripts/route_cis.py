from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "cis.route.v1"
ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "references" / "external-engine-registry.json"

VALID_ASSET_TYPES = {"equity", "etf", "crypto", "portfolio", "other"}
VALID_MODES = {"fast", "standard", "deep"}
VALID_INTENTS = {
    "fact_lookup",
    "general_research",
    "valuation",
    "earnings",
    "screening",
    "quant_research",
    "factor_discovery",
    "strategy_validation",
    "tactical_trade",
    "holding_review",
    "portfolio_review",
    "etf_review",
}

BASE_GATES = [
    "evidence_audit",
    "risk_review",
    "critical_dimension_gate",
    "cis_scoring",
]

INTENT_ENGINE_MAP = {
    "fact_lookup": ["openbb"],
    "general_research": ["openbb", "tradingagents"],
    "valuation": ["openbb", "tradingagents", "finrobot"],
    "earnings": ["openbb", "tradingagents", "finrobot"],
    "screening": ["openbb", "qlib"],
    "quant_research": ["openbb", "qlib"],
    "factor_discovery": ["openbb", "rd_agent", "qlib", "lean"],
    "strategy_validation": ["lean"],
    "tactical_trade": ["openbb", "tradingagents"],
    "holding_review": ["openbb", "tradingagents"],
    "portfolio_review": ["openbb", "qlib"],
    "etf_review": ["openbb"],
}

DEEP_SECONDARY = {
    "valuation": ["anthropic_financial_services"],
    "earnings": ["anthropic_financial_services"],
    "general_research": ["anthropic_financial_services"],
    "holding_review": ["anthropic_financial_services"],
}

PHASE_ORDER = {
    "openbb": "data",
    "tradingagents": "research",
    "finrobot": "specialist_modeling",
    "anthropic_financial_services": "specialist_modeling",
    "rd_agent": "research_and_development",
    "qlib": "quant_research",
    "lean": "strategy_validation",
}


def _load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "cis.external-engines.v1":
        raise ValueError("unsupported external engine registry schema")
    if data.get("controller") != "cis_control_layer":
        raise ValueError("registry must preserve CIS control authority")
    return data


def _strict_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a JSON boolean")
    return value


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_route(request: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or _load_registry()

    intent = request.get("intent")
    if intent not in VALID_INTENTS:
        raise ValueError(f"intent must be one of: {', '.join(sorted(VALID_INTENTS))}")

    asset_type = request.get("asset_type", "equity")
    if asset_type not in VALID_ASSET_TYPES:
        raise ValueError(f"asset_type must be one of: {', '.join(sorted(VALID_ASSET_TYPES))}")

    mode = request.get("mode", "standard")
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")

    explicit_lean = _strict_bool(request.get("explicit_lean", False), "explicit_lean")
    needs_backtest = _strict_bool(request.get("needs_backtest", False), "needs_backtest")
    needs_new_factor_rnd = _strict_bool(request.get("needs_new_factor_rnd", False), "needs_new_factor_rnd")
    needs_portfolio_optimization = _strict_bool(
        request.get("needs_portfolio_optimization", False), "needs_portfolio_optimization"
    )

    engines = list(INTENT_ENGINE_MAP[intent])

    if mode == "fast":
        # Keep only the minimum specialist set; never remove a user-requested validator.
        if intent in {"valuation", "earnings"}:
            engines = ["openbb", "finrobot"]
        elif intent in {"general_research", "tactical_trade", "holding_review"}:
            engines = ["openbb", "tradingagents"]
        elif intent == "screening":
            engines = ["openbb", "qlib"]

    if mode == "deep":
        engines.extend(DEEP_SECONDARY.get(intent, []))

    if explicit_lean or needs_backtest:
        engines.append("lean")
    if needs_new_factor_rnd:
        engines.extend(["rd_agent", "qlib", "lean"])
    if needs_portfolio_optimization:
        engines.append("qlib")

    # ETF product discipline belongs to CIS even if LEAN/OpenBB are also selected.
    cis_gates = list(BASE_GATES)
    if intent in {"tactical_trade"}:
        cis_gates.extend(["price_session_guard", "tactical_rr_gate", "four_layer_trading_gate"])
    if intent == "etf_review" or asset_type == "etf":
        cis_gates.append("etf_qdii_gate")
    if intent in {"portfolio_review", "holding_review"} or asset_type == "portfolio":
        cis_gates.append("portfolio_gate")

    engines = _dedupe(engines)
    cis_gates = _dedupe(cis_gates)

    engine_registry = registry["engines"]
    selected: list[dict[str, Any]] = []
    for engine_id in engines:
        if engine_id not in engine_registry:
            raise ValueError(f"engine missing from registry: {engine_id}")
        item = engine_registry[engine_id]
        selected.append(
            {
                "engine": engine_id,
                "name": item["name"],
                "phase": PHASE_ORDER[engine_id],
                "role": item["role"],
                "status": item["status"],
                "decision_authority": item["decision_authority"],
                "output_class": item["output_class"],
                "fallback": item.get("fallback", []),
            }
        )

    warnings: list[str] = []
    if asset_type == "crypto":
        warnings.append(
            "Crypto coverage depends on the actually available OpenBB/provider endpoints; do not assume equity-only engines support the asset."
        )
    if explicit_lean:
        warnings.append(
            "LEAN was explicitly requested: if unavailable, report unavailable/error and do not substitute the lightweight baseline evaluator."
        )
    if needs_new_factor_rnd or intent == "factor_discovery":
        warnings.append(
            "RD-Agent output is experimental. Promotion requires independent Qlib/LEAN validation plus CIS Backtest Validation."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "intent": intent,
        "asset_type": asset_type,
        "mode": mode,
        "controller": "cis_control_layer",
        "final_decision_authority": "cis_control_layer",
        "selected_engines": selected,
        "cis_gates": cis_gates,
        "execution_order": [
            "intake_and_as_of",
            "data_and_primary_source_verification",
            "general_research",
            "specialist_modeling",
            "quant_or_rnd_if_selected",
            "strategy_validation_if_selected",
            "evidence_and_risk_gates",
            "cis_scoring",
            "asset_specific_and_trade_gates",
            "final_chinese_synthesis",
        ],
        "conflict_policy": {
            "facts": "primary_source_then_freshness_then_provider_coverage",
            "valuation": "reconcile_assumptions_do_not_average",
            "quant_vs_fundamental": "separate_horizon_and_hypothesis_do_not_vote",
            "external_actions": "evidence_only_no_direct_action",
        },
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic CIS orchestration plan")
    parser.add_argument("request", help="JSON object describing the CIS task")
    args = parser.parse_args()
    try:
        request = json.loads(args.request)
        if not isinstance(request, dict):
            raise ValueError("request must be a JSON object")
        print(json.dumps(build_route(request), ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
