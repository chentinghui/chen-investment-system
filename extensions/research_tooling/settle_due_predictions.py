from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from prediction_ledger import DEFAULT_LEDGER, load_events, outcome_keys, prediction_map, record_outcome

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


@dataclass(frozen=True)
class DailyBar:
    session_date: date
    adjusted_close: float
    price_basis: str = "adjusted_close"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _unix_day(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())


def fetch_yahoo_daily(symbol: str, start: date, end: date) -> list[DailyBar]:
    encoded = urllib.parse.quote(symbol, safe="")
    params = urllib.parse.urlencode(
        {
            "period1": _unix_day(start),
            "period2": _unix_day(end + timedelta(days=1)),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
    )
    request = urllib.request.Request(
        f"{YAHOO_CHART.format(symbol=encoded)}?{params}",
        headers={"User-Agent": "chen-investment-system/0.4.5-research-tooling"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo error for {symbol}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"Yahoo returned no history for {symbol}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    adjclose_blocks = indicators.get("adjclose") or []
    adjusted = (adjclose_blocks[0].get("adjclose") if adjclose_blocks else None) or []

    # Do not silently substitute raw close for Adjusted Close. Mixing raw and
    # adjusted price semantics can create false returns around splits/dividends.
    bars: list[DailyBar] = []
    for index, timestamp in enumerate(timestamps):
        raw = adjusted[index] if index < len(adjusted) else None
        if raw is None:
            continue
        value = float(raw)
        if not math.isfinite(value) or value <= 0:
            continue
        session = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date()
        bars.append(DailyBar(session, value, "adjusted_close"))
    if not bars:
        raise RuntimeError(f"Yahoo returned no usable adjusted closes for {symbol}")
    return bars


def _first_index_after(bars: list[DailyBar], as_of: date) -> int | None:
    for index, bar in enumerate(bars):
        if bar.session_date > as_of:
            return index
    return None


def _bar_on_date(bars: list[DailyBar], target: date) -> DailyBar | None:
    for bar in bars:
        if bar.session_date == target:
            return bar
    return None


def path_metrics(path: list[float]) -> dict[str, float]:
    if not path or path[0] <= 0:
        raise ValueError("price path must start with a positive value")
    entry = path[0]
    relative = [value / entry - 1 for value in path]
    peak = path[0]
    max_drawdown = 0.0
    for value in path:
        peak = max(peak, value)
        drawdown = value / peak - 1
        max_drawdown = min(max_drawdown, drawdown)
    return {
        "realized_return": path[-1] / entry - 1,
        "max_favorable_excursion": max(relative),
        "max_adverse_excursion": min(relative),
        "max_drawdown_during_horizon": max_drawdown,
    }


def _benchmark_return_exact(
    bars: list[DailyBar], start: date, end: date
) -> tuple[float, DailyBar, DailyBar]:
    entry = _bar_on_date(bars, start)
    exit_bar = _bar_on_date(bars, end)
    if entry is None or exit_bar is None:
        raise ValueError("benchmark does not exactly cover the evaluation sessions")
    return exit_bar.adjusted_close / entry.adjusted_close - 1, entry, exit_bar


def settle_prediction(
    prediction: dict[str, Any],
    already_settled: set[tuple[str, int]],
    *,
    today: date,
    fetcher: Callable[[str, date, date], list[DailyBar]] = fetch_yahoo_daily,
) -> tuple[list[dict[str, Any]], list[str]]:
    research_id = str(prediction["research_id"])
    as_of = date.fromisoformat(str(prediction["as_of"]))
    horizons = [int(value) for value in prediction.get("horizons_trading_days", [])]
    if not horizons and prediction.get("horizon_days"):
        horizons = [int(prediction["horizon_days"])]
    pending = [h for h in sorted(set(horizons)) if (research_id, h) not in already_settled]
    if not pending:
        return [], []

    start = as_of - timedelta(days=15)
    benchmark_symbol = str(prediction["benchmark"])
    benchmark_bars = fetcher(benchmark_symbol, start, today)
    calendar_entry_index = _first_index_after(benchmark_bars, as_of)
    if calendar_entry_index is None:
        return [], [f"{research_id}: benchmark has no next session after research date"]

    entry_session = benchmark_bars[calendar_entry_index].session_date
    stock_bars = fetcher(str(prediction["ticker"]), start, today)
    entry_bar = _bar_on_date(stock_bars, entry_session)
    if entry_bar is None:
        return [], [f"{research_id}: no executable stock price on next benchmark session {entry_session}"]

    sector_symbol = str(prediction.get("sector_benchmark") or "").strip()
    sector_bars = fetcher(sector_symbol, start, today) if sector_symbol else []

    outcomes: list[dict[str, Any]] = []
    warnings: list[str] = []
    for horizon in pending:
        target_index = calendar_entry_index + horizon
        if target_index >= len(benchmark_bars):
            continue
        exit_session = benchmark_bars[target_index].session_date
        if exit_session > today:
            continue

        exit_bar = _bar_on_date(stock_bars, exit_session)
        if exit_bar is None:
            warnings.append(
                f"{research_id}/{horizon}: no stock price on target benchmark session {exit_session}; left unresolved"
            )
            continue

        path_bars = [
            bar for bar in stock_bars
            if entry_session <= bar.session_date <= exit_session
        ]
        if not path_bars or path_bars[0].session_date != entry_session or path_bars[-1].session_date != exit_session:
            warnings.append(f"{research_id}/{horizon}: incomplete stock path")
            continue
        if any(bar.price_basis != "adjusted_close" for bar in path_bars):
            warnings.append(f"{research_id}/{horizon}: mixed/non-adjusted stock price basis; left unresolved")
            continue
        metrics = path_metrics([bar.adjusted_close for bar in path_bars])

        try:
            benchmark_return, benchmark_entry, benchmark_exit = _benchmark_return_exact(
                benchmark_bars, entry_session, exit_session
            )
        except ValueError as exc:
            warnings.append(f"{research_id}/{horizon}: {exc}")
            continue
        if benchmark_entry.price_basis != "adjusted_close" or benchmark_exit.price_basis != "adjusted_close":
            warnings.append(f"{research_id}/{horizon}: benchmark price basis is not adjusted_close")
            continue

        sector_return: float | None = None
        if sector_bars:
            try:
                sector_return, sector_entry, sector_exit = _benchmark_return_exact(
                    sector_bars, entry_session, exit_session
                )
                if sector_entry.price_basis != "adjusted_close" or sector_exit.price_basis != "adjusted_close":
                    raise ValueError("sector benchmark price basis is not adjusted_close")
            except ValueError as exc:
                warnings.append(f"{research_id}/{horizon}: sector benchmark: {exc}")
                sector_return = None

        expected_session_count = horizon + 1
        if len(path_bars) < expected_session_count:
            warnings.append(
                f"{research_id}/{horizon}: stock path has {len(path_bars)} observed sessions vs "
                f"{expected_session_count} benchmark sessions; path metrics may miss halted sessions"
            )

        outcome: dict[str, Any] = {
            "research_id": research_id,
            "horizon_trading_days": horizon,
            "horizon_calendar_basis": f"benchmark_sessions:{benchmark_symbol}",
            "evaluation_as_of": exit_session.isoformat(),
            "entry_session_date": entry_session.isoformat(),
            "exit_session_date": exit_session.isoformat(),
            "entry_price": entry_bar.adjusted_close,
            "exit_price": exit_bar.adjusted_close,
            "entry_price_basis": "next_benchmark_session_adjusted_close",
            "exit_price_basis": "target_benchmark_session_adjusted_close",
            "return_semantics": "next_session_close_to_close_adjusted_price_return",
            "realized_return": metrics["realized_return"],
            "benchmark_return": benchmark_return,
            "benchmark_entry_price": benchmark_entry.adjusted_close,
            "benchmark_exit_price": benchmark_exit.adjusted_close,
            "max_favorable_excursion": metrics["max_favorable_excursion"],
            "max_adverse_excursion": metrics["max_adverse_excursion"],
            "max_drawdown_during_horizon": metrics["max_drawdown_during_horizon"],
            "path_metric_basis": "adjusted_close_only",
            "falsifier_triggered": None,
            "falsifier_status": "not_evaluated_automatically",
            "market_data_source": "Yahoo Finance chart API (best-effort, unauthenticated)",
            "market_data_retrieved_at": now_iso(),
            "terminal_event_handling": "not_implemented_missing_terminal_price_remains_unresolved",
        }
        if sector_return is not None:
            outcome["sector_benchmark_return"] = sector_return
        outcomes.append(outcome)
    return outcomes, warnings


def settle_due(
    ledger: Path,
    *,
    today: date,
    fetcher: Callable[[str, date, date], list[DailyBar]] = fetch_yahoo_daily,
    dry_run: bool = False,
) -> dict[str, Any]:
    events = load_events(ledger)
    predictions = prediction_map(events)
    settled = outcome_keys(events)
    created: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for prediction in predictions.values():
        try:
            outcomes, item_warnings = settle_prediction(
                prediction, settled, today=today, fetcher=fetcher
            )
            warnings.extend(item_warnings)
            for outcome in outcomes:
                if not dry_run:
                    record_outcome(ledger, outcome)
                    settled.add((str(outcome["research_id"]), int(outcome["horizon_trading_days"])))
                created.append(outcome)
        except Exception as exc:
            errors.append(f"{prediction.get('research_id')}: {type(exc).__name__}: {exc}")

    if errors and created:
        status = "partial"
    elif errors and not created:
        status = "provider_unavailable_or_no_settlement"
    elif warnings and created:
        status = "partial"
    elif warnings and not created:
        status = "unresolved"
    else:
        status = "success"
    return {
        "status": status,
        "prediction_count": len(predictions),
        "outcomes_created": len(created),
        "dry_run": dry_run,
        "outcomes": created,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional CIS outcome settlement utility")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--today", help="Override current UTC date, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    result = settle_due(args.ledger, today=today, dry_run=args.dry_run)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
