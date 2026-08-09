#!/usr/bin/env python3
"""Run TradingAgents in a remote GitHub Actions environment for CIS.

Input:  runtime/tradingagents/request.json
Output: runtime/tradingagents/result.json and result.md

The default backend is local Ollama on the Actions runner, so the bridge does
not require a third-party LLM API key. Cloud OpenAI-compatible endpoints remain
supported as an optional quality upgrade.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BACKEND = "ollama"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        try:
            return jsonable(value.model_dump())
        except Exception:
            pass
    return str(value)


def validate_request(payload: dict[str, Any]) -> dict[str, Any]:
    ticker = str(payload.get("ticker", "")).strip().upper()
    if not ticker:
        raise ValueError("ticker is required")

    analysis_date = str(payload.get("analysis_date", "")).strip() or date.today().isoformat()
    date.fromisoformat(analysis_date)

    backend = str(payload.get("backend") or DEFAULT_BACKEND).strip().lower()
    if backend not in {"ollama", "openai_compatible"}:
        raise ValueError("backend must be 'ollama' or 'openai_compatible'")

    if backend == "ollama":
        deep_model = str(payload.get("deep_model") or DEFAULT_OLLAMA_MODEL)
        quick_model = str(payload.get("quick_model") or deep_model)
        backend_url = str(payload.get("backend_url") or OLLAMA_BASE_URL)
    else:
        deep_model = str(payload.get("deep_model") or "")
        quick_model = str(payload.get("quick_model") or deep_model)
        backend_url = str(payload.get("backend_url") or os.getenv("TRADINGAGENTS_LLM_BACKEND_URL") or "")
        if not deep_model or not backend_url:
            raise ValueError("openai_compatible backend requires deep_model and backend_url")

    debate_rounds = int(payload.get("max_debate_rounds", 1))
    risk_rounds = int(payload.get("max_risk_rounds", 1))
    if debate_rounds < 0 or risk_rounds < 0:
        raise ValueError("debate rounds must be >= 0")

    return {
        "request_id": str(payload.get("request_id") or f"{ticker}-{analysis_date}"),
        "ticker": ticker,
        "analysis_date": analysis_date,
        "backend": backend,
        "backend_url": backend_url,
        "deep_model": deep_model,
        "quick_model": quick_model,
        "max_debate_rounds": debate_rounds,
        "max_risk_rounds": risk_rounds,
        "output_language": str(payload.get("output_language") or "Chinese"),
    }


def compact_state(state: dict[str, Any] | None) -> dict[str, Any]:
    state = state or {}
    debate = state.get("investment_debate_state") or {}
    risk = state.get("risk_debate_state") or {}
    return {
        "market_report": jsonable(state.get("market_report")),
        "sentiment_report": jsonable(state.get("sentiment_report")),
        "news_report": jsonable(state.get("news_report")),
        "fundamentals_report": jsonable(state.get("fundamentals_report")),
        "bull_researcher": jsonable(debate.get("bull_history")),
        "bear_researcher": jsonable(debate.get("bear_history")),
        "research_manager": jsonable(debate.get("judge_decision")),
        "trader_plan": jsonable(state.get("trader_investment_plan")),
        "aggressive_risk": jsonable(risk.get("aggressive_history")),
        "neutral_risk": jsonable(risk.get("neutral_history")),
        "conservative_risk": jsonable(risk.get("conservative_history")),
        "portfolio_manager": jsonable(risk.get("judge_decision")),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# TradingAgents Remote Result — {result.get('ticker', 'UNKNOWN')}",
        "",
        f"- status: `{result.get('status')}`",
        f"- runtime_readiness: `{result.get('runtime_readiness')}`",
        f"- request_id: `{result.get('request_id')}`",
        f"- analysis_date: `{result.get('analysis_date')}`",
        f"- TradingAgents upstream SHA: `{result.get('tradingagents_upstream_sha')}`",
        f"- LLM backend: `{result.get('backend')}`",
        f"- deep model: `{result.get('deep_model')}`",
        f"- quick model: `{result.get('quick_model')}`",
        "",
    ]
    if result.get("status") != "success":
        lines.extend(["## Error", "", f"```text\n{result.get('error', 'unknown error')}\n```", ""])
        return "\n".join(lines)

    lines.extend([
        "## External Decision Candidate",
        "",
        str(result.get("external_decision_candidate") or "(empty)"),
        "",
    ])

    titles = [
        ("market_report", "Technical / Market Analyst"),
        ("sentiment_report", "Sentiment Analyst"),
        ("news_report", "News Analyst"),
        ("fundamentals_report", "Fundamentals Analyst"),
        ("bull_researcher", "Bull Researcher"),
        ("bear_researcher", "Bear Researcher"),
        ("research_manager", "Research Manager"),
        ("trader_plan", "Trader"),
        ("aggressive_risk", "Aggressive Risk Analyst"),
        ("neutral_risk", "Neutral Risk Analyst"),
        ("conservative_risk", "Conservative Risk Analyst"),
        ("portfolio_manager", "Portfolio Manager"),
    ]
    reports = result.get("reports") or {}
    for key, title in titles:
        if reports.get(key):
            lines.extend([f"## {title}", "", str(reports[key]), ""])

    lines.extend([
        "## CIS Contract",
        "",
        "This output is **not** the final CIS action. It must still pass CIS evidence audit, risk gate, eight-dimension scoring, and any applicable four-layer/ETF/portfolio gates.",
        "",
    ])
    return "\n".join(lines)


def write_result(path_json: Path, path_md: Path, payload: dict[str, Any]) -> None:
    path_json.parent.mkdir(parents=True, exist_ok=True)
    path_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    path_md.write_text(render_markdown(payload), encoding="utf-8")


def configure_llm(req: dict[str, Any], config: dict[str, Any]) -> None:
    if req["backend"] == "ollama":
        config["llm_provider"] = "ollama"
        config["backend_url"] = req["backend_url"]
    else:
        api_key = os.getenv("TRADINGAGENTS_API_KEY") or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        if not api_key:
            raise RuntimeError("TRADINGAGENTS_API_KEY is required for openai_compatible backend")
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = api_key
        config["llm_provider"] = "openai_compatible"
        config["backend_url"] = req["backend_url"]

    config["deep_think_llm"] = req["deep_model"]
    config["quick_think_llm"] = req["quick_model"]
    config["max_debate_rounds"] = req["max_debate_rounds"]
    config["max_risk_discuss_rounds"] = req["max_risk_rounds"]
    config["output_language"] = req["output_language"]
    config["llm_max_retries"] = 2
    config["checkpoint_enabled"] = False


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: run_tradingagents_remote.py REQUEST_JSON RESULT_JSON RESULT_MD", file=sys.stderr)
        return 2

    request_path, result_path, markdown_path = map(Path, sys.argv[1:4])
    raw = json.loads(request_path.read_text(encoding="utf-8"))

    try:
        req = validate_request(raw)
    except Exception as exc:
        write_result(result_path, markdown_path, {
            "status": "invalid_input",
            "runtime_readiness": "blocked",
            "error": str(exc),
            "raw_request": raw,
        })
        return 2

    base_result = {
        **req,
        "engine": "TradingAgents",
        "runner": "github_actions",
        "tradingagents_upstream_sha": os.getenv("TRADINGAGENTS_UPSTREAM_SHA", "unknown"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cis_contract": "candidate_only_requires_CIS_quality_gates",
    }

    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        config = DEFAULT_CONFIG.copy()
        configure_llm(req, config)

        # Use the keyless data stack where possible. External data still needs
        # CIS evidence auditing because provider availability can vary by run.
        config["data_vendors"] = dict(config.get("data_vendors") or {})
        config["data_vendors"].update({
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance",
            "fundamental_data": "yfinance",
            "news_data": "yfinance",
            "prediction_markets": "polymarket",
        })

        graph = TradingAgentsGraph(debug=False, config=config)
        state, decision = graph.propagate(req["ticker"], req["analysis_date"])
        result = {
            **base_result,
            "status": "success",
            "runtime_readiness": "remote_ready",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "external_decision_candidate": jsonable(decision),
            "reports": compact_state(state),
            "data_vendors": jsonable(config.get("data_vendors")),
        }
        write_result(result_path, markdown_path, result)
        return 0
    except Exception as exc:
        result = {
            **base_result,
            "status": "error",
            "runtime_readiness": "remote_limited",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc()[-6000:],
            "note": "Do not treat this as a TradingAgents decision; CIS must fall back or repair the remote runner.",
        }
        write_result(result_path, markdown_path, result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
