from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LEDGER = Path("runtime/evaluations/predictions.jsonl")
DEFAULT_HORIZONS_TRADING_DAYS = (5, 20, 60)
REQUIRED_PREDICTION_FIELDS = {
    "research_id",
    "as_of",
    "ticker",
    "cis_version",
    "score_status",
    "research_posture",
    "benchmark",
}
PUBLIC_PREDICTION_ALLOWED_FIELDS = {
    "research_id", "as_of", "ticker", "company", "cis_version", "methodology_version",
    "score_status", "research_posture", "benchmark", "sector_benchmark",
    "benchmark_mapping_version", "cis_score", "coverage_pct", "dimension_scores",
    "horizons_trading_days", "horizon_days", "schema_version", "recorded_at",
    "snapshot_type", "formal_research", "regime", "sector", "industry", "quant_score",
    "analysis_price", "analysis_price_source", "analysis_timestamp", "information_cutoff_at",
    "methodology_mode", "decision_context", "research_cohort", "setup_type",
    "technical_state", "relative_strength", "catalyst_status", "sentiment_status",
    "entry_zone_low", "entry_zone_high", "chase_limit", "stop_price", "stop_type",
    "target_1", "target_2", "planned_rr_target1", "planned_rr_target2",
    "thesis_falsifiers",
}
PUBLIC_OUTCOME_ALLOWED_FIELDS = {
    "research_id", "horizon_trading_days", "horizon_days", "evaluation_as_of",
    "entry_session_date", "exit_session_date", "entry_price", "exit_price",
    "entry_price_basis", "exit_price_basis", "return_semantics",
    "realized_return", "benchmark_return", "benchmark_entry_price", "benchmark_exit_price",
    "sector_benchmark_return", "max_favorable_excursion", "max_adverse_excursion",
    "max_drawdown_during_horizon", "path_metric_basis", "horizon_calendar_basis",
    "falsifier_triggered", "falsifier_status", "market_data_source",
    "market_data_retrieved_at", "terminal_event_handling", "schema_version", "recorded_at",
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


def _finite_float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _reject_unknown(payload: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"{label} contains fields not allowed in the public ledger: " + ", ".join(unknown))


def _normalize_horizons(payload: dict[str, Any]) -> list[int]:
    raw = payload.get("horizons_trading_days")
    if raw in (None, ""):
        legacy = payload.get("horizon_days")
        raw = [legacy] if legacy not in (None, "") else list(DEFAULT_HORIZONS_TRADING_DAYS)
    if not isinstance(raw, (list, tuple)):
        raise ValueError("horizons_trading_days must be an array")
    horizons: list[int] = []
    for value in raw:
        if isinstance(value, bool):
            raise ValueError("horizons_trading_days must contain positive integers")
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
    _reject_unknown(payload, PUBLIC_PREDICTION_ALLOWED_FIELDS, "prediction")
    missing = sorted(field for field in REQUIRED_PREDICTION_FIELDS if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("prediction missing required fields: " + ", ".join(missing))
    score = payload.get("cis_score")
    if score is not None:
        score_value = _finite_float(score, "cis_score")
        if not 0 <= score_value <= 100:
            raise ValueError("cis_score must be between 0 and 100")
    dimensions = payload.get("dimension_scores", {})
    if dimensions is not None and not isinstance(dimensions, dict):
        raise ValueError("dimension_scores must be an object")
    if isinstance(dimensions, dict):
        for name, value in dimensions.items():
            if value is None:
                continue
            number = _finite_float(value, f"dimension_scores.{name}")
            if not 0 <= number <= 100:
                raise ValueError(f"dimension_scores.{name} must be between 0 and 100")
    falsifiers = payload.get("thesis_falsifiers")
    if falsifiers is not None:
        if not isinstance(falsifiers, list) or any(not isinstance(item, str) for item in falsifiers):
            raise ValueError("thesis_falsifiers must be an array of research-only strings")

    event = dict(payload)
    event["as_of"] = _iso_date(payload["as_of"], "as_of")
    event["ticker"] = str(payload["ticker"]).strip().upper()
    event["benchmark"] = str(payload["benchmark"]).strip().upper()
    if payload.get("sector_benchmark"):
        event["sector_benchmark"] = str(payload["sector_benchmark"]).strip().upper()
    event["horizons_trading_days"] = _normalize_horizons(payload)
    event.pop("horizon_days", None)
    event["schema_version"] = int(payload.get("schema_version", 3))
    event["event_type"] = "prediction"
    event["recorded_at"] = payload.get("recorded_at") or now_iso()
    return event


def validate_outcome(payload: dict[str, Any], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
    _reject_unknown(payload, PUBLIC_OUTCOME_ALLOWED_FIELDS, "outcome")
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
    if isinstance(horizon, bool):
        raise ValueError("horizon_trading_days must be positive")
    horizon = int(horizon)
    if horizon <= 0:
        raise ValueError("horizon_trading_days must be positive")
    if prediction and horizon not in _normalize_horizons(prediction):
        raise ValueError(f"horizon {horizon} was not registered in prediction")

    event = dict(payload)
    event["evaluation_as_of"] = _iso_date(payload["evaluation_as_of"], "evaluation_as_of")
    event["horizon_trading_days"] = horizon
    event.pop("horizon_days", None)
    event["realized_return"] = _finite_float(payload["realized_return"], "realized_return")
    event["benchmark_return"] = _finite_float(payload["benchmark_return"], "benchmark_return")
    event["max_drawdown_during_horizon"] = _finite_float(
        payload["max_drawdown_during_horizon"], "max_drawdown_during_horizon"
    )
    if event["realized_return"] < -1 or event["benchmark_return"] < -1:
        raise ValueError("returns cannot be below -100%")
    if not -1 <= event["max_drawdown_during_horizon"] <= 0:
        raise ValueError("max_drawdown_during_horizon must be between -1 and 0")

    for field in ("sector_benchmark_return", "max_favorable_excursion", "max_adverse_excursion", "entry_price", "exit_price", "benchmark_entry_price", "benchmark_exit_price"):
        if payload.get(field) not in (None, ""):
            event[field] = _finite_float(payload[field], field)
    for field in ("entry_price", "exit_price", "benchmark_entry_price", "benchmark_exit_price"):
        if field in event and event[field] <= 0:
            raise ValueError(f"{field} must be positive")
    if "max_favorable_excursion" in event and event["max_favorable_excursion"] < 0:
        raise ValueError("max_favorable_excursion cannot be negative")
    if "max_adverse_excursion" in event and not -1 <= event["max_adverse_excursion"] <= 0:
        raise ValueError("max_adverse_excursion must be between -1 and 0")
    if "sector_benchmark_return" in event and event["sector_benchmark_return"] < -1:
        raise ValueError("sector_benchmark_return cannot be below -100%")

    event["falsifier_triggered"] = _strict_optional_bool(payload.get("falsifier_triggered"), "falsifier_triggered")
    event["schema_version"] = int(payload.get("schema_version", 3))
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
    parser = argparse.ArgumentParser(description="Optional append-only public-safe ledger for CIS research evaluation")
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
