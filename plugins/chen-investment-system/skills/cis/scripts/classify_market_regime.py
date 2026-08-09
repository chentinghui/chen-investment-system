from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SIGNAL_COUNT = 5


def as_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    score = 0
    used: dict[str, int] = {}

    if "index_above_sma200" in payload and payload["index_above_sma200"] is not None:
        value = bool(payload["index_above_sma200"])
        used["index_above_sma200"] = 1 if value else -1
        score += used["index_above_sma200"]

    slope = as_float(payload.get("sma50_slope_pct"))
    if slope is not None:
        used["sma50_slope_pct"] = 1 if slope > 0 else -1 if slope < 0 else 0
        score += used["sma50_slope_pct"]

    breadth = as_float(payload.get("breadth_above_sma200_pct"))
    if breadth is not None:
        signal = 1 if breadth >= 55 else -1 if breadth <= 45 else 0
        used["breadth_above_sma200_pct"] = signal
        score += signal

    vix = as_float(payload.get("vix"))
    if vix is not None:
        signal = 1 if vix < 20 else -1 if vix > 30 else 0
        used["vix"] = signal
        score += signal

    credit = as_float(payload.get("credit_spread_change_bps_3m"))
    if credit is not None:
        signal = 1 if credit <= 0 else -1 if credit >= 50 else 0
        used["credit_spread_change_bps_3m"] = signal
        score += signal

    coverage = len(used) / SIGNAL_COUNT
    if coverage < 0.60:
        regime = "insufficient"
        status = "insufficient"
    else:
        regime = "risk_on" if score >= 2 else "risk_off" if score <= -2 else "neutral"
        status = "experimental_baseline"

    return {
        "as_of": payload.get("as_of"),
        "regime": regime,
        "regime_score": score,
        "signals_used": used,
        "coverage": round(coverage, 4),
        "status": status,
        "warning": "Baseline thresholds are experimental and must be validated out of sample before becoming production rules.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CIS market regime baseline classifier")
    parser.add_argument("input_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = classify(payload)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
