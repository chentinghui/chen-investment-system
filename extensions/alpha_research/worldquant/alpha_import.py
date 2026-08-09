from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "cis.alpha_candidate.v1"
SOURCE = "worldquant_brain"


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _nested(mapping: dict[str, Any], *path: str) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _finite_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("%"):
            text = text[:-1].strip()
            try:
                number = float(text) / 100.0
            except ValueError:
                return None
            return number if math.isfinite(number) else None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _metric(payload: dict[str, Any], *keys: str, ratio: bool = False) -> float | None:
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    raw = _first(metrics, *keys)
    if raw is None:
        raw = _first(payload, *keys)
    value = _finite_number(raw)
    if value is None:
        return None
    if ratio and isinstance(raw, str) and raw.strip().endswith("%"):
        return value
    return value


def _normalize_settings(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("settings") if isinstance(payload.get("settings"), dict) else {}
    delay = _first(raw, "delay", "Delay")
    try:
        delay_value = int(delay) if delay is not None and not isinstance(delay, bool) else None
    except (TypeError, ValueError):
        delay_value = None

    decay = _finite_number(_first(raw, "decay", "Decay"))
    truncation = _finite_number(_first(raw, "truncation", "Truncation"))

    return {
        "region": _first(raw, "region", "Region") or _first(payload, "region", "Region"),
        "universe": _first(raw, "universe", "Universe") or _first(payload, "universe", "Universe"),
        "delay": delay_value,
        "neutralization": _first(raw, "neutralization", "Neutralization"),
        "decay": decay,
        "truncation": truncation,
    }


def normalize_worldquant_alpha(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("WorldQuant alpha payload must be a JSON object")

    expression = _first(payload, "expression", "formula", "code")
    if expression is None:
        expression = _nested(payload, "regular", "code")
    if expression is None:
        expression = _nested(payload, "alpha", "expression")
    expression_text = str(expression or "").strip()
    if not expression_text:
        raise ValueError("WorldQuant alpha payload must contain an expression/formula/code")

    settings = _normalize_settings(payload)
    raw_id = _first(payload, "alpha_id", "alphaId", "id")
    if raw_id is None:
        fingerprint_source = json.dumps(
            {"expression": expression_text, "settings": settings},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        raw_id = "wq-" + hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]

    canonical_source = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    metrics = {
        "sharpe": _metric(payload, "sharpe", "Sharpe"),
        "annual_return": _metric(payload, "annual_return", "return", "returns", "Returns", ratio=True),
        "turnover": _metric(payload, "turnover", "Turnover", ratio=True),
        "fitness": _metric(payload, "fitness", "Fitness"),
        "margin": _metric(payload, "margin", "Margin"),
        "max_drawdown": _metric(payload, "max_drawdown", "drawdown", "Drawdown", ratio=True),
        "coverage": _metric(payload, "coverage", "Coverage", ratio=True),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "alpha_id": str(raw_id).strip(),
        "name": str(_first(payload, "name", "alpha_name", "title") or raw_id).strip(),
        "expression": expression_text,
        "hypothesis": str(_first(payload, "hypothesis", "description", "idea") or "").strip() or None,
        "settings": settings,
        "metrics": metrics,
        "research_status": "unreviewed",
        "decision_authority": "none",
        "provenance": {
            "import_mode": "offline_or_api_json",
            "source_payload_sha256": hashlib.sha256(canonical_source.encode("utf-8")).hexdigest(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a WorldQuant BRAIN alpha export/API JSON into the CIS alpha-candidate contract"
    )
    parser.add_argument("input_json", help="WorldQuant BRAIN export or API JSON")
    parser.add_argument("--output", help="Optional normalized JSON output path")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    normalized = normalize_worldquant_alpha(payload)
    text = json.dumps(normalized, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
