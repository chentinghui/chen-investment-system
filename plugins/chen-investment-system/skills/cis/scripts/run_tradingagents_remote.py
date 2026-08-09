#!/usr/bin/env python3
"""Run original TradingAgents in GitHub Actions as a CIS candidate-only engine.

Execution success is deliberately separated from evidence/research quality.
A completed graph is not automatically an accepted CIS research result.

Security boundary:
- request payloads never contain API keys;
- each provider profile maps to exactly one credential environment variable;
- arbitrary OpenAI-compatible endpoints may use only OPENAI_COMPATIBLE_API_KEY;
- NVIDIA credentials are accepted only for NVIDIA's fixed endpoint;
- invalid requests are not echoed back into repository artifacts.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_BACKEND = "ollama"
DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct"
DEFAULT_ANALYSTS = ["market", "social", "news", "fundamentals"]
ALLOWED_ANALYSTS = set(DEFAULT_ANALYSTS)
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
ALLOWED_REQUEST_FIELDS = {
    "request_id",
    "ticker",
    "analysis_date",
    "backend",
    "provider_profile",
    "backend_url",
    "deep_model",
    "quick_model",
    "selected_analysts",
    "max_debate_rounds",
    "max_risk_rounds",
    "output_language",
}
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
TICKER_RE = re.compile(r"^[A-Z0-9.^_-]{1,24}$")


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


def _strict_nonnegative_int(value: Any, label: str, default: int) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a non-negative integer") from exc
    if number < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return number


def _validated_https_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{label} must be an absolute https URL")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} must not contain embedded credentials")
    return value.rstrip("/")


def validate_request(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("request must be a JSON object")
    unknown = sorted(set(payload) - ALLOWED_REQUEST_FIELDS)
    if unknown:
        raise ValueError("unknown or forbidden request fields: " + ", ".join(unknown))

    ticker = str(payload.get("ticker", "")).strip().upper()
    if not ticker or not TICKER_RE.fullmatch(ticker):
        raise ValueError("ticker is required and must contain only standard ticker characters")

    analysis_date = str(payload.get("analysis_date", "")).strip() or date.today().isoformat()
    date.fromisoformat(analysis_date)

    backend = str(payload.get("backend") or DEFAULT_BACKEND).strip().lower()
    if backend not in {"ollama", "openai_compatible"}:
        raise ValueError("backend must be 'ollama' or 'openai_compatible'")

    requested_profile = str(payload.get("provider_profile") or "").strip().lower()
    raw_backend_url = str(payload.get("backend_url") or "").strip()

    if backend == "ollama":
        if requested_profile not in {"", "local_ollama"}:
            raise ValueError("ollama backend requires provider_profile=local_ollama")
        provider_profile = "local_ollama"
        deep_model = str(payload.get("deep_model") or DEFAULT_OLLAMA_MODEL).strip()
        quick_model = str(payload.get("quick_model") or deep_model).strip()
        backend_url = raw_backend_url.rstrip("/") if raw_backend_url else OLLAMA_BASE_URL
        if backend_url != OLLAMA_BASE_URL:
            raise ValueError(f"ollama backend_url must equal {OLLAMA_BASE_URL}")
        credential_env = None
    else:
        deep_model = str(payload.get("deep_model") or "").strip()
        quick_model = str(payload.get("quick_model") or deep_model).strip()
        if not deep_model:
            raise ValueError("openai_compatible backend requires deep_model")

        if not requested_profile:
            # Backward-compatible inference is deliberately narrow: only the exact
            # NVIDIA endpoint may infer the NVIDIA profile. Any other endpoint is
            # treated as a custom endpoint and can use only the generic credential.
            requested_profile = (
                "nvidia" if raw_backend_url.rstrip("/") == NVIDIA_BASE_URL else "custom"
            )
        if requested_profile not in {"nvidia", "custom"}:
            raise ValueError("openai_compatible provider_profile must be nvidia or custom")
        provider_profile = requested_profile

        if provider_profile == "nvidia":
            backend_url = raw_backend_url.rstrip("/") if raw_backend_url else NVIDIA_BASE_URL
            if backend_url != NVIDIA_BASE_URL:
                raise ValueError(f"nvidia provider_profile requires backend_url={NVIDIA_BASE_URL}")
            credential_env = "NVIDIA_API_KEY"
        else:
            if not raw_backend_url:
                raise ValueError("custom provider_profile requires backend_url")
            backend_url = _validated_https_url(raw_backend_url, "backend_url")
            if backend_url == NVIDIA_BASE_URL:
                raise ValueError("NVIDIA endpoint must use provider_profile=nvidia")
            credential_env = "OPENAI_COMPATIBLE_API_KEY"

    if not deep_model or not quick_model:
        raise ValueError("deep_model and quick_model must be non-empty")

    debate_rounds = _strict_nonnegative_int(
        payload.get("max_debate_rounds"), "max_debate_rounds", 1
    )
    risk_rounds = _strict_nonnegative_int(
        payload.get("max_risk_rounds"), "max_risk_rounds", 1
    )

    raw_analysts = payload.get("selected_analysts", DEFAULT_ANALYSTS)
    if not isinstance(raw_analysts, list) or not raw_analysts:
        raise ValueError("selected_analysts must be a non-empty list")
    selected_analysts: list[str] = []
    for item in raw_analysts:
        analyst = str(item).strip().lower()
        if analyst not in ALLOWED_ANALYSTS:
            raise ValueError(f"unsupported analyst: {analyst}")
        if analyst not in selected_analysts:
            selected_analysts.append(analyst)

    request_id = str(payload.get("request_id") or "").strip()
    if not request_id:
        request_id = f"{ticker}-{analysis_date}"
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("request_id must match [A-Za-z0-9._-] and be at most 128 characters")

    return {
        "request_id": request_id,
        "ticker": ticker,
        "analysis_date": analysis_date,
        "backend": backend,
        "provider_profile": provider_profile,
        "backend_url": backend_url,
        "credential_env": credential_env,
        "deep_model": deep_model,
        "quick_model": quick_model,
        "selected_analysts": selected_analysts,
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
        f"- execution_status: `{result.get('execution_status')}`",
        f"- legacy runtime_readiness: `{result.get('runtime_readiness')}`",
        f"- evidence_audit_status: `{result.get('evidence_audit_status')}`",
        f"- research_quality: `{result.get('research_quality')}`",
        f"- request_id: `{result.get('request_id')}`",
        f"- analysis_date: `{result.get('analysis_date')}`",
        f"- selected analysts: `{', '.join(result.get('selected_analysts') or [])}`",
        f"- TradingAgents upstream SHA: `{result.get('tradingagents_upstream_sha')}`",
        f"- LLM backend: `{result.get('backend')}`",
        f"- provider profile: `{result.get('provider_profile')}`",
        f"- deep model: `{result.get('deep_model')}`",
        f"- quick model: `{result.get('quick_model')}`",
        "",
    ]
    if result.get("execution_status") != "success":
        lines.extend(["## Error", "", f"```text\n{result.get('error', 'unknown error')}\n```", ""])
        return "\n".join(lines)

    lines.extend([
        "## External Decision Candidate",
        "",
        str(result.get("external_decision_candidate") or "(empty)"),
        "",
        "> Execution completed, but evidence audit has not run. This candidate is unreviewed and cannot be treated as the final CIS action.",
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
        "This output is **not** the final CIS action. It must still pass CIS evidence audit, risk review, eight-dimension scoring, critical-dimension gates, and any applicable four-layer/ETF/portfolio gates.",
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
        credential_env = req.get("credential_env")
        if credential_env not in {"NVIDIA_API_KEY", "OPENAI_COMPATIBLE_API_KEY"}:
            raise RuntimeError("invalid credential routing for openai_compatible backend")
        api_key = os.getenv(str(credential_env))
        if not api_key:
            raise RuntimeError(f"{credential_env} is required for provider_profile={req['provider_profile']}")
        # TradingAgents' compatible backend reads this generic variable. Only the
        # single provider-specific credential selected above is copied into it.
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
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
        req = validate_request(raw)
    except Exception as exc:
        write_result(result_path, markdown_path, {
            "status": "invalid_input",
            "execution_status": "invalid_input",
            "runtime_readiness": "blocked",
            "evidence_audit_status": "not_run",
            "research_quality": "rejected",
            "error": str(exc),
        })
        return 2

    base_result = {
        **{key: value for key, value in req.items() if key != "credential_env"},
        "engine": "TradingAgents",
        "runner": "github_actions",
        "tradingagents_upstream_sha": os.getenv("TRADINGAGENTS_UPSTREAM_SHA", "unknown"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cis_contract": "candidate_only_requires_CIS_quality_gates",
        "evidence_audit_status": "not_run",
        "research_quality": "unreviewed",
    }

    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        config = DEFAULT_CONFIG.copy()
        configure_llm(req, config)
        config["data_vendors"] = dict(config.get("data_vendors") or {})
        config["data_vendors"].update({
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance",
            "fundamental_data": "yfinance",
            "news_data": "yfinance",
            "prediction_markets": "polymarket",
        })

        graph = TradingAgentsGraph(
            selected_analysts=tuple(req["selected_analysts"]),
            debug=False,
            config=config,
        )
        state, decision = graph.propagate(req["ticker"], req["analysis_date"])
        result = {
            **base_result,
            "status": "success",
            "execution_status": "success",
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
            "execution_status": "error",
            "runtime_readiness": "remote_limited",
            "research_quality": "rejected",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc()[-6000:],
            "note": "Execution failed. Do not treat this as a TradingAgents decision.",
        }
        write_result(result_path, markdown_path, result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
