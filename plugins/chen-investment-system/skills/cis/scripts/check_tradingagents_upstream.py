from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATUS = Path("runtime/tradingagents/upstream-status.json")
TRADINGAGENTS_API = "https://api.github.com/repos/TauricResearch/TradingAgents/commits/main"
LEAN_TAGS_API = (
    "https://hub.docker.com/v2/repositories/quantconnect/lean/tags"
    "?page_size=100&ordering=last_updated"
)
DEFAULT_TTL_DAYS = 7


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def should_check(status: dict[str, Any], now: datetime, force: bool = False) -> bool:
    if force:
        return True
    ttl_days = int(status.get("check_ttl_days", DEFAULT_TTL_DAYS))
    last = status.get("last_checked_at")
    if not last:
        return True
    return now >= parse_time(str(last)) + timedelta(days=ttl_days)


def fetch_json(url: str, *, user_agent: str = "chen-investment-system") -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def fetch_current_sha(url: str = TRADINGAGENTS_API) -> str:
    payload = fetch_json(url)
    sha = str(payload.get("sha", "")).strip()
    if not sha:
        raise RuntimeError("TradingAgents upstream response did not contain sha")
    return sha


def latest_numeric_lean_tag(payload: dict[str, Any]) -> str:
    tags: list[int] = []
    for item in payload.get("results", []):
        name = str(item.get("name", "")).strip()
        if name.isdigit():
            tags.append(int(name))
    if not tags:
        raise RuntimeError("LEAN Docker Hub response did not contain a numeric build tag")
    return str(max(tags))


def fetch_latest_lean_tag(url: str = LEAN_TAGS_API) -> str:
    payload = fetch_json(url)
    if not isinstance(payload, dict):
        raise RuntimeError("LEAN Docker Hub response was not an object")
    return latest_numeric_lean_tag(payload)


def apply_check(status: dict[str, Any], current_sha: str, now: datetime) -> dict[str, Any]:
    """Refresh the backward-compatible top-level TradingAgents status."""
    result = dict(status)
    ttl_days = int(result.get("check_ttl_days", DEFAULT_TTL_DAYS))
    result.setdefault("upstream", "TauricResearch/TradingAgents")
    result.setdefault("branch", "main")
    result["observed_sha"] = current_sha
    result["last_checked_at"] = iso_z(now)
    result["check_ttl_days"] = ttl_days
    result["next_check_not_before"] = iso_z(now + timedelta(days=ttl_days))
    result["policy"] = "use_time_check_with_7_day_ttl_stable_baseline"

    reviewed_sha = str(result.get("reviewed_sha", ""))
    if current_sha == reviewed_sha:
        if not str(result.get("review_status", "")).startswith("reviewed"):
            result["review_status"] = "reviewed_current"
        result["upstream_check"] = "current"
    else:
        result["review_status"] = "review_required"
        result["detected_at"] = iso_z(now)
        result["upstream_check"] = "change_detected"
    return result


def apply_lean_check(status: dict[str, Any], current_tag: str, now: datetime) -> dict[str, Any]:
    """Refresh LEAN status without ever changing the reviewed/pinned engine tag."""
    result = dict(status)
    ttl_days = int(result.get("check_ttl_days", DEFAULT_TTL_DAYS))
    result.setdefault("upstream", "quantconnect/lean")
    result.setdefault("source", "Docker Hub numeric build tags")
    result.setdefault("reviewed_tag", "")
    result.setdefault("auto_upgrade", False)
    result.setdefault("validation_required_before_upgrade", True)
    result["observed_tag"] = current_tag
    result["last_checked_at"] = iso_z(now)
    result["check_ttl_days"] = ttl_days
    result["next_check_not_before"] = iso_z(now + timedelta(days=ttl_days))
    result["policy"] = "use_time_check_with_7_day_ttl_stable_baseline"

    reviewed_tag = str(result.get("reviewed_tag", "")).strip()
    if current_tag == reviewed_tag:
        if not str(result.get("review_status", "")).startswith("reviewed"):
            result["review_status"] = "reviewed_current"
        result["upstream_check"] = "current"
    else:
        result["review_status"] = "review_required"
        result["detected_at"] = iso_z(now)
        result["upstream_check"] = "change_detected"

    # This checker is intentionally detection-only. A new tag must first pass
    # CIS LEAN integration/backtest validation before the pinned image changes.
    result["auto_upgrade"] = False
    result["validation_required_before_upgrade"] = True
    return result


def cached_summary(status: dict[str, Any], *, version_key: str) -> dict[str, Any]:
    return {
        "upstream_check": "cached_current",
        "last_checked_at": status.get("last_checked_at"),
        "next_check_not_before": status.get("next_check_not_before"),
        "review_status": status.get("review_status"),
        version_key: status.get(version_key),
    }


def unavailable_summary(exc: Exception) -> dict[str, Any]:
    return {
        "upstream_check": "unavailable",
        "error": f"{type(exc).__name__}: {exc}",
        "stable_baseline_allowed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CIS external upstreams only when their 7-day TTL is due"
    )
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument(
        "--component",
        choices=("all", "tradingagents", "lean"),
        default="all",
        help="Check only the upstream relevant to the current task",
    )
    parser.add_argument("--force", action="store_true", help="Ignore TTL and check now")
    parser.add_argument("--no-write", action="store_true", help="Do not persist refreshed status")
    args = parser.parse_args()

    if not args.status.is_file():
        raise SystemExit(f"status file not found: {args.status}")
    status = json.loads(args.status.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    refreshed = dict(status)
    output: dict[str, Any] = {}
    changed = False

    if args.component in ("all", "tradingagents"):
        if should_check(status, now, args.force):
            try:
                current_sha = fetch_current_sha()
                refreshed = apply_check(refreshed, current_sha, now)
                output["tradingagents"] = {
                    "upstream_check": refreshed.get("upstream_check"),
                    "last_checked_at": refreshed.get("last_checked_at"),
                    "next_check_not_before": refreshed.get("next_check_not_before"),
                    "review_status": refreshed.get("review_status"),
                    "observed_sha": refreshed.get("observed_sha"),
                }
                changed = True
            except Exception as exc:
                output["tradingagents"] = unavailable_summary(exc)
        else:
            output["tradingagents"] = cached_summary(status, version_key="observed_sha")

    if args.component in ("all", "lean"):
        lean_status = status.get("lean")
        if not isinstance(lean_status, dict):
            lean_status = {}
        if should_check(lean_status, now, args.force):
            try:
                current_tag = fetch_latest_lean_tag()
                new_lean_status = apply_lean_check(lean_status, current_tag, now)
                refreshed["lean"] = new_lean_status
                output["lean"] = {
                    "upstream_check": new_lean_status.get("upstream_check"),
                    "last_checked_at": new_lean_status.get("last_checked_at"),
                    "next_check_not_before": new_lean_status.get("next_check_not_before"),
                    "review_status": new_lean_status.get("review_status"),
                    "observed_tag": new_lean_status.get("observed_tag"),
                    "reviewed_tag": new_lean_status.get("reviewed_tag"),
                    "auto_upgrade": False,
                }
                changed = True
            except Exception as exc:
                output["lean"] = unavailable_summary(exc)
        else:
            output["lean"] = cached_summary(lean_status, version_key="observed_tag")
            output["lean"]["reviewed_tag"] = lean_status.get("reviewed_tag")
            output["lean"]["auto_upgrade"] = False

    if changed and not args.no_write:
        args.status.write_text(
            json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
