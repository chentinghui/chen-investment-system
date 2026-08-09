from __future__ import annotations

import argparse
import json
import math
from datetime import date
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

# Calendar-day tolerance is deliberately conservative and only a freshness guard,
# not a forecasting parameter. Market/volatility signals should be near the same
# session; credit series are allowed a wider publication lag.
MAX_SIGNAL_AGE_DAYS = {
    "index_above_sma200": 4,
    "sma50_slope_pct": 4,
    "breadth_above_sma200_pct": 4,
    "vix": 4,
    "realized_vol_20d": 4,
    "high_yield_oas_bps": 14,
    "credit_spread_change_bps_3m": 14,
}


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


def _iso_date(value: Any, label: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("as_of"):
        raise ValueError("as_of is required")
    overall_as_of = _iso_date(payload.get("as_of"), "as_of")
    raw_signal_as_of = payload.get("signal_as_of") or {}
    if not isinstance(raw_signal_as_of, dict):
        raise ValueError("signal_as_of must be an object mapping signal names to YYYY-MM-DD")

    weighted_score = 0.0
    used_weight = 0.0
    used: dict[str, dict[str, float | int | str]] = {}
    missing_signal_dates: list[str] = []
    stale_signals: list[str] = []

    def add_signal(name: str, signal: int) -> None:
        nonlocal weighted_score, used_weight
        weight = SIGNAL_WEIGHTS[name]
        weighted_score += signal * weight
        used_weight += weight

        signal_date_raw = raw_signal_as_of.get(name)
        if signal_date_raw in (None, ""):
            missing_signal_dates.append(name)
            signal_date_text = "missing"
            age_days: int | str = "unknown"
        else:
            signal_date = _iso_date(signal_date_raw, f"signal_as_of.{name}")
            if signal_date > overall_as_of:
                raise ValueError(f"signal_as_of.{name} cannot be after as_of")
            age_days = (overall_as_of - signal_date).days
            signal_date_text = signal_date.isoformat()
            if age_days > MAX_SIGNAL_AGE_DAYS[name]:
                stale_signals.append(name)

        used[name] = {
            "signal": signal,
            "weight": weight,
            "as_of": signal_date_text,
            "age_days": age_days,
        }

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
    freshness_status = (
        "missing_signal_as_of"
        if missing_signal_dates
        else "stale"
        if stale_signals
        else "pass"
    )

    if coverage < 0.60 or len(used) < 3 or freshness_status != "pass":
        regime = "insufficient"
        status = "insufficient"
    else:
        regime = "risk_on" if normalized_score >= 0.35 else "risk_off" if normalized_score <= -0.35 else "neutral"
        status = "experimental_baseline"

    return {
        "as_of": overall_as_of.isoformat(),
        "regime": regime,
        "regime_score": round(normalized_score, 4),
        "raw_weighted_score": round(weighted_score, 4),
        "signals_used": used,
        "coverage": round(coverage, 4),
        "freshness_status": freshness_status,
        "missing_signal_dates": sorted(missing_signal_dates),
        "stale_signals": sorted(stale_signals),
        "status": status,
        "warning": "Thresholds and freshness tolerances remain experimental. Regime is context, not a direct trading signal.",
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
