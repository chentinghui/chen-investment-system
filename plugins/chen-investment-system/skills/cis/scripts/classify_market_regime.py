from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SIGNAL_WEIGHTS = {
    "index_above_sma200": 1.0,
    "sma50_slope_pct": 0.75,
    "breadth_above_sma200_pct": 1.25,
    "vix": 1.0,
    "realized_vol_20d": 0.75,
    "high_yield_oas_bps": 1.25,
    "credit_spread_change_bps_3m": 1.0,
}
TOTAL_WEIGHT = sum(SIGNAL_WEIGHTS.values())


def as_float(value: Any, label: str) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def strict_bool(value: Any, label: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise ValueError(f"{label} must be a JSON boolean, not {type(value).__name__}")
    return value


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("as_of"):
        raise ValueError("as_of is required")

    weighted_score = 0.0
    used_weight = 0.0
    used: dict[str, dict[str, float | int]] = {}

    def add_signal(name: str, signal: int) -> None:
        nonlocal weighted_score, used_weight
        weight = SIGNAL_WEIGHTS[name]
        weighted_score += signal * weight
        used_weight += weight
        used[name] = {"signal": signal, "weight": weight}

    above = strict_bool(payload.get("index_above_sma200"), "index_above_sma200")
    if above is not None:
        add_signal("index_above_sma200", 1 if above else -1)

    slope = as_float(payload.get("sma50_slope_pct"), "sma50_slope_pct")
    if slope is not None:
        add_signal("sma50_slope_pct", 1 if slope >= 0.5 else -1 if slope <= -0.5 else 0)

    breadth = as_float(payload.get("breadth_above_sma200_pct"), "breadth_above_sma200_pct")
    if breadth is not None:
        if not 0 <= breadth <= 100:
            raise ValueError("breadth_above_sma200_pct must be between 0 and 100")
        add_signal("breadth_above_sma200_pct", 1 if breadth >= 55 else -1 if breadth <= 45 else 0)

    vix = as_float(payload.get("vix"), "vix")
    if vix is not None:
        if vix < 0:
            raise ValueError("vix must be non-negative")
        add_signal("vix", 1 if vix < 20 else -1 if vix > 30 else 0)

    realized = as_float(payload.get("realized_vol_20d"), "realized_vol_20d")
    if realized is not None:
        if realized < 0:
            raise ValueError("realized_vol_20d must be non-negative")
        add_signal("realized_vol_20d", 1 if realized < 18 else -1 if realized > 30 else 0)

    hy_oas = as_float(payload.get("high_yield_oas_bps"), "high_yield_oas_bps")
    if hy_oas is not None:
        if hy_oas < 0:
            raise ValueError("high_yield_oas_bps must be non-negative")
        add_signal("high_yield_oas_bps", 1 if hy_oas < 400 else -1 if hy_oas > 600 else 0)

    credit_change = as_float(payload.get("credit_spread_change_bps_3m"), "credit_spread_change_bps_3m")
    if credit_change is not None:
        add_signal(
            "credit_spread_change_bps_3m",
            1 if credit_change <= -25 else -1 if credit_change >= 50 else 0,
        )

    coverage = used_weight / TOTAL_WEIGHT
    normalized_score = weighted_score / used_weight if used_weight else 0.0

    if coverage < 0.60 or len(used) < 3:
        regime = "insufficient"
        status = "insufficient"
    else:
        regime = "risk_on" if normalized_score >= 0.35 else "risk_off" if normalized_score <= -0.35 else "neutral"
        status = "experimental_baseline"

    return {
        "as_of": payload.get("as_of"),
        "regime": regime,
        "regime_score": round(normalized_score, 4),
        "raw_weighted_score": round(weighted_score, 4),
        "signals_used": used,
        "coverage": round(coverage, 4),
        "status": status,
        "warning": "Thresholds remain experimental. Regime is context, not a direct trading signal.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CIS market regime baseline classifier")
    parser.add_argument("input_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    try:
        result = classify(payload)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
