from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MARKET_SESSIONS = {"premarket", "regular", "afterhours", "closed"}
PRICE_TYPES = {"premarket", "live", "afterhours", "last_close"}
EXPECTED_PRICE_TYPE = {
    "premarket": "premarket",
    "regular": "live",
    "afterhours": "afterhours",
    "closed": "last_close",
}
DIRECTIONS = {"long", "short"}


def _parse_timestamp(value: Any, label: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return dt


def _positive_number(value: Any, label: str, *, optional: bool = False) -> float | None:
    if optional and value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return number


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_price_context(payload: dict[str, Any]) -> dict[str, Any]:
    analysis_timestamp = _parse_timestamp(payload.get("analysis_timestamp"), "analysis_timestamp")
    quote_timestamp = _parse_timestamp(payload.get("quote_timestamp"), "quote_timestamp")
    if quote_timestamp > analysis_timestamp:
        raise ValueError("quote_timestamp cannot be later than analysis_timestamp")

    market_session = str(payload.get("market_session") or "").strip().lower()
    if market_session not in MARKET_SESSIONS:
        raise ValueError("market_session must be one of: " + ", ".join(sorted(MARKET_SESSIONS)))

    price_type = str(payload.get("price_type") or "").strip().lower()
    if price_type not in PRICE_TYPES:
        raise ValueError("price_type must be one of: " + ", ".join(sorted(PRICE_TYPES)))

    expected = EXPECTED_PRICE_TYPE[market_session]
    if price_type != expected:
        raise ValueError(
            f"price_type={price_type} is inconsistent with market_session={market_session}; "
            f"expected {expected}"
        )

    current_price = _positive_number(payload.get("current_price"), "current_price")
    age_seconds = (analysis_timestamp - quote_timestamp).total_seconds()
    semantics = {
        "regular": "live_current",
        "premarket": "extended_hours_current",
        "afterhours": "extended_hours_current",
        "closed": "last_close_reference",
    }[market_session]

    return {
        "status": "pass",
        "analysis_timestamp": _iso(analysis_timestamp),
        "quote_timestamp": _iso(quote_timestamp),
        "quote_age_seconds": round(age_seconds, 3),
        "market_session": market_session,
        "price_type": price_type,
        "price_semantics": semantics,
        "current_price": current_price,
    }


def _rr(entry: float, stop: float, target: float, direction: str) -> float:
    if direction == "long":
        risk = entry - stop
        reward = target - entry
    else:
        risk = stop - entry
        reward = entry - target
    if risk <= 0 or reward <= 0:
        raise ValueError("entry/stop/target geometry is invalid")
    return reward / risk


def _grade(rr_target1_worst: float) -> str:
    if rr_target1_worst < 1.0:
        return "reject"
    if rr_target1_worst < 1.5:
        return "weak_setup"
    if rr_target1_worst < 2.0:
        return "acceptable"
    return "attractive"


def evaluate_tactical_setup(payload: dict[str, Any]) -> dict[str, Any]:
    price_context = validate_price_context(payload)
    current_price = float(price_context["current_price"])

    direction = str(payload.get("direction") or "long").strip().lower()
    if direction not in DIRECTIONS:
        raise ValueError("direction must be long or short")

    entry_low = float(_positive_number(payload.get("entry_low"), "entry_low"))
    entry_high = float(_positive_number(payload.get("entry_high"), "entry_high"))
    stop = float(_positive_number(payload.get("stop"), "stop"))
    target1 = float(_positive_number(payload.get("target1"), "target1"))
    target2_raw = _positive_number(payload.get("target2"), "target2", optional=True)
    target2 = float(target2_raw) if target2_raw is not None else None
    chase_raw = _positive_number(payload.get("chase_limit"), "chase_limit", optional=True)
    chase_limit = float(chase_raw) if chase_raw is not None else None

    if entry_low > entry_high:
        raise ValueError("entry_low cannot exceed entry_high")

    if direction == "long":
        if not stop < entry_low <= entry_high < target1:
            raise ValueError("long setup requires stop < entry_low <= entry_high < target1")
        if target2 is not None and target2 <= target1:
            raise ValueError("long target2 must be above target1")
        if chase_limit is not None and chase_limit < entry_high:
            raise ValueError("long chase_limit cannot be below entry_high")
    else:
        if not target1 < entry_low <= entry_high < stop:
            raise ValueError("short setup requires target1 < entry_low <= entry_high < stop")
        if target2 is not None and target2 >= target1:
            raise ValueError("short target2 must be below target1")
        if chase_limit is not None and chase_limit > entry_low:
            raise ValueError("short chase_limit cannot be above entry_low")

    rr1_values = [_rr(entry_low, stop, target1, direction), _rr(entry_high, stop, target1, direction)]
    rr2_values = (
        [_rr(entry_low, stop, target2, direction), _rr(entry_high, stop, target2, direction)]
        if target2 is not None
        else None
    )
    rr1_worst = min(rr1_values)
    rr1_best = max(rr1_values)
    setup_grade = _grade(rr1_worst)

    if entry_low <= current_price <= entry_high:
        price_location = "in_entry_zone"
    elif direction == "long":
        if chase_limit is not None and current_price > chase_limit:
            price_location = "beyond_chase_limit"
        elif current_price < entry_low:
            price_location = "below_entry_zone"
        else:
            price_location = "above_entry_zone"
    else:
        if chase_limit is not None and current_price < chase_limit:
            price_location = "beyond_chase_limit"
        elif current_price > entry_high:
            price_location = "above_entry_zone"
        else:
            price_location = "below_entry_zone"

    if price_location == "beyond_chase_limit":
        trade_gate = "blocked_do_not_chase"
    elif setup_grade == "reject":
        trade_gate = "reject"
    elif price_location == "in_entry_zone":
        trade_gate = "eligible_setup"
    else:
        trade_gate = "wait_for_entry"

    midpoint = (entry_low + entry_high) / 2
    output: dict[str, Any] = {
        "status": "evaluated",
        "direction": direction,
        "price_context": price_context,
        "entry_zone": {"low": entry_low, "high": entry_high},
        "reference_entry_midpoint": round(midpoint, 6),
        "stop": stop,
        "target1": target1,
        "target2": target2,
        "chase_limit": chase_limit,
        "rr_target1_best": round(rr1_best, 4),
        "rr_target1_worst": round(rr1_worst, 4),
        "setup_grade": setup_grade,
        "price_location": price_location,
        "trade_gate": trade_gate,
        "warning": "Tactical gate evaluates price context and payoff geometry only; it does not replace CIS evidence, risk, score, or trading analysis.",
    }
    if rr2_values is not None:
        output["rr_target2_best"] = round(max(rr2_values), 4)
        output["rr_target2_worst"] = round(min(rr2_values), 4)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CIS tactical price context and risk/reward gate")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
        result = evaluate_tactical_setup(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
