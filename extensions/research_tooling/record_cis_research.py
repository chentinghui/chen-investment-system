from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Any

from prediction_ledger import DEFAULT_HORIZONS_TRADING_DAYS, DEFAULT_LEDGER, record_prediction

CIS_VERSION = "0.4.3"


def make_research_id(ticker: str, as_of: str) -> str:
    safe_ticker = re.sub(r"[^A-Z0-9._-]", "-", ticker.upper())
    return f"CIS-{as_of.replace('-', '')}-{safe_ticker}-{uuid.uuid4().hex[:10]}"


def normalize_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"ticker", "as_of", "score_status", "research_posture", "benchmark"}
    missing = sorted(field for field in required if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("research snapshot missing required fields: " + ", ".join(missing))

    ticker = str(payload["ticker"]).strip().upper()
    as_of = str(payload["as_of"]).strip()
    event = dict(payload)
    event["research_id"] = str(payload.get("research_id") or make_research_id(ticker, as_of))
    event["ticker"] = ticker
    event["as_of"] = as_of
    event["cis_version"] = str(payload.get("cis_version") or CIS_VERSION)
    event["horizons_trading_days"] = payload.get(
        "horizons_trading_days", list(DEFAULT_HORIZONS_TRADING_DAYS)
    )
    event["snapshot_type"] = "formal_cis_research"
    event["formal_research"] = True
    event.setdefault("dimension_scores", {})
    event.setdefault("thesis_falsifiers", [])
    event.setdefault("regime", "unknown")
    event.setdefault("sector", "unknown")
    event.setdefault("quant_score", None)
    event.setdefault("analysis_price", None)
    event.setdefault("analysis_price_source", None)
    event.setdefault("methodology_mode", "chatgpt_native_tradingagents")
    return event


def record_snapshot(ledger: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return record_prediction(ledger, normalize_snapshot(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Optional CIS research-tooling snapshot recorder"
    )
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args()

    try:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
        result = record_snapshot(args.ledger, payload)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
