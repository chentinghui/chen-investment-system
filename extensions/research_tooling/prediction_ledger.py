from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LEDGER = Path("runtime/evaluations/predictions.jsonl")
DEFAULT_HORIZONS_TRADING_DAYS = (20, 60, 120, 250)
REQUIRED_PREDICTION_FIELDS = {
    "research_id",
    "as_of",
    "ticker",
    "cis_version",
    "score_status",
    "research_posture",
    "benchmark",
}
PUBLIC_LEDGER_FORBIDDEN_FIELDS = {
    "account", "account_id", "broker", "cost_basis", "holding_cost",
    "portfolio_value", "position_size", "shares", "user_name",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iso_date(value: Any, label: str) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc


def _strict_optional_bool(value: Any, label: str) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    raise ValueError(f"{label} must be true, false, or null")


def _normalize_horizons(payload: dict[str, Any]) -> list[int]:
    raw = payload.get("horizons_trading_days")
    if raw in (None, ""):
        legacy = payload.get("horizon_days")
        raw = [legacy] if legacy not in (None, "") else list(DEFAULT_HORIZONS_TRADING_DAYS)
    if not isinstance(raw, (list, tuple)):
        raise ValueError("horizons_trading_days must be an array")
    horizons: list[int] = []
    for value in raw:
        try:
            horizon = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("horizons_trading_days must contain positive integers") from exc
        if horizon <= 0:
            raise ValueError("horizons_trading_days must contain positive integers")
        horizons.append(horizon)
    normalized = sorted(set(horizons))
    if not normalized:
        raise ValueError("at least one evaluation horizon is required")
    return normalized


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_no}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"ledger line {line_no} must be a JSON object")
        events.append(event)
    return events


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def prediction_ids(events: list[dict[str, Any]]) -> set[str]:
    return {str(event.get("research_id")) for event in events if event.get("event_type") == "prediction" and event.get("research_id")}


def prediction_map(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(event["research_id"]): event for event in events if event.get("event_type") == "prediction" and event.get("research_id")}


def outcome_keys(events: list[dict[str, Any]]) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    predictions = prediction_map(events)
    for event in events:
        if event.get("event_type") != "outcome" or not event.get("research_id"):
            continue
        research_id = str(event["research_id"])
        horizon = event.get("horizon_trading_days", event.get("horizon_days"))
        if horizon in (None, ""):
            prediction = predictions.get(research_id, {})
            horizons = _normalize_horizons(prediction) if prediction else []
            if len(horizons) == 1:
                horizon = horizons[0]
        if horizon not in (None, ""):
            keys.add((research_id, int(horizon)))
    return keys


def validate_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_PREDICTION_FIELDS if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("prediction missing required fields: " + ", ".join(missing))
    forbidden = sorted(field for field in PUBLIC_LEDGER_FORBIDDEN_FIELDS if field in payload)
    if forbidden:
        raise ValueError("public prediction ledger must not contain private portfolio fields: " + ", ".join(forbidden))
    score = payload.get("cis_score")
    if score is not None and not 0 <= float(score) <= 100:
        raise ValueError("cis_score must be between 0 and 100")
    dimensions = payload.get("dimension_scores", {})
    if dimensions is not None and not isinstance(dimensions, dict):
        raise ValueError("dimension_scores must be an object")
    event = dict(payload)
    event["as_of"] = _iso_date(payload["as_of"], "as_of")
    event["ticker"] = str(payload["ticker"]).strip().upper()
    event["benchmark"] = str(payload["benchmark"]).strip().upper()
    if payload.get("sector_benchmark"):
        event["sector_benchmark"] = str(payload["sector_benchmark"]).strip().upper()
    event["horizons_trading_days"] = _normalize_horizons(payload)
    event.pop("horizon_days", None)
    event["schema_version"] = int(payload.get("schema_version", 2))
    event["event_type"] = "prediction"
    event["recorded_at"] = payload.get("recorded_at") or now_iso()
    return event


def validate_outcome(payload: dict[str, Any], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
    required = {"research_id", "evaluation_as_of", "realized_return", "benchmark_return", "max_drawdown_during_horizon"}
    missing = sorted(field for field in required if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("outcome missing required fields: " + ", ".join(missing))
    horizon = payload.get("horizon_trading_days", payload.get("horizon_days"))
    if horizon in (None, "") and prediction:
        horizons = _normalize_horizons(prediction)
        if len(horizons) == 1:
            horizon = horizons[0]
    if horizon in (None, ""):
        raise ValueError("outcome missing required field: horizon_trading_days")
    horizon = int(horizon)
    if horizon <= 0:
        raise ValueError("horizon_trading_days must be positive")
    if prediction and horizon not in _normalize_horizons(prediction):
        raise ValueError(f"horizon {horizon} was not registered in prediction")
    event = dict(payload)
    event["evaluation_as_of"] = _iso_date(payload["evaluation_as_of"], "evaluation_as_of")
    event["horizon_trading_days"] = horizon
    event.pop("horizon_days", None)
    event["realized_return"] = float(payload["realized_return"])
    event["benchmark_return"] = float(payload["benchmark_return"])
    event["max_drawdown_during_horizon"] = float(payload["max_drawdown_during_horizon"])
    for field in ("sector_benchmark_return", "max_favorable_excursion", "max_adverse_excursion", "entry_price", "exit_price", "benchmark_entry_price", "benchmark_exit_price"):
        if payload.get(field) not in (None, ""):
            event[field] = float(payload[field])
    event["falsifier_triggered"] = _strict_optional_bool(payload.get("falsifier_triggered"), "falsifier_triggered")
    event["event_type"] = "outcome"
    event["recorded_at"] = payload.get("recorded_at") or now_iso()
    return event


def record_prediction(ledger: Path, payload: dict[str, Any]) -> dict[str, Any]:
    events = load_events(ledger)
    event = validate_prediction(payload)
    research_id = str(event["research_id"])
    if research_id in prediction_ids(events):
        raise ValueError(f"prediction research_id already exists: {research_id}")
    append_event(ledger, event)
    return event


def record_outcome(ledger: Path, payload: dict[str, Any]) -> dict[str, Any]:
    events = load_events(ledger)
    predictions = prediction_map(events)
    research_id = str(payload.get("research_id", ""))
    prediction = predictions.get(research_id)
    if prediction is None:
        raise ValueError(f"cannot settle unknown research_id: {research_id}")
    event = validate_outcome(payload, prediction)
    key = (research_id, int(event["horizon_trading_days"]))
    if key in outcome_keys(events):
        raise ValueError(f"outcome already exists for research_id={research_id}, horizon={key[1]}")
    append_event(ledger, event)
    return event


def materialize(ledger: Path) -> list[dict[str, Any]]:
    events = load_events(ledger)
    predictions = {str(event["research_id"]): dict(event) for event in events if event.get("event_type") == "prediction"}
    outcomes_by_id: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("event_type") != "outcome":
            continue
        research_id = str(event.get("research_id"))
        if research_id in predictions:
            outcomes_by_id.setdefault(research_id, []).append(dict(event))
    for research_id, prediction in predictions.items():
        outcomes = sorted(outcomes_by_id.get(research_id, []), key=lambda event: int(event.get("horizon_trading_days", 0)))
        prediction["outcomes"] = outcomes
        if len(outcomes) == 1:
            prediction["outcome"] = outcomes[0]
    return list(predictions.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional append-only ledger for CIS research evaluation")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record")
    record.add_argument("input_json", type=Path)
    settle = sub.add_parser("settle")
    settle.add_argument("input_json", type=Path)
    sub.add_parser("show")
    args = parser.parse_args()
    try:
        if args.command == "record":
            payload = json.loads(args.input_json.read_text(encoding="utf-8"))
            result = record_prediction(args.ledger, payload)
        elif args.command == "settle":
            payload = json.loads(args.input_json.read_text(encoding="utf-8"))
            result = record_outcome(args.ledger, payload)
        else:
            result = {"records": materialize(args.ledger)}
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
