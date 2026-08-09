from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LEDGER = Path("runtime/evaluations/predictions.jsonl")
REQUIRED_PREDICTION_FIELDS = {
    "research_id",
    "as_of",
    "ticker",
    "cis_version",
    "score_status",
    "research_posture",
    "horizon_days",
    "benchmark",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    return {
        str(event.get("research_id"))
        for event in events
        if event.get("event_type") == "prediction" and event.get("research_id")
    }


def outcome_ids(events: list[dict[str, Any]]) -> set[str]:
    return {
        str(event.get("research_id"))
        for event in events
        if event.get("event_type") == "outcome" and event.get("research_id")
    }


def validate_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_PREDICTION_FIELDS if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("prediction missing required fields: " + ", ".join(missing))
    horizon_days = int(payload["horizon_days"])
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")
    score = payload.get("cis_score")
    if score is not None and not 0 <= float(score) <= 100:
        raise ValueError("cis_score must be between 0 and 100")
    dimensions = payload.get("dimension_scores", {})
    if dimensions is not None and not isinstance(dimensions, dict):
        raise ValueError("dimension_scores must be an object")
    event = dict(payload)
    event["ticker"] = str(payload["ticker"]).strip().upper()
    event["horizon_days"] = horizon_days
    event["event_type"] = "prediction"
    event["recorded_at"] = payload.get("recorded_at") or now_iso()
    return event


def validate_outcome(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"research_id", "evaluation_as_of", "realized_return", "benchmark_return", "max_drawdown_during_horizon"}
    missing = sorted(field for field in required if payload.get(field) in (None, ""))
    if missing:
        raise ValueError("outcome missing required fields: " + ", ".join(missing))
    event = dict(payload)
    event["realized_return"] = float(payload["realized_return"])
    event["benchmark_return"] = float(payload["benchmark_return"])
    event["max_drawdown_during_horizon"] = float(payload["max_drawdown_during_horizon"])
    event["falsifier_triggered"] = bool(payload.get("falsifier_triggered", False))
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
    event = validate_outcome(payload)
    research_id = str(event["research_id"])
    if research_id not in prediction_ids(events):
        raise ValueError(f"cannot settle unknown research_id: {research_id}")
    if research_id in outcome_ids(events):
        raise ValueError(f"outcome already exists for research_id: {research_id}")
    append_event(ledger, event)
    return event


def materialize(ledger: Path) -> list[dict[str, Any]]:
    events = load_events(ledger)
    predictions = {
        str(event["research_id"]): dict(event)
        for event in events
        if event.get("event_type") == "prediction"
    }
    for event in events:
        if event.get("event_type") != "outcome":
            continue
        research_id = str(event.get("research_id"))
        if research_id in predictions:
            predictions[research_id]["outcome"] = dict(event)
    return list(predictions.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Immutable event ledger for CIS research predictions and outcomes")
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
