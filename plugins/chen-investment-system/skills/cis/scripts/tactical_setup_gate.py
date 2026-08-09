from __future__ import annotations

import argparse
import calendar
import json
import math
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SUPPORTED_EXCHANGES = {"XNAS", "XNYS"}
MARKET_TIMEZONE = ZoneInfo("America/New_York")
MARKET_SESSIONS = {"premarket", "regular", "afterhours", "closed"}
PRICE_TYPES = {"premarket", "live", "afterhours", "last_close"}
EXPECTED_PRICE_TYPE = {
    "premarket": "premarket",
    "regular": "live",
    "afterhours": "afterhours",
    "closed": "last_close",
}
DIRECTIONS = {"long", "short"}
STOP_TYPES = {"hard_price", "close_confirmation", "technical_invalidation"}
MAX_ALLOWED_ACTIVE_QUOTE_AGE_SECONDS = 3600


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


def _strict_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be a JSON boolean")
    return value


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return first + timedelta(days=delta + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    current = date(year, month, last_day)
    delta = (current.weekday() - weekday) % 7
    return current - timedelta(days=delta)


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _full_holidays(year: int) -> set[date]:
    holidays = {
        _observed(date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter_sunday(year) - timedelta(days=2),
        _last_weekday(year, 5, 0),
        _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _observed(date(year, 12, 25)),
    }
    if year >= 2022:
        holidays.add(_observed(date(year, 6, 19)))
    return holidays


def _is_trading_day(day: date) -> bool:
    if day.weekday() >= 5:
        return False
    holidays: set[date] = set()
    for year in (day.year - 1, day.year, day.year + 1):
        holidays.update(_full_holidays(year))
    return day not in holidays


def _regular_close(day: date) -> time:
    # Common US equity early-close baseline. Exceptional closures still require
    # manual verification by the evidence layer.
    thanksgiving = _nth_weekday(day.year, 11, 3, 4)
    if day == thanksgiving + timedelta(days=1) and _is_trading_day(day):
        return time(13, 0)
    if day.month == 12 and day.day == 24 and _is_trading_day(day):
        return time(13, 0)
    if day.month == 7 and day.day == 3 and _is_trading_day(day):
        return time(13, 0)
    return time(16, 0)


def _derived_session(timestamp: datetime) -> tuple[str, date, time]:
    local = timestamp.astimezone(MARKET_TIMEZONE)
    day = local.date()
    close_time = _regular_close(day)
    if not _is_trading_day(day):
        return "closed", day, close_time
    current = local.time().replace(tzinfo=None)
    if time(4, 0) <= current < time(9, 30):
        return "premarket", day, close_time
    if time(9, 30) <= current < close_time:
        return "regular", day, close_time
    if close_time <= current < time(20, 0):
        return "afterhours", day, close_time
    return "closed", day, close_time


def _previous_trading_day(day: date) -> date:
    cursor = day - timedelta(days=1)
    while not _is_trading_day(cursor):
        cursor -= timedelta(days=1)
    return cursor


def _last_completed_session(analysis_timestamp: datetime) -> date:
    local = analysis_timestamp.astimezone(MARKET_TIMEZONE)
    day = local.date()
    if _is_trading_day(day) and local.time().replace(tzinfo=None) >= _regular_close(day):
        return day
    return _previous_trading_day(day)


def validate_price_context(payload: dict[str, Any]) -> dict[str, Any]:
    analysis_timestamp = _parse_timestamp(payload.get("analysis_timestamp"), "analysis_timestamp")
    quote_timestamp = _parse_timestamp(payload.get("quote_timestamp"), "quote_timestamp")
    if quote_timestamp > analysis_timestamp:
        raise ValueError("quote_timestamp cannot be later than analysis_timestamp")

    exchange = str(payload.get("exchange") or "").strip().upper()
    if exchange not in SUPPORTED_EXCHANGES:
        raise ValueError("exchange must be XNAS or XNYS")

    derived_session, session_date, regular_close = _derived_session(analysis_timestamp)
    supplied_session = str(payload.get("market_session") or "").strip().lower()
    if supplied_session and supplied_session not in MARKET_SESSIONS:
        raise ValueError("market_session must be one of: " + ", ".join(sorted(MARKET_SESSIONS)))
    if supplied_session and supplied_session != derived_session:
        raise ValueError(
            f"market_session={supplied_session} conflicts with exchange calendar/time; expected {derived_session}"
        )
    market_session = derived_session

    price_type = str(payload.get("price_type") or "").strip().lower()
    if price_type not in PRICE_TYPES:
        raise ValueError("price_type must be one of: " + ", ".join(sorted(PRICE_TYPES)))
    expected = EXPECTED_PRICE_TYPE[market_session]
    if price_type != expected:
        raise ValueError(
            f"price_type={price_type} is inconsistent with market_session={market_session}; expected {expected}"
        )

    current_price = _positive_number(payload.get("current_price"), "current_price")
    age_seconds = (analysis_timestamp - quote_timestamp).total_seconds()

    quote_observation_session, quote_observation_date, _ = _derived_session(quote_timestamp)

    if market_session == "closed":
        raw_quote_session = str(payload.get("quote_session_date") or "").strip()
        if not raw_quote_session:
            raise ValueError("quote_session_date is required when market_session=closed")
        try:
            quote_session_date = date.fromisoformat(raw_quote_session)
        except ValueError as exc:
            raise ValueError("quote_session_date must be YYYY-MM-DD") from exc
        expected_last_session = _last_completed_session(analysis_timestamp)
        if quote_session_date != expected_last_session:
            raise ValueError(
                f"last_close must reference the most recent completed session {expected_last_session.isoformat()}"
            )
        if quote_observation_date != quote_session_date:
            raise ValueError("last_close quote_timestamp date must match quote_session_date")
        freshness_status = "last_close_reference"
        max_age_seconds = None
    else:
        max_age_raw = _positive_number(
            payload.get("quote_max_age_seconds"), "quote_max_age_seconds"
        )
        max_age_seconds = float(max_age_raw)
        if max_age_seconds > MAX_ALLOWED_ACTIVE_QUOTE_AGE_SECONDS:
            raise ValueError(
                f"quote_max_age_seconds cannot exceed {MAX_ALLOWED_ACTIVE_QUOTE_AGE_SECONDS} for active-session tactical use"
            )
        if age_seconds > max_age_seconds:
            raise ValueError(
                f"quote is stale: age={round(age_seconds, 3)}s exceeds allowed {max_age_seconds}s"
            )
        quote_session_date = quote_observation_date
        if quote_session_date != session_date:
            raise ValueError("active-session quote must come from the current exchange session date")
        if quote_observation_session != market_session:
            raise ValueError(
                f"quote_timestamp belongs to {quote_observation_session}, not analysis market_session={market_session}"
            )
        freshness_status = "fresh"

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
        "quote_max_age_seconds": max_age_seconds,
        "quote_freshness_status": freshness_status,
        "quote_observation_session": quote_observation_session,
        "quote_session_date": quote_session_date.isoformat(),
        "exchange": exchange,
        "market_timezone": str(MARKET_TIMEZONE),
        "market_session": market_session,
        "session_date": session_date.isoformat(),
        "regular_close_local": regular_close.isoformat(timespec="minutes"),
        "price_type": price_type,
        "price_semantics": semantics,
        "current_price": current_price,
        "calendar_basis": "US-equity stdlib baseline; exceptional exchange closures require evidence-layer verification",
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

    raw_stop_type = str(payload.get("stop_type") or "").strip().lower()
    if not raw_stop_type:
        raise ValueError("stop_type is required")
    stop_type = raw_stop_type
    if stop_type not in STOP_TYPES:
        raise ValueError("stop_type must be one of: " + ", ".join(sorted(STOP_TYPES)))

    if stop_type == "hard_price":
        if payload.get("stop_confirmation_met") in (None, ""):
            stop_confirmation_met = None
        else:
            stop_confirmation_met = _strict_bool(
                payload.get("stop_confirmation_met"), "stop_confirmation_met"
            )
    else:
        stop_confirmation_met = _strict_bool(
            payload.get("stop_confirmation_met"), "stop_confirmation_met"
        )

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
        if chase_limit is not None and not entry_high <= chase_limit < target1:
            raise ValueError("long chase_limit must satisfy entry_high <= chase_limit < target1")
    else:
        if not target1 < entry_low <= entry_high < stop:
            raise ValueError("short setup requires target1 < entry_low <= entry_high < stop")
        if target2 is not None and target2 >= target1:
            raise ValueError("short target2 must be below target1")
        if chase_limit is not None and not target1 < chase_limit <= entry_low:
            raise ValueError("short chase_limit must satisfy target1 < chase_limit <= entry_low")

    rr1_values = [_rr(entry_low, stop, target1, direction), _rr(entry_high, stop, target1, direction)]
    rr2_values = (
        [_rr(entry_low, stop, target2, direction), _rr(entry_high, stop, target2, direction)]
        if target2 is not None
        else None
    )
    rr1_worst = min(rr1_values)
    rr1_best = max(rr1_values)
    setup_grade = _grade(rr1_worst)

    stop_breached = current_price <= stop if direction == "long" else current_price >= stop
    target1_reached = current_price >= target1 if direction == "long" else current_price <= target1

    # Confirmed invalidation is persistent. A setup cannot become active again merely
    # because price later rebounds back above/below the numeric stop.
    if stop_confirmation_met is True:
        price_location = "invalidation_confirmed"
        setup_state = "invalidated"
        trade_gate = "invalidated_reprice_required"
    elif stop_breached:
        price_location = "stop_breached"
        if stop_type == "hard_price":
            setup_state = "invalidated"
            trade_gate = "invalidated_reprice_required"
        else:
            setup_state = "stop_breached_unconfirmed"
            trade_gate = "blocked_pending_stop_confirmation"
    elif target1_reached:
        price_location = "target1_reached"
        setup_state = "expired_target_reached"
        trade_gate = "setup_expired_reprice_required"
    elif entry_low <= current_price <= entry_high:
        price_location = "in_entry_zone"
        setup_state = "active"
        trade_gate = "reject" if setup_grade == "reject" else "eligible_setup"
    elif direction == "long":
        if chase_limit is not None and current_price > chase_limit:
            price_location = "beyond_chase_limit"
            setup_state = "active_but_overextended"
            trade_gate = "blocked_do_not_chase"
        elif current_price < entry_low:
            price_location = "below_entry_zone"
            setup_state = "active_waiting"
            trade_gate = "reject" if setup_grade == "reject" else "wait_for_entry"
        else:
            price_location = "above_entry_zone"
            setup_state = "active_waiting"
            trade_gate = "reject" if setup_grade == "reject" else "wait_for_entry"
    else:
        if chase_limit is not None and current_price < chase_limit:
            price_location = "beyond_chase_limit"
            setup_state = "active_but_overextended"
            trade_gate = "blocked_do_not_chase"
        elif current_price > entry_high:
            price_location = "above_entry_zone"
            setup_state = "active_waiting"
            trade_gate = "reject" if setup_grade == "reject" else "wait_for_entry"
        else:
            price_location = "below_entry_zone"
            setup_state = "active_waiting"
            trade_gate = "reject" if setup_grade == "reject" else "wait_for_entry"

    midpoint = (entry_low + entry_high) / 2
    output: dict[str, Any] = {
        "status": "evaluated",
        "direction": direction,
        "price_context": price_context,
        "entry_zone": {"low": entry_low, "high": entry_high},
        "reference_entry_midpoint": round(midpoint, 6),
        "stop": stop,
        "stop_type": stop_type,
        "stop_confirmation_met": stop_confirmation_met,
        "target1": target1,
        "target2": target2,
        "chase_limit": chase_limit,
        "rr_target1_best": round(rr1_best, 4),
        "rr_target1_worst": round(rr1_worst, 4),
        "setup_grade": setup_grade,
        "setup_state": setup_state,
        "price_location": price_location,
        "trade_gate": trade_gate,
        "warning": "Tactical gate evaluates session/freshness, persistent invalidation state, and payoff geometry only; it does not replace CIS evidence, risk, score, or trading analysis.",
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
