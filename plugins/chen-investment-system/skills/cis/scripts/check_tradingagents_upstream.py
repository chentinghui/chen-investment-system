from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATUS = Path("runtime/tradingagents/upstream-status.json")
UPSTREAM_API = "https://api.github.com/repos/TauricResearch/TradingAgents/commits/main"


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def should_check(status: dict[str, Any], now: datetime, force: bool = False) -> bool:
    if force:
        return True
    ttl_days = int(status.get("check_ttl_days", 7))
    last = status.get("last_checked_at")
    if not last:
        return True
    return now >= parse_time(str(last)) + timedelta(days=ttl_days)


def fetch_current_sha(url: str = UPSTREAM_API) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "chen-investment-system",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)
    sha = str(payload.get("sha", "")).strip()
    if not sha:
        raise RuntimeError("upstream response did not contain sha")
    return sha


def apply_check(status: dict[str, Any], current_sha: str, now: datetime) -> dict[str, Any]:
    result = dict(status)
    ttl_days = int(result.get("check_ttl_days", 7))
    result.setdefault("upstream", "TauricResearch/TradingAgents")
    result.setdefault("branch", "main")
    result["observed_sha"] = current_sha
    result["last_checked_at"] = iso_z(now)
    result["check_ttl_days"] = ttl_days
    result["next_check_not_before"] = iso_z(now + timedelta(days=ttl_days))
    result["policy"] = "use_time_check_with_7_day_ttl_stable_baseline"

    reviewed_sha = str(result.get("reviewed_sha", ""))
    if current_sha == reviewed_sha:
        if str(result.get("review_status", "")).startswith("reviewed"):
            pass
        else:
            result["review_status"] = "reviewed_current"
        result["upstream_check"] = "current"
    else:
        result["review_status"] = "review_required"
        result["detected_at"] = iso_z(now)
        result["upstream_check"] = "change_detected"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check TradingAgents upstream SHA only when the CIS TTL is due")
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--force", action="store_true", help="Ignore TTL and check now")
    parser.add_argument("--no-write", action="store_true", help="Do not persist refreshed status")
    args = parser.parse_args()

    if not args.status.is_file():
        raise SystemExit(f"status file not found: {args.status}")
    status = json.loads(args.status.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)

    if not should_check(status, now, args.force):
        print(json.dumps({
            "upstream_check": "cached_current",
            "last_checked_at": status.get("last_checked_at"),
            "next_check_not_before": status.get("next_check_not_before"),
            "review_status": status.get("review_status"),
            "observed_sha": status.get("observed_sha"),
        }, ensure_ascii=False, indent=2))
        return 0

    try:
        current_sha = fetch_current_sha()
    except Exception as exc:
        print(json.dumps({
            "upstream_check": "unavailable",
            "error": f"{type(exc).__name__}: {exc}",
            "stable_baseline_allowed": True,
        }, ensure_ascii=False, indent=2))
        return 0

    refreshed = apply_check(status, current_sha, now)
    if not args.no_write:
        args.status.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(refreshed, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
